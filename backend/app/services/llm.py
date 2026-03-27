from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from openai import AsyncOpenAI, RateLimitError
from pydantic import BaseModel, Field, ValidationError

from app.config import Settings
from app.schemas.analysis import AtomicClaim, EventHypothesis, EvidenceSpan, PerArticleFraming
from app.services.divergence import lexical_fallback_emphasis
from app.services.llm_client import build_async_openai_client, build_groq_client


PIPELINE_VERSION = "1.0.0"

SYSTEM_PROMPT = """You are a senior computational linguistics and journalism-studies assistant.
You compare how multiple news articles frame the same underlying event.

Rules:
- Do not claim factual truth or falsehood. Analyze framing, stance, emphasis, and omissions.
- Every stance or sentiment judgment must be grounded in the provided article text.
- evidence[].quote MUST be exact excerpts copied from that article's text (max 25 words each). Never put analysis, apologies, or meta sentences (e.g. "text is insufficient…") inside evidence—use analysis_notes for that.
- atomic_claims[].support_quote must be an exact excerpt from the same article when present, or null.
- If text is insufficient for a judgment, explain only in analysis_notes, set neutral stance if needed, and omit non-verbatim evidence for that gap.
- Output MUST be a single JSON object matching the schema described in the user message.
- Stance must be one of: supportive | neutral | critical (relative to the primary actors described in the neutral event summary).
- sentiment_score is in [-1, 1].
"""


class _LLMFramingRow(BaseModel):
    article_index: int
    source_label: str = ""
    stance: str
    sentiment_score: float
    emphasis_terms: list[str] = Field(default_factory=list)
    protagonist_descriptor: str | None = None
    antagonist_descriptor: str | None = None
    atomic_claims: list[dict[str, Any]] = Field(default_factory=list)
    omission_candidates: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    analysis_notes: str | None = None


class _LLMEvent(BaseModel):
    title: str
    neutral_summary: str
    key_entities: list[str] = Field(default_factory=list)


class _LLMPayload(BaseModel):
    event: _LLMEvent
    framing: list[_LLMFramingRow]


def _build_user_prompt(
    labeled_bodies: list[tuple[int, str, str]],
    *,
    provider_tag: str = "primary",
) -> str:
    parts: list[str] = []
    parts.append(
        "Return JSON with keys: event {title, neutral_summary, key_entities}, "
        "framing [array with one object per article]. "
        "Each framing object must include: article_index (int), source_label (string), "
        "stance (supportive|neutral|critical), sentiment_score (number -1..1), "
        "emphasis_terms (string array), protagonist_descriptor (string|null), antagonist_descriptor (string|null), "
        "atomic_claims [{claim, support_quote|null}], omission_candidates (string array), "
        "evidence [{quote, role}] — quote must be verbatim from that article only; role is one of "
        "stance_support|emphasis|tone|actor_framing. "
        "analysis_notes (string|null) for hedges or insufficiency; never put those in evidence.quote."
    )
    if provider_tag == "groq":
        parts.append(
            "Required: for every article, include at least one evidence item whose quote is an exact "
            "contiguous copy from that article's text (same spelling and punctuation as in the excerpt)."
        )
    parts.append("Articles:")
    for idx, label, body in labeled_bodies:
        safe = body[:12000]
        parts.append(f"--- BEGIN ARTICLE index={idx} label={label} ---")
        parts.append(safe)
        parts.append(f"--- END ARTICLE index={idx} ---")
    return "\n".join(parts)


def _normalize_stance(raw: str) -> str:
    s = raw.strip().lower()
    if s in ("supportive", "neutral", "critical"):
        return s
    if "support" in s:
        return "supportive"
    if "critical" in s or "oppose" in s:
        return "critical"
    return "neutral"


def _coerce_per_article(row: _LLMFramingRow) -> PerArticleFraming:
    claims: list[AtomicClaim] = []
    for c in row.atomic_claims[:20]:
        if not isinstance(c, dict):
            continue
        claim = str(c.get("claim", "")).strip()
        if not claim:
            continue
        sq = c.get("support_quote")
        claims.append(
            AtomicClaim(
                claim=claim[:400],
                support_quote=(str(sq).strip()[:500] if sq else None),
            )
        )

    evidence: list[EvidenceSpan] = []
    for e in row.evidence[:12]:
        if not isinstance(e, dict):
            continue
        quote = str(e.get("quote", "")).strip()
        role = str(e.get("role", "stance_support")).strip()
        if role not in ("stance_support", "emphasis", "tone", "actor_framing"):
            role = "stance_support"
        if quote:
            evidence.append(EvidenceSpan(quote=quote[:500], role=role))  # type: ignore[arg-type]

    stance = _normalize_stance(row.stance)
    ss = float(row.sentiment_score)
    ss = max(-1.0, min(1.0, ss))

    return PerArticleFraming(
        article_index=int(row.article_index),
        source_label=(row.source_label or "").strip() or "unknown",
        stance=stance,  # type: ignore[arg-type]
        sentiment_score=ss,
        emphasis_terms=[str(t) for t in row.emphasis_terms][:24],
        protagonist_descriptor=(row.protagonist_descriptor or None),
        antagonist_descriptor=(row.antagonist_descriptor or None),
        atomic_claims=claims,
        omission_candidates=[str(x) for x in row.omission_candidates][:16],
        evidence=evidence,
        analysis_notes=row.analysis_notes,
    )


def _extract_json_text(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _parse_llm_json(text: str) -> _LLMPayload:
    data = json.loads(_extract_json_text(text))
    return _LLMPayload.model_validate(data)


def _maybe_truncate_labeled_bodies(
    labeled_bodies: list[tuple[int, str, str]],
    max_chars: int,
) -> tuple[list[tuple[int, str, str]], bool]:
    out: list[tuple[int, str, str]] = []
    truncated_any = False
    for idx, label, body in labeled_bodies:
        if len(body) > max_chars:
            truncated_any = True
            out.append((idx, label, body[:max_chars]))
        else:
            out.append((idx, label, body))
    return out, truncated_any


def _build_provider_attempts(settings: Settings) -> list[tuple[str, AsyncOpenAI, str, bool]]:
    """
    (tag, client, model_id, truncate_bodies_for_tokens)
    Primary first; Groq when configured as sole provider or as fallback after primary.
    """
    attempts: list[tuple[str, AsyncOpenAI, str, bool]] = []
    if settings.openai_api_key:
        attempts.append(
            ("primary", build_async_openai_client(settings), settings.openai_model, False),
        )
    use_groq = bool(settings.groq_api_key) and (
        (settings.llm_fallback_enabled and bool(settings.openai_api_key))
        or not settings.openai_api_key
    )
    if use_groq:
        gclient = build_groq_client(settings)
        if gclient:
            if (
                settings.openai_api_key
                and settings.groq_api_key == settings.openai_api_key
                and "groq.com" in (settings.openai_base_url or "").lower()
                and attempts
            ):
                return attempts
            attempts.append(("groq", gclient, settings.groq_model, True))
    return attempts


async def _chat_completion(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict[str, str]],
    *,
    json_object: bool,
) -> Any:
    kwargs: dict = {
        "model": model,
        "temperature": 0.2,
        "messages": messages,
    }
    if json_object:
        kwargs["response_format"] = {"type": "json_object"}
    return await client.chat.completions.create(**kwargs)


_BACKOFF_SECONDS = (1.5, 3.0, 6.0, 10.0, 14.0, 20.0, 28.0, 36.0)


async def _chat_completion_with_rate_limit_backoff(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict[str, str]],
    *,
    json_object: bool,
    tag: str,
    settings: Settings,
    warnings: list[str],
) -> Any:
    """
    Retries on RateLimitError for the primary provider only (reduces unnecessary Groq fallback).
    """
    retries = settings.llm_primary_rate_limit_retries if tag == "primary" else 0
    last_rl: RateLimitError | None = None
    for attempt in range(retries + 1):
        try:
            return await _chat_completion(client, model, messages, json_object=json_object)
        except RateLimitError as exc:
            last_rl = exc
            if attempt >= retries:
                raise
            delay = _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]
            warnings.append(
                f"[{tag}] Rate limited ({type(exc).__name__}); waiting {delay:.1f}s "
                f"before retry ({attempt + 2}/{retries + 1}).",
            )
            await asyncio.sleep(delay)
    assert last_rl is not None
    raise last_rl


def _payload_to_result(payload: _LLMPayload) -> tuple[EventHypothesis, list[PerArticleFraming]]:
    event = EventHypothesis(
        title=payload.event.title[:300],
        neutral_summary=payload.event.neutral_summary[:2000],
        key_entities=payload.event.key_entities[:32],
    )
    framing = [_coerce_per_article(r) for r in payload.framing]
    return event, framing


async def generate_framing_bundle(
    labeled_bodies: list[tuple[int, str, str]],
    settings: Settings,
) -> tuple[EventHypothesis, list[PerArticleFraming], list[str], str, str]:
    """
    Returns (event, framing, warnings, model_id, provider_tag).
    provider_tag is primary | groq | mock (which endpoint succeeded).
    """
    warnings: list[str] = []
    if not settings.llm_live_enabled:
        e, f, w = _mock_bundle(labeled_bodies, settings, warnings)
        return e, f, w, "mock-deterministic", "mock"

    attempts = _build_provider_attempts(settings)
    if not attempts:
        e, f, w = _mock_bundle(labeled_bodies, settings, warnings)
        return e, f, w, "mock-deterministic", "mock"

    for idx, (tag, client, model, truncate) in enumerate(attempts):
        bodies = labeled_bodies
        if truncate:
            bodies, did_trunc = _maybe_truncate_labeled_bodies(
                labeled_bodies,
                settings.llm_fallback_max_chars_per_article,
            )
            if did_trunc:
                warnings.append(
                    f"[{tag}] Truncated each article to {settings.llm_fallback_max_chars_per_article} "
                    "characters to reduce token usage on the backup model."
                )

        user_prompt = _build_user_prompt(bodies, provider_tag=tag)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        resp = None
        try:
            if settings.llm_json_response_format:
                try:
                    resp = await _chat_completion_with_rate_limit_backoff(
                        client,
                        model,
                        messages,
                        json_object=True,
                        tag=tag,
                        settings=settings,
                        warnings=warnings,
                    )
                except Exception as exc:  # noqa: BLE001
                    warnings.append(
                        f"[{tag}] JSON response_format failed ({type(exc).__name__}); retrying without."
                    )
                    resp = await _chat_completion_with_rate_limit_backoff(
                        client,
                        model,
                        messages,
                        json_object=False,
                        tag=tag,
                        settings=settings,
                        warnings=warnings,
                    )
            else:
                resp = await _chat_completion_with_rate_limit_backoff(
                    client,
                    model,
                    messages,
                    json_object=False,
                    tag=tag,
                    settings=settings,
                    warnings=warnings,
                )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"[{tag}] Request failed ({type(exc).__name__}); trying next provider if available.")
            continue

        content = (resp.choices[0].message.content if resp and resp.choices else None) or ""
        try:
            payload = _parse_llm_json(content)
        except (json.JSONDecodeError, ValidationError) as exc:
            warnings.append(
                f"[{tag}] Model output was not valid JSON ({type(exc).__name__}); trying next provider if available.",
            )
            continue

        event, framing = _payload_to_result(payload)
        if idx > 0:
            warnings.append(
                "Recovered via Groq backup after the primary LLM endpoint failed, rate-limited, or returned unusable output.",
            )
        return event, framing, warnings, model, tag

    e, f, w = _mock_bundle(labeled_bodies, settings, warnings)
    return e, f, w, "mock-deterministic", "mock"


def _mock_bundle(
    labeled_bodies: list[tuple[int, str, str]],
    settings: Settings,
    warnings: list[str],
) -> tuple[EventHypothesis, list[PerArticleFraming], list[str]]:
    warnings.append(
        "LLM operating in deterministic mock mode. Configure LLM_API_KEY + OPENAI_BASE_URL for primary, "
        "add GROQ_API_KEY for automatic Groq fallback on rate limits, and set USE_MOCK_LLM=false."
    )
    combined = "\n\n".join(body for _, _, body in labeled_bodies)
    title = re.sub(r"\s+", " ", combined[:120]).strip() or "Unspecified event"
    summary = re.sub(r"\s+", " ", combined[:900]).strip()

    entities = sorted(
        {m.group(0) for m in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", combined[:4000])}
    )[:12]

    event = EventHypothesis(
        title=title[:300],
        neutral_summary=summary[:2000],
        key_entities=entities,
    )

    framing: list[PerArticleFraming] = []
    for idx, label, body in labeled_bodies:
        terms = lexical_fallback_emphasis(body, top_k=12)
        # crude sentiment heuristic for demo-only path
        neg_hits = sum(1 for w in ("crisis", "mob", "chaos", "violence", "arrest") if w in body.lower())
        pos_hits = sum(1 for w in ("rights", "peaceful", "demand", "citizen", "dialogue") if w in body.lower())
        sentiment = max(-1.0, min(1.0, (pos_hits - neg_hits) * 0.15))
        stance = "neutral"
        if sentiment > 0.15:
            stance = "supportive"
        elif sentiment < -0.15:
            stance = "critical"

        claims: list[AtomicClaim] = []
        for sentence in re.split(r"(?<=[.!?])\s+", body[:2000]):
            s = sentence.strip()
            if 40 < len(s) < 220:
                claims.append(AtomicClaim(claim=s[:400], support_quote=s[:500]))
            if len(claims) >= 5:
                break

        framing.append(
            PerArticleFraming(
                article_index=idx,
                source_label=label or f"source_{idx}",
                stance=stance,  # type: ignore[arg-type]
                sentiment_score=sentiment,
                emphasis_terms=terms,
                protagonist_descriptor="Primary actors described in the article",
                antagonist_descriptor="Opposing or institutional actors, if any",
                atomic_claims=claims,
                omission_candidates=[],
                evidence=[
                    EvidenceSpan(
                        quote=re.sub(r"\s+", " ", body[:220]).strip()[:500],
                        role="stance_support",
                    )
                ],
                analysis_notes="Mock analysis: configure a free-tier OpenAI-compatible API (e.g. Groq or OpenRouter) for full structured reasoning.",
            )
        )

    _ = settings  # reserved for future model-specific mock behavior
    return event, framing, warnings

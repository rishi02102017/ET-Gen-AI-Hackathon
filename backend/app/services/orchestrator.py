from __future__ import annotations

from app.config import Settings
from app.schemas.analysis import (
    AnalysisMeta,
    AnalysisResponse,
    AnalyzeRequest,
    ArticleInput,
    AtomicClaim,
    PerArticleFraming,
    ResolvedArticle,
)
from app.services.divergence import compute_divergence, lexical_fallback_emphasis
from app.services.extraction import document_fingerprint, extract_from_paste, fetch_url_text
from app.services.framing_grounding import (
    inject_verbatim_evidence_fallback,
    sanitize_framing_against_source,
)
from app.services.llm import PIPELINE_VERSION, generate_framing_bundle
from app.services.security import UnsafeUrlError


class AnalysisInputError(ValueError):
    pass


def _label_for(idx: int, article: ArticleInput) -> str:
    if article.source_label and article.source_label.strip():
        return article.source_label.strip()
    if article.url is not None:
        return str(article.url)
    return f"article_{idx}"


async def run_analysis(request: AnalyzeRequest, settings: Settings) -> AnalysisResponse:
    if len(request.articles) > settings.max_url_fetches:
        raise AnalysisInputError("Too many articles for this deployment configuration.")

    warnings: list[str] = []
    labeled_bodies: list[tuple[int, str, str]] = []
    resolved: list[ResolvedArticle] = []

    for idx, art in enumerate(request.articles):
        label = _label_for(idx, art)
        text = ""
        url_str: str | None = str(art.url) if art.url is not None else None

        if art.text:
            doc = extract_from_paste(art.text)
            text = doc.plain_text
            warnings.extend(doc.warnings)

        if art.url is not None and not text:
            try:
                doc = await fetch_url_text(str(art.url), settings)
                text = doc.plain_text
                warnings.extend(doc.warnings)
            except UnsafeUrlError as exc:
                raise AnalysisInputError(str(exc)) from exc
            except Exception as exc:  # noqa: BLE001
                raise AnalysisInputError(f"Failed to fetch article URL ({type(exc).__name__}).") from exc

        if not text.strip():
            raise AnalysisInputError(f"No usable text for article index {idx}.")

        fp = document_fingerprint(text)
        excerpt = " ".join(text.split())[:600]
        wc = len(text.split())
        resolved.append(
            ResolvedArticle(
                index=idx,
                source_label=label,
                url=url_str,
                excerpt=excerpt,
                content_sha256=fp,
                word_count=wc,
            )
        )
        labeled_bodies.append((idx, label, text))

    event, framing, llm_warnings, used_model_id, provider_tag = await generate_framing_bundle(
        labeled_bodies,
        settings,
    )
    warnings.extend(llm_warnings)

    by_index = {f.article_index: f for f in framing}
    ordered: list[PerArticleFraming] = []
    grounding_touched = False
    evidence_injected = False
    for idx, (_, label, body) in enumerate(labeled_bodies):
        row = by_index.get(idx)
        if row is None:
            terms = lexical_fallback_emphasis(body)
            row = PerArticleFraming(
                article_index=idx,
                source_label=label,
                stance="neutral",
                sentiment_score=0.0,
                emphasis_terms=terms,
                protagonist_descriptor=None,
                antagonist_descriptor=None,
                atomic_claims=[
                    AtomicClaim(claim="Insufficient structured output for this article.", support_quote=None)
                ],
                omission_candidates=[],
                evidence=[],
                analysis_notes="Recovered locally after partial LLM output.",
            )
        if not row.emphasis_terms:
            row = row.model_copy(update={"emphasis_terms": lexical_fallback_emphasis(body)})
        if row.source_label in ("", "unknown"):
            row = row.model_copy(update={"source_label": label})
        row, touched = sanitize_framing_against_source(row, body)
        row, injected = inject_verbatim_evidence_fallback(row, body)
        grounding_touched = grounding_touched or touched
        evidence_injected = evidence_injected or injected
        ordered.append(row)

    if grounding_touched:
        warnings.append(
            "Evidence and claim support quotes were checked against source text; "
            "non-verbatim or meta lines were removed (see per-source notes).",
        )
    if evidence_injected:
        warnings.append(
            "Some sources had verbatim evidence excerpts auto-selected from the article text "
            "after no valid model quotes remained.",
        )

    divergence = compute_divergence(ordered)

    model_id = used_model_id if settings.llm_live_enabled else "mock-deterministic"
    # True when a primary key was configured but the successful call used the backup chain entry (Groq).
    fallback_used = (
        settings.llm_live_enabled
        and provider_tag == "groq"
        and bool(settings.openai_api_key)
    )

    meta = AnalysisMeta(
        model_id=model_id,
        pipeline_version=PIPELINE_VERSION,
        warnings=warnings,
        llm_fallback_used=fallback_used,
    )

    return AnalysisResponse(
        event=event,
        articles=resolved,
        framing=ordered,
        divergence=divergence,
        meta=meta,
    )

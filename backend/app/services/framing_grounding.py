from __future__ import annotations

import re

from app.schemas.analysis import AtomicClaim, EvidenceSpan, PerArticleFraming

# Model commentary often placed in evidence.quote by smaller models; never treat as verbatim.
_META_PHRASES = (
    "text is insufficient",
    "insufficient to",
    "cannot determine",
    "unable to determine",
    "unclear from the text",
    "not enough information",
    "no direct evidence",
    "cannot be determined",
    "not possible to",
    "does not specify",
    "the article does not",
    "unable to assess",
)


def _collapse_ws(s: str) -> str:
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    s = s.lower().strip()
    return re.sub(r"\s+", " ", s)


def _alnum_compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _is_meta_commentary(text: str) -> bool:
    t = text.lower().strip()
    if any(p in t for p in _META_PHRASES):
        return True
    if "determine" in t and ("text" in t or "article" in t or "source" in t):
        return True
    return False


def quote_appears_in_body(quote: str, body: str) -> bool:
    """True if quote is plausibly copied from body (whitespace-tolerant, light punctuation tolerance)."""
    q = quote.strip()
    if len(q) < 3:
        return False
    b_norm = _collapse_ws(body)
    q_norm = _collapse_ws(q)
    if q_norm in b_norm:
        return True
    # Punctuation / hyphen variants (e.g. "co-operate" vs "cooperate")
    qa = _alnum_compact(q)
    ba = _alnum_compact(body)
    if len(qa) >= 16 and qa in ba:
        return True
    return False


def sanitize_framing_against_source(row: PerArticleFraming, body: str) -> tuple[PerArticleFraming, bool]:
    """
    Drop evidence quotes that are not substrings of the article or that read as model meta-commentary.
    Clear atomic_claim support_quote when it does not appear in the source.
    Returns (updated row, True if evidence or support quotes were changed).
    """
    dropped_evidence: list[str] = []

    kept_evidence: list[EvidenceSpan] = []
    for ev in row.evidence:
        q = ev.quote.strip()
        if not q:
            continue
        if _is_meta_commentary(q):
            dropped_evidence.append(q[:120] + ("…" if len(q) > 120 else ""))
            continue
        if not quote_appears_in_body(q, body):
            dropped_evidence.append(q[:120] + ("…" if len(q) > 120 else ""))
            continue
        kept_evidence.append(ev)

    new_claims: list[AtomicClaim] = []
    cleared_support_quotes = 0
    for c in row.atomic_claims:
        sq = (c.support_quote or "").strip()
        if sq and not quote_appears_in_body(sq, body):
            new_claims.append(AtomicClaim(claim=c.claim, support_quote=None))
            cleared_support_quotes += 1
        else:
            new_claims.append(c)
    extra_parts: list[str] = []
    if dropped_evidence:
        preview = "; ".join(dropped_evidence[:3])
        if len(dropped_evidence) > 3:
            preview += f" (+{len(dropped_evidence) - 3} more)"
        extra_parts.append(
            "Non-verbatim or meta commentary removed from grounded evidence "
            f"(not found in source text): {preview}"
        )
    if cleared_support_quotes:
        extra_parts.append(
            f"Cleared {cleared_support_quotes} claim support quote(s) not found verbatim in source."
        )
    extra_note = "\n\n".join(extra_parts) if extra_parts else None

    merged_notes = row.analysis_notes or ""
    if extra_note:
        merged_notes = f"{merged_notes}\n\n{extra_note}".strip() if merged_notes else extra_note
    if len(merged_notes) > 1200:
        merged_notes = merged_notes[:1197] + "…"

    updated = row.model_copy(
        update={
            "evidence": kept_evidence,
            "atomic_claims": new_claims,
            "analysis_notes": merged_notes or None,
        },
    )
    changed = bool(dropped_evidence) or cleared_support_quotes > 0
    return updated, changed


def _verbatim_sentence_excerpts(body: str, max_spans: int = 2) -> list[str]:
    """Pick 1–2 substantial sentences from the article for deterministic evidence (always verbatim)."""
    text = body.strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if 40 <= len(p) <= 500:
            out.append(p[:500])
        if len(out) >= max_spans:
            break
    if not out:
        chunk = re.split(r"[\n]", text, maxsplit=1)[0].strip()
        if len(chunk) >= 80:
            out.append(chunk[:500])
        elif len(text) >= 50:
            out.append(text[:500])
    return out[:max_spans]


def inject_verbatim_evidence_fallback(row: PerArticleFraming, body: str) -> tuple[PerArticleFraming, bool]:
    """
    If the model left no valid evidence spans, attach short verbatim excerpts from the source body.
    """
    if row.evidence:
        return row, False
    excerpts = _verbatim_sentence_excerpts(body, max_spans=2)
    if not excerpts:
        return row, False
    spans = [EvidenceSpan(quote=q, role="stance_support") for q in excerpts]
    note_add = (
        "Verbatim excerpts were auto-selected from the source text because no model-provided "
        "evidence quotes passed validation."
    )
    merged = (row.analysis_notes + "\n\n" + note_add).strip() if row.analysis_notes else note_add
    if len(merged) > 1200:
        merged = merged[:1197] + "…"
    return (
        row.model_copy(update={"evidence": spans, "analysis_notes": merged}),
        True,
    )


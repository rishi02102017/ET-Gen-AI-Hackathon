from __future__ import annotations

import math
import re
from collections import Counter
from typing import Literal

from app.schemas.analysis import (
    AtomicClaim,
    DivergenceBreakdown,
    DivergenceResult,
    PerArticleFraming,
)


def _stance_numeric(stance: str) -> float:
    return {"supportive": 1.0, "neutral": 0.0, "critical": -1.0}.get(stance, 0.0)


def _tokenize_terms(terms: list[str]) -> set[str]:
    out: set[str] = set()
    for t in terms:
        x = re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
        for part in x.split():
            if len(part) >= 3:
                out.add(part)
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return 1.0 - (inter / union) if union else 0.0


def _claim_key(claim: str) -> str:
    return re.sub(r"\s+", " ", claim.lower().strip())[:200]


def _coverage_asymmetry(claims_per_article: list[list[AtomicClaim]]) -> float:
    union: set[str] = set()
    per_counts: list[int] = []
    for claims in claims_per_article:
        keys = {_claim_key(c.claim) for c in claims if c.claim.strip()}
        union |= keys
        per_counts.append(len(keys))
    if not union:
        return 0.0
    coverages = [c / len(union) for c in per_counts]
    mean = sum(coverages) / len(coverages)
    var = sum((c - mean) ** 2 for c in coverages) / len(coverages)
    # Map variance to 0..1 with diminishing returns
    return float(max(0.0, min(1.0, math.sqrt(var) * 2.0)))


def _omission_asymmetry(frames: list[PerArticleFraming]) -> float:
    """
    Pairwise Jaccard *distance* on omission-candidate sets: different omission themes → higher score.
    """
    key_sets: list[set[str]] = []
    for f in frames:
        keys = {_claim_key(x) for x in f.omission_candidates if x.strip()}
        key_sets.append(keys)
    if len(key_sets) < 2:
        return 0.0
    pairs: list[float] = []
    for i in range(len(key_sets)):
        for j in range(i + 1, len(key_sets)):
            a, b = key_sets[i], key_sets[j]
            if not a and not b:
                pairs.append(0.0)
                continue
            inter = len(a & b)
            union = len(a | b)
            sim = inter / union if union else 0.0
            pairs.append(1.0 - sim)
    return sum(pairs) / len(pairs) if pairs else 0.0


def _actor_delta(frames: list[PerArticleFraming]) -> float:
    def norm(s: str | None) -> set[str]:
        if not s:
            return set()
        return set(re.findall(r"[a-z0-9]{3,}", s.lower()))

    scores: list[float] = []
    n = len(frames)
    for i in range(n):
        for j in range(i + 1, n):
            a = norm(frames[i].protagonist_descriptor) | norm(frames[i].antagonist_descriptor)
            b = norm(frames[j].protagonist_descriptor) | norm(frames[j].antagonist_descriptor)
            scores.append(_jaccard(a, b))
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def compute_divergence(framing: list[PerArticleFraming]) -> DivergenceResult:
    """
    Deterministic divergence from structured per-article signals.
    Weights sum to 1.0; score is 0..100.
    """
    weights = {
        "stance_spread": 0.28,
        "emphasis_mismatch": 0.26,
        "coverage_asymmetry": 0.26,
        "actor_framing_delta": 0.20,
    }

    stances = [_stance_numeric(f.stance) for f in framing]
    stance_spread = 0.0
    if stances:
        stance_spread = (max(stances) - min(stances)) / 2.0

    term_sets = [_tokenize_terms(f.emphasis_terms) for f in framing]
    emphasis_pairs: list[float] = []
    for i in range(len(term_sets)):
        for j in range(i + 1, len(term_sets)):
            emphasis_pairs.append(_jaccard(term_sets[i], term_sets[j]))
    emphasis_mismatch = sum(emphasis_pairs) / len(emphasis_pairs) if emphasis_pairs else 0.0

    claims = [f.atomic_claims for f in framing]
    claim_balance = _coverage_asymmetry(claims)
    omission_spread = _omission_asymmetry(framing)
    # Blend: extracted-claim balance + cross-source omission mismatch (explains “same # of claims” cases).
    coverage_asym = float(
        max(0.0, min(1.0, 0.52 * claim_balance + 0.48 * omission_spread)),
    )

    actor_delta = _actor_delta(framing)

    breakdown = DivergenceBreakdown(
        stance_spread=float(max(0.0, min(1.0, stance_spread))),
        emphasis_mismatch=float(max(0.0, min(1.0, emphasis_mismatch))),
        coverage_asymmetry=float(max(0.0, min(1.0, coverage_asym))),
        actor_framing_delta=float(max(0.0, min(1.0, actor_delta))),
        weights=weights,
    )

    raw = (
        weights["stance_spread"] * breakdown.stance_spread
        + weights["emphasis_mismatch"] * breakdown.emphasis_mismatch
        + weights["coverage_asymmetry"] * breakdown.coverage_asymmetry
        + weights["actor_framing_delta"] * breakdown.actor_framing_delta
    )
    score = int(round(max(0.0, min(1.0, raw)) * 100))

    band: Literal["low", "moderate", "high"]
    if score < 34:
        band = "low"
    elif score < 67:
        band = "moderate"
    else:
        band = "high"

    interpretation = (
        "Divergence summarizes how differently sources frame the same event: stance spread, "
        "emphasis keywords, balance of extracted claims plus cross-source omission signals, "
        "and differences in how actors are cast. "
        f"Aggregate score: {score}/100 ({band}). "
        "This is a framing diagnostic, not a verdict on factual accuracy."
    )

    return DivergenceResult(
        score_0_100=score,
        band=band,
        breakdown=breakdown,
        interpretation=interpretation,
    )


def lexical_fallback_emphasis(text: str, top_k: int = 12) -> list[str]:
    """Deterministic emphasis hints if the LLM omits terms."""
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
    stop = {
        "the",
        "and",
        "for",
        "that",
        "with",
        "from",
        "this",
        "have",
        "has",
        "was",
        "were",
        "are",
        "but",
        "not",
        "his",
        "her",
        "they",
        "their",
        "will",
        "into",
        "about",
        "after",
        "before",
        "when",
        "than",
        "also",
        "said",
        "say",
        "says",
    }
    filtered = [t for t in tokens if t not in stop]
    counts = Counter(filtered)
    return [w for w, _ in counts.most_common(top_k)]

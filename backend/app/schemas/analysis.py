from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class ArticleInput(BaseModel):
    """One news item: either a public URL or raw article text (or both)."""

    url: HttpUrl | None = None
    text: str | None = None
    source_label: str | None = Field(
        default=None,
        description="Optional display name (e.g. outlet).",
    )

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s if s else None

    @model_validator(mode="after")
    def require_url_or_text(self) -> ArticleInput:
        if self.url is None and not self.text:
            raise ValueError("Each article requires a non-empty URL or pasted text.")
        return self


class AnalyzeOptions(BaseModel):
    """Optional tuning for analysis runs."""

    language_hint: str | None = Field(
        default=None,
        description="ISO-like language hint for extraction (e.g. en).",
    )


class AnalyzeRequest(BaseModel):
    articles: list[ArticleInput] = Field(
        ...,
        min_length=2,
        max_length=6,
        description="Two to six articles to compare.",
    )
    options: AnalyzeOptions | None = None


class EvidenceSpan(BaseModel):
    quote: str = Field(..., max_length=500)
    role: Literal[
        "stance_support",
        "emphasis",
        "tone",
        "actor_framing",
    ]


class AtomicClaim(BaseModel):
    claim: str = Field(..., max_length=400)
    support_quote: str | None = Field(default=None, max_length=500)


class PerArticleFraming(BaseModel):
    article_index: int
    source_label: str
    stance: Literal["supportive", "neutral", "critical"]
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    emphasis_terms: list[str] = Field(default_factory=list, max_length=24)
    protagonist_descriptor: str | None = Field(default=None, max_length=200)
    antagonist_descriptor: str | None = Field(default=None, max_length=200)
    atomic_claims: list[AtomicClaim] = Field(default_factory=list, max_length=20)
    omission_candidates: list[str] = Field(
        default_factory=list,
        max_length=16,
        description="Claims present in other articles but weak or missing here.",
    )
    evidence: list[EvidenceSpan] = Field(default_factory=list, max_length=12)
    analysis_notes: str | None = Field(default=None, max_length=1200)


class EventHypothesis(BaseModel):
    title: str = Field(..., max_length=300)
    neutral_summary: str = Field(..., max_length=2000)
    key_entities: list[str] = Field(default_factory=list, max_length=32)


class DivergenceBreakdown(BaseModel):
    stance_spread: float = Field(..., ge=0.0, le=1.0)
    emphasis_mismatch: float = Field(..., ge=0.0, le=1.0)
    coverage_asymmetry: float = Field(..., ge=0.0, le=1.0)
    actor_framing_delta: float = Field(..., ge=0.0, le=1.0)
    weights: dict[str, float]


class DivergenceResult(BaseModel):
    score_0_100: int = Field(..., ge=0, le=100)
    band: Literal["low", "moderate", "high"]
    breakdown: DivergenceBreakdown
    interpretation: str = Field(..., max_length=1200)


class AnalysisMeta(BaseModel):
    model_id: str
    pipeline_version: str
    warnings: list[str] = Field(default_factory=list)
    llm_fallback_used: bool = Field(
        default=False,
        description="True when the successful completion used the configured backup (e.g. Groq) provider.",
    )


class ResolvedArticle(BaseModel):
    index: int
    source_label: str
    url: str | None
    excerpt: str = Field(..., max_length=600)
    content_sha256: str
    word_count: int


class AnalysisResponse(BaseModel):
    event: EventHypothesis
    articles: list[ResolvedArticle]
    framing: list[PerArticleFraming]
    divergence: DivergenceResult
    meta: AnalysisMeta


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    pipeline_version: str
    llm_mode: Literal["mock", "live"]
    llm_api_host: str | None = Field(
        default=None,
        description="Resolved API hostname for the configured OpenAI-compatible endpoint.",
    )
    llm_fallback_ready: bool = Field(
        default=False,
        description="True when Groq fallback is configured (GROQ_API_KEY + LLM_FALLBACK_ENABLED).",
    )

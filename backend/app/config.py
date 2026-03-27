from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# This file lives in backend/app/; parents walk to backend/ then repository root.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent


def _resolved_env_files() -> tuple[str, ...] | None:
    """
    Load secrets from disk in a cwd-independent way (SDE: one canonical repo-root .env).
    Later files override earlier ones. Process environment still wins over file values
    when using the default pydantic-settings precedence.
    """
    candidates = (
        _REPO_ROOT / ".env",
        _BACKEND_DIR / ".env",
    )
    found = tuple(str(p) for p in candidates if p.is_file())
    return found or None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_resolved_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Narrative Framing Analyzer API"
    debug: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Primary OpenAI-compatible provider (OpenAI, OpenRouter, etc.). Do not use GROQ_API_KEY here—use groq_api_key for fallback.
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "OPENAI_API_KEY",
            "LLM_API_KEY",
        ),
    )
    openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_BASE_URL", "LLM_BASE_URL"),
        description="e.g. https://api.groq.com/openai/v1 or https://openrouter.ai/api/v1",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("OPENAI_MODEL", "LLM_MODEL"),
    )
    llm_timeout_seconds: float = 120.0
    llm_json_response_format: bool = Field(
        default=True,
        validation_alias=AliasChoices("LLM_JSON_RESPONSE_FORMAT"),
        description="If false, never send response_format=json_object (some endpoints reject it).",
    )
    llm_primary_rate_limit_retries: int = Field(
        default=2,
        ge=0,
        le=8,
        validation_alias=AliasChoices("LLM_PRIMARY_RATE_LIMIT_RETRIES"),
        description="On primary provider only: extra attempts after RateLimitError with backoff before fallback.",
    )
    openrouter_http_referer: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_HTTP_REFERER", "HTTP_REFERER"),
        description="OpenRouter recommends a site URL for free-tier attribution.",
    )
    openrouter_x_title: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_X_TITLE", "X_TITLE"),
    )

    # Automatic fallback when primary fails (rate limits, 5xx, timeouts, parse errors after a successful HTTP response)
    groq_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GROQ_API_KEY"),
        description="Separate Groq key for fallback; not mixed with primary LLM_API_KEY.",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias=AliasChoices("GROQ_MODEL"),
        description="Groq model for backup; default is stronger for eval quality; override with 8B for speed.",
    )
    llm_fallback_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("LLM_FALLBACK_ENABLED"),
    )
    llm_fallback_max_chars_per_article: int = Field(
        default=8000,
        ge=1500,
        le=12000,
        validation_alias=AliasChoices("LLM_FALLBACK_MAX_CHARS_PER_ARTICLE"),
        description="Truncate each article body for fallback attempts to reduce tokens.",
    )

    max_url_fetches: int = 6
    max_html_bytes: int = 2_000_000
    http_timeout_seconds: float = 25.0
    use_mock_llm: bool = False

    @field_validator("openai_api_key", "groq_api_key", mode="after")
    @classmethod
    def normalize_api_key(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("openai_base_url", mode="after")
    @classmethod
    def strip_base_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip().rstrip("/")
        return s if s else None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_live_enabled(self) -> bool:
        return bool(
            not self.use_mock_llm and (self.openai_api_key or self.groq_api_key),
        )

    @property
    def llm_fallback_configured(self) -> bool:
        return bool(self.llm_fallback_enabled and self.groq_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

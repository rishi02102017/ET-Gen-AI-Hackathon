from __future__ import annotations

from urllib.parse import urlparse

from openai import AsyncOpenAI

from app.config import Settings

GROQ_OPENAI_BASE = "https://api.groq.com/openai/v1"


def build_async_openai_client(settings: Settings) -> AsyncOpenAI:
    """Primary OpenAI-compatible client (OpenRouter, OpenAI, self-hosted, etc.)."""
    kwargs: dict = {
        "api_key": settings.openai_api_key or "",
        "timeout": settings.llm_timeout_seconds,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url

    default_headers: dict[str, str] = {}
    if settings.openrouter_http_referer:
        default_headers["HTTP-Referer"] = settings.openrouter_http_referer.strip()
    if settings.openrouter_x_title:
        default_headers["X-Title"] = settings.openrouter_x_title.strip()
    if default_headers:
        kwargs["default_headers"] = default_headers

    return AsyncOpenAI(**kwargs)


def build_groq_client(settings: Settings) -> AsyncOpenAI | None:
    """Dedicated Groq OpenAI-compatible client (no OpenRouter headers)."""
    if not settings.groq_api_key:
        return None
    return AsyncOpenAI(
        api_key=settings.groq_api_key,
        base_url=GROQ_OPENAI_BASE,
        timeout=settings.llm_timeout_seconds,
    )


def resolve_llm_api_host(settings: Settings) -> str | None:
    if not settings.llm_live_enabled:
        return None
    if settings.openai_api_key and settings.openai_base_url:
        return urlparse(settings.openai_base_url).hostname
    if settings.openai_api_key:
        return "api.openai.com"
    if settings.groq_api_key:
        return urlparse(GROQ_OPENAI_BASE).hostname
    return None

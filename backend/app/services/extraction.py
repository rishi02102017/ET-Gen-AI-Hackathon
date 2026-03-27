from __future__ import annotations

import hashlib
from dataclasses import dataclass

import httpx
import trafilatura

from app.config import Settings
from app.services.security import UnsafeUrlError, assert_fetchable_http_url


@dataclass(frozen=True)
class ExtractedDocument:
    plain_text: str
    warnings: list[str]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def fetch_url_text(url: str, settings: Settings) -> ExtractedDocument:
    warnings: list[str] = []
    assert_fetchable_http_url(url)
    headers = {
        "User-Agent": "ET-FramingAnalyzer/1.0 (research; +https://economictimes.indiatimes.com)",
        "Accept": "text/html,application/xhtml+xml",
    }
    async with httpx.AsyncClient(
        timeout=settings.http_timeout_seconds,
        follow_redirects=True,
        limits=httpx.Limits(max_connections=5),
    ) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        body = resp.content
        if len(body) > settings.max_html_bytes:
            raise ValueError("Downloaded document exceeds configured size limit.")

    extracted = trafilatura.extract(
        body,
        url=url,
        include_comments=False,
        include_tables=False,
    )
    if not extracted or not extracted.strip():
        warnings.append("Primary extraction yielded little or no text; page may be paywalled or script-rendered.")
        extracted = (
            trafilatura.extract(
                body,
                url=url,
                favor_precision=True,
                include_comments=False,
                include_tables=False,
            )
            or ""
        )

    text = extracted.strip()
    if len(text) < 200:
        warnings.append("Very short article body after extraction; results may be low confidence.")

    return ExtractedDocument(plain_text=text, warnings=warnings)


def extract_from_paste(text: str) -> ExtractedDocument:
    t = text.strip()
    warnings: list[str] = []
    if len(t) < 200:
        warnings.append("Pasted text is short; analysis may be low confidence.")
    return ExtractedDocument(plain_text=t, warnings=warnings)


def document_fingerprint(text: str) -> str:
    return _sha256(text)

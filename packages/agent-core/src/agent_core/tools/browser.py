"""Minimal web-fetch tool — requests-based, no JS rendering.

Playwright can replace this later in the Forest phase; keeping Seed tiny.
"""

from __future__ import annotations

import re

import httpx

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
_MAX_TEXT = 5000
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def browse_website(url: str, extract_text: bool = True, timeout: float = 10.0) -> str:
    """Fetch a URL and return raw HTML or crude text (first 5000 chars)."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": _UA})
            resp.raise_for_status()
            body = resp.text
    except httpx.HTTPError as e:
        return f"Lỗi khi truy cập {url}: {e}"
    if not extract_text:
        return body[:_MAX_TEXT]
    text = _HTML_TAG_RE.sub(" ", body)
    text = _WS_RE.sub(" ", text)
    return text.strip()[:_MAX_TEXT]

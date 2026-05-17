"""Browser tool for seed agents — fetches web content via stdlib urllib."""

from __future__ import annotations

import re
import urllib.request


def browse_website(url: str, extract_text: bool = True) -> str:
    """Fetch URL and return content (text-only by default)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mekong-seed/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        if extract_text:
            content = re.sub(r"<[^>]+>", " ", content)
            content = re.sub(r"\s+", " ", content).strip()
            content = content[:8000]
        return content
    except Exception as e:
        return f"[browse_website error: {e}]"

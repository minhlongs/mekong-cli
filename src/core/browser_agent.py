# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Browser Agent (AGI v2)."""

import logging
import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class BrowserAction(str, Enum):
    NAVIGATE = "navigate"
    SCREENSHOT = "screenshot"
    EXTRACT_TEXT = "extract_text"
    FILL_FORM = "fill_form"
    CLICK = "click"
    GET_LINKS = "get_links"
    CHECK_STATUS = "check_status"

@dataclass
class BrowserResult:
    action: BrowserAction
    success: bool = False
    url: str = ""
    content: str = ""
    status_code: int = 0
    screenshot_path: str = ""
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    error: str = ""

@dataclass
class PageInfo:
    url: str
    title: str = ""
    status_code: int = 0
    content_type: str = ""
    text_content: str = ""
    links: List[str] = field(default_factory=list)
    forms: List[Dict[str, Any]] = field(default_factory=list)
    meta_tags: Dict[str, str] = field(default_factory=dict)
    load_time_ms: float = 0.0

class BrowserAgent:
    """Browser automation agent for web interaction."""

    def __init__(self, llm_client: Optional[Any] = None, cache_dir: Optional[str] = None) -> None:
        self.llm_client, self._cache_dir = llm_client, Path(cache_dir or ".mekong/browser_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._history: List[BrowserResult] = []
        self._playwright_available = self._check_playwright()

    def navigate(self, url: str) -> BrowserResult:
        start, result = time.time(), BrowserResult(action=BrowserAction.NAVIGATE, url=url)
        try:
            response = self._fetch_url(url)
            result.success, result.status_code, result.content = True, response["status_code"], response["body"][:10000]
            result.metadata = {"content_type": response.get("content_type", ""), "title": self._extract_title(response["body"])}
        except Exception as e:
            result.error = str(e)
        result.duration_ms = (time.time() - start) * 1000
        return self._record(result)

    def check_status(self, url: str) -> BrowserResult:
        start, result = time.time(), BrowserResult(action=BrowserAction.CHECK_STATUS, url=url)
        try:
            proc = subprocess.run(["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code}", url], capture_output=True, text=True, timeout=15)
            result.status_code = int(proc.stdout.strip())
            result.success, result.content = 200 <= result.status_code < 400, f"HTTP {result.status_code}"
        except Exception as e:
            result.error = str(e)
        result.duration_ms = (time.time() - start) * 1000
        return self._record(result)

    def extract_text(self, url: str) -> BrowserResult:
        start, result = time.time(), BrowserResult(action=BrowserAction.EXTRACT_TEXT, url=url)
        try:
            response = self._fetch_url(url)
            result.success, result.content, result.status_code = True, self._html_to_text(response["body"])[:5000], response["status_code"]
        except Exception as e:
            result.error = str(e)
        result.duration_ms = (time.time() - start) * 1000
        return self._record(result)

    def get_links(self, url: str) -> BrowserResult:
        start, result = time.time(), BrowserResult(action=BrowserAction.GET_LINKS, url=url)
        try:
            response = self._fetch_url(url)
            links = self._extract_links(response["body"], url)
            result.success, result.links, result.content, result.status_code = True, links[:100], f"Found {len(links)} links", response["status_code"]
        except Exception as e:
            result.error = str(e)
        result.duration_ms = (time.time() - start) * 1000
        return self._record(result)

    def analyze_page(self, url: str) -> PageInfo:
        start, info = time.time(), PageInfo(url=url)
        try:
            response = self._fetch_url(url)
            html = response["body"]
            info.status_code, info.content_type = response["status_code"], response.get("content_type", "")
            info.title, info.text_content = self._extract_title(html), self._html_to_text(html)[:5000]
            info.links, info.meta_tags = self._extract_links(html, url)[:50], self._extract_meta(html)
        except Exception as e:
            logger.debug("Page analysis failed: %s", e)
        info.load_time_ms = (time.time() - start) * 1000
        return info

    def get_history(self, limit: int = 20) -> List[BrowserResult]:
        return self._history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        if not self._history:
            return {"total_actions": 0, "success_rate": 0.0}
        return {"total_actions": len(self._history), "success_rate": sum(1 for r in self._history if r.success) / len(self._history), "playwright_available": self._playwright_available, "unique_domains": len({urlparse(r.url).netloc for r in self._history if r.url})}

    def _fetch_url(self, url: str) -> Dict[str, Any]:
        proc = subprocess.run(["curl", "-sL", "-w", "\n---HTTP_CODE:%{http_code}---\n---CONTENT_TYPE:%{content_type}---", url], capture_output=True, text=True, timeout=20)
        body = proc.stdout
        code_match, ct_match = re.search(r"---HTTP_CODE:(\d+)---", body), re.search(r"---CONTENT_TYPE:([^-]*)---", body)
        return {"body": re.sub(r"\n---HTTP_CODE:\d+---\n---CONTENT_TYPE:[^-]*---$", "", body), "status_code": int(code_match.group(1)) if code_match else 0, "content_type": ct_match.group(1).strip() if ct_match else ""}

    def _html_to_text(self, html: str) -> str:
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        for pat, repl in [(r"<br\s*/?>|<p[^>]*>", "\n"), (r"<h[1-6][^>]*>", "\n## "), (r"<li[^>]*>", "\n- ")]:
            text = re.sub(pat, repl, text, flags=re.IGNORECASE)
        return re.sub(r" {2,}", " ", re.sub(r"\n{3,}", "\n\n", re.sub(r"<[^>]+>", "", text))).strip()

    def _extract_title(self, html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        links, parsed_base = [], urlparse(base_url)
        for match in re.finditer(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE):
            href = match.group(1)
            if href.startswith("//"):
                href = f"{parsed_base.scheme}:{href}"
            elif href.startswith("/"):
                href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
            elif not href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                href = f"{base_url.rstrip('/')}/{href}"
            if href.startswith(("http://", "https://")):
                links.append(href)
        return list(dict.fromkeys(links))

    def _extract_meta(self, html: str) -> Dict[str, str]:
        return {m.group(1): m.group(2) for m in re.finditer(r'<meta\s+(?:name|property)=["\']([^"\']+)["\']\s+content=["\']([^"\']*)["\']', html, re.IGNORECASE)}

    def _check_playwright(self) -> bool:
        try:
            return subprocess.run(["python3", "-c", "import playwright"], capture_output=True, timeout=5).returncode == 0
        except Exception:
            return False

    def _record(self, result: BrowserResult) -> BrowserResult:
        self._history = (self._history + [result])[-100:]
        return result

__all__ = ["BrowserAgent", "BrowserAction", "BrowserResult", "PageInfo"]

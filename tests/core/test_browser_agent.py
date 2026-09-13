# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for BrowserAgent and associated classes (src/core/browser_agent.py).

All tests are hermetic and deterministic: subprocess and network calls are
mocked using unittest.mock.patch to eliminate external dependencies and ensure
zero skipped tests.
"""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.core.browser_agent import (
    BrowserAction,
    BrowserAgent,
    BrowserResult,
    PageInfo,
)


# ===========================================================================
# Dataclass tests
# ===========================================================================


class TestBrowserResult:
    def test_default_values(self):
        r = BrowserResult(action=BrowserAction.NAVIGATE)
        assert r.action == BrowserAction.NAVIGATE
        assert r.success is False
        assert r.url == ""
        assert r.content == ""
        assert r.status_code == 0
        assert r.screenshot_path == ""
        assert r.links == []
        assert r.metadata == {}
        assert r.duration_ms == 0.0
        assert r.error == ""

    def test_fields_settable(self):
        r = BrowserResult(
            action=BrowserAction.CHECK_STATUS,
            success=True,
            url="https://example.com",
            content="HTTP 200",
            status_code=200,
            screenshot_path="/tmp/shot.png",
            links=["https://example.com/1"],
            metadata={"title": "Example"},
            duration_ms=42.5,
            error="",
        )
        assert r.success is True
        assert r.status_code == 200
        assert r.links == ["https://example.com/1"]
        assert r.metadata["title"] == "Example"
        assert r.duration_ms == 42.5


class TestPageInfo:
    def test_default_values(self):
        p = PageInfo(url="https://test.com")
        assert p.url == "https://test.com"
        assert p.title == ""
        assert p.status_code == 0
        assert p.content_type == ""
        assert p.text_content == ""
        assert p.links == []
        assert p.forms == []
        assert p.meta_tags == {}
        assert p.load_time_ms == 0.0


# ===========================================================================
# BrowserAgent Initialization & Playwright Detection
# ===========================================================================


class TestBrowserAgentInit:
    def test_init_default_cache_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch.object(BrowserAgent, "_check_playwright", return_value=False):
            agent = BrowserAgent()
            assert agent._cache_dir == Path(".mekong/browser_cache")
            assert agent._cache_dir.exists()
            assert agent.llm_client is None
            assert agent._history == []
            assert agent._playwright_available is False

    def test_init_custom_cache_dir_and_llm(self, tmp_path):
        custom_cache = str(tmp_path / "custom_browser_cache")
        fake_llm = MagicMock()
        with patch.object(BrowserAgent, "_check_playwright", return_value=True):
            agent = BrowserAgent(llm_client=fake_llm, cache_dir=custom_cache)
            assert agent._cache_dir == Path(custom_cache)
            assert agent._cache_dir.exists()
            assert agent.llm_client is fake_llm
            assert agent._playwright_available is True

    def test_check_playwright_success(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        with patch("subprocess.run", return_value=mock_proc):
            agent = BrowserAgent()
            assert agent._check_playwright() is True

    def test_check_playwright_failure(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        with patch("subprocess.run", return_value=mock_proc):
            agent = BrowserAgent()
            assert agent._check_playwright() is False

    def test_check_playwright_exception(self):
        with patch("subprocess.run", side_effect=OSError("command not found")):
            agent = BrowserAgent()
            assert agent._check_playwright() is False


# ===========================================================================
# Action Methods: check_status, navigate, extract_text, get_links, analyze_page
# ===========================================================================


class TestBrowserAgentActions:
    @pytest.fixture(autouse=True)
    def setup_agent(self, tmp_path):
        with patch.object(BrowserAgent, "_check_playwright", return_value=False):
            self.agent = BrowserAgent(cache_dir=str(tmp_path / "cache"))

    def test_check_status_success_200(self):
        mock_proc = MagicMock()
        mock_proc.stdout = "200\n"
        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            result = self.agent.check_status("https://example.com/status")
            assert result.action == BrowserAction.CHECK_STATUS
            assert result.success is True
            assert result.status_code == 200
            assert result.content == "HTTP 200"
            assert result.duration_ms > 0 or result.duration_ms == 0.0
            assert len(self.agent._history) == 1
            mock_run.assert_called_once_with(
                ["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code}", "https://example.com/status"],
                capture_output=True,
                text=True,
                timeout=15,
            )

    def test_check_status_failure_500(self):
        mock_proc = MagicMock()
        mock_proc.stdout = "500"
        with patch("subprocess.run", return_value=mock_proc):
            result = self.agent.check_status("https://example.com/err")
            assert result.action == BrowserAction.CHECK_STATUS
            assert result.success is False
            assert result.status_code == 500
            assert result.content == "HTTP 500"

    def test_check_status_exception_handled(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("curl", 15)):
            result = self.agent.check_status("https://example.com/timeout")
            assert result.action == BrowserAction.CHECK_STATUS
            assert result.success is False
            assert "timed out" in result.error

    def test_navigate_success(self):
        html_payload = (
            "<html><head><title>Test Title</title></head>"
            "<body><h1>Hello</h1><p>World</p></body></html>"
        )
        fake_response = {
            "body": html_payload,
            "status_code": 200,
            "content_type": "text/html; charset=utf-8",
        }
        with patch.object(self.agent, "_fetch_url", return_value=fake_response):
            result = self.agent.navigate("https://example.com/page")
            assert result.action == BrowserAction.NAVIGATE
            assert result.success is True
            assert result.status_code == 200
            assert result.content == html_payload
            assert result.metadata["content_type"] == "text/html; charset=utf-8"
            assert result.metadata["title"] == "Test Title"
            assert result.error == ""

    def test_navigate_exception_handled(self):
        with patch.object(self.agent, "_fetch_url", side_effect=RuntimeError("connection refused")):
            result = self.agent.navigate("https://example.com/fail")
            assert result.action == BrowserAction.NAVIGATE
            assert result.success is False
            assert result.error == "connection refused"

    def test_extract_text_success(self):
        html_payload = "<html><body><h1>Title</h1><p>First paragraph.</p></body></html>"
        fake_response = {
            "body": html_payload,
            "status_code": 200,
            "content_type": "text/html",
        }
        with patch.object(self.agent, "_fetch_url", return_value=fake_response):
            result = self.agent.extract_text("https://example.com/text")
            assert result.action == BrowserAction.EXTRACT_TEXT
            assert result.success is True
            assert result.status_code == 200
            assert "## Title" in result.content
            assert "First paragraph." in result.content

    def test_extract_text_exception_handled(self):
        with patch.object(self.agent, "_fetch_url", side_effect=Exception("parse error")):
            result = self.agent.extract_text("https://example.com/text")
            assert result.action == BrowserAction.EXTRACT_TEXT
            assert result.success is False
            assert result.error == "parse error"

    def test_get_links_success(self):
        html_payload = """
        <html><body>
            <a href="/about">About</a>
            <a href="https://other.com/help">Help</a>
            <a href="javascript:void(0)">Ignored</a>
        </body></html>
        """
        fake_response = {
            "body": html_payload,
            "status_code": 200,
            "content_type": "text/html",
        }
        with patch.object(self.agent, "_fetch_url", return_value=fake_response):
            result = self.agent.get_links("https://example.com")
            assert result.action == BrowserAction.GET_LINKS
            assert result.success is True
            assert result.status_code == 200
            assert "https://example.com/about" in result.links
            assert "https://other.com/help" in result.links
            assert result.content == f"Found {len(result.links)} links"

    def test_get_links_exception_handled(self):
        with patch.object(self.agent, "_fetch_url", side_effect=ValueError("bad url")):
            result = self.agent.get_links("invalid-url")
            assert result.action == BrowserAction.GET_LINKS
            assert result.success is False
            assert result.error == "bad url"

    def test_analyze_page_success(self):
        html_payload = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>My Cool Page</title>
            <meta name="description" content="A description here">
            <meta property="og:title" content="OG Title">
        </head>
        <body>
            <p>Welcome to our platform!</p>
            <a href="/features">Features</a>
        </body>
        </html>
        """
        fake_response = {
            "body": html_payload,
            "status_code": 200,
            "content_type": "text/html",
        }
        with patch.object(self.agent, "_fetch_url", return_value=fake_response):
            info = self.agent.analyze_page("https://example.com/cool")
            assert info.url == "https://example.com/cool"
            assert info.status_code == 200
            assert info.content_type == "text/html"
            assert info.title == "My Cool Page"
            assert "Welcome to our platform!" in info.text_content
            assert "https://example.com/features" in info.links
            assert info.meta_tags.get("description") == "A description here"
            assert info.meta_tags.get("og:title") == "OG Title"
            assert info.load_time_ms >= 0.0

    def test_analyze_page_exception_caught(self):
        with patch.object(self.agent, "_fetch_url", side_effect=RuntimeError("curl failed")):
            info = self.agent.analyze_page("https://example.com/fail")
            assert info.url == "https://example.com/fail"
            assert info.status_code == 0
            assert info.title == ""
            assert info.text_content == ""
            assert info.links == []
            assert info.load_time_ms >= 0.0


# ===========================================================================
# History, Stats, and Internal Helper Methods
# ===========================================================================


class TestBrowserAgentHelpersAndStats:
    @pytest.fixture(autouse=True)
    def setup_agent(self, tmp_path):
        with patch.object(BrowserAgent, "_check_playwright", return_value=False):
            self.agent = BrowserAgent(cache_dir=str(tmp_path / "cache"))

    def test_get_history_and_truncation(self):
        for i in range(120):
            res = BrowserResult(action=BrowserAction.NAVIGATE, url=f"https://example.com/{i}")
            self.agent._record(res)
        assert len(self.agent._history) == 100
        recent = self.agent.get_history(limit=5)
        assert len(recent) == 5
        assert recent[-1].url == "https://example.com/119"

    def test_get_stats_empty(self):
        stats = self.agent.get_stats()
        assert stats["total_actions"] == 0
        assert stats["success_rate"] == 0.0

    def test_get_stats_with_data(self):
        r1 = BrowserResult(action=BrowserAction.NAVIGATE, success=True, url="https://site-a.com/1")
        r2 = BrowserResult(action=BrowserAction.NAVIGATE, success=False, url="https://site-b.com/2")
        r3 = BrowserResult(action=BrowserAction.NAVIGATE, success=True, url="https://site-a.com/3")
        r4 = BrowserResult(action=BrowserAction.NAVIGATE, success=True, url="")  # Empty url branch
        for r in (r1, r2, r3, r4):
            self.agent._record(r)

        stats = self.agent.get_stats()
        assert stats["total_actions"] == 4
        assert stats["success_rate"] == 0.75
        assert stats["playwright_available"] is False
        assert stats["unique_domains"] == 2

    def test_fetch_url_with_footer(self):
        stdout_text = (
            "<html><body>Hello</body></html>\n"
            "---HTTP_CODE:200---\n"
            "---CONTENT_TYPE:text/html; charset=utf-8---"
        )
        mock_proc = MagicMock()
        mock_proc.stdout = stdout_text
        with patch("subprocess.run", return_value=mock_proc):
            res = self.agent._fetch_url("https://example.com")
            assert res["body"] == "<html><body>Hello</body></html>"
            assert res["status_code"] == 200
            assert res["content_type"] == "text/html; charset=utf-8"

    def test_fetch_url_without_footer(self):
        stdout_text = "raw content without matches"
        mock_proc = MagicMock()
        mock_proc.stdout = stdout_text
        with patch("subprocess.run", return_value=mock_proc):
            res = self.agent._fetch_url("https://example.com")
            assert res["body"] == "raw content without matches"
            assert res["status_code"] == 0
            assert res["content_type"] == ""

    def test_html_to_text_full_transformations(self):
        html = """
        <html>
        <head>
            <style>body { color: red; }</style>
            <script>console.log('hi');</script>
        </head>
        <body>
            <h1>Heading 1</h1>
            <h2>Heading 2</h2>
            <p>Paragraph with <br/> line break</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <div>Extra    spaces   here</div>
            <p>Bottom</p>
        </body>
        </html>
        """
        text = self.agent._html_to_text(html)
        assert "color: red" not in text
        assert "console.log" not in text
        assert "## Heading 1" in text
        assert "## Heading 2" in text
        assert "- Item 1" in text
        assert "- Item 2" in text
        assert "Paragraph with" in text
        assert "    " not in text  # compressed spaces

    def test_extract_title_present_and_absent(self):
        assert self.agent._extract_title("<title>Hello World</title>") == "Hello World"
        assert self.agent._extract_title("<TITLE>  spaced  \n</title>") == "spaced"
        assert self.agent._extract_title("<div>No title here</div>") == ""

    def test_extract_links_various_schemes(self):
        html = """
        <a href="//cdn.example.com/asset.js">CDN</a>
        <a href="/root/path">Root</a>
        <a href="relative/file.html">Relative</a>
        <a href="https://external.com">External</a>
        <a href="http://insecure.com">Insecure</a>
        <a href="mailto:support@example.com">Mail</a>
        <a href="#section">Hash</a>
        <a href="javascript:void(0)">JS</a>
        <a href="https://external.com">External Duplicate</a>
        """
        base = "https://example.com/folder/index.html"
        links = self.agent._extract_links(html, base)
        assert "https://cdn.example.com/asset.js" in links
        assert "https://example.com/root/path" in links
        assert "https://example.com/folder/index.html/relative/file.html" in links
        assert "https://external.com" in links
        assert "http://insecure.com" in links
        assert not any("mailto:" in link for link in links)
        assert not any("#section" in link for link in links)
        assert not any("javascript:" in link for link in links)
        # Deduplication check
        assert links.count("https://external.com") == 1

    def test_extract_meta(self):
        html = """
        <meta name="author" content="Mekong Team">
        <meta property="og:description" content="AI platform">
        <meta charset="utf-8">
        """
        meta = self.agent._extract_meta(html)
        assert meta["author"] == "Mekong Team"
        assert meta["og:description"] == "AI platform"
        assert "charset" not in meta

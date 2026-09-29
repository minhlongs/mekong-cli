# Mekong CLI — Pure Standard-Library Content Marketing & Publishing Tests
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit and integration tests for Content Marketing & Editorial Publishing Suite.

Covers:
- Pure standard library ContentEngine core and SQLite persistence
- Multi-pillar content generation (one-person-company, ai-agents, solo-founder, binh-phap, zenos)
- Multi-format templates (blog, twitter, linkedin, youtube_script, newsletter)
- Editorial calendar and publication cadence calculation
- Channel telemetry and post reach statistics
- Typer CLI command surface with Rich rendering and --json mode
- Dual-engine MCP tool handlers (FastMCP & pure JSON-RPC)
- AST boundary verification (zero external HTTP or vendor SDK dependencies)
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.content_engine import ContentEngine, get_content_engine

runner = CliRunner()
app = build_app()


@pytest.fixture
def temp_content_engine(tmp_path: Path) -> ContentEngine:
    """Provide an isolated ContentEngine with temporary SQLite database."""
    db_file = tmp_path / "test_content.db"
    return ContentEngine(db_path=db_file)


class TestContentEngineCore:
    """Core domain logic tests for ContentEngine."""

    def test_registered_pillars(self, temp_content_engine: ContentEngine) -> None:
        pillars = temp_content_engine.get_pillars()
        assert "one-person-company" in pillars
        assert "ai-agents" in pillars
        assert "solo-founder" in pillars
        assert "binh-phap" in pillars
        assert "zenos" in pillars
        assert len(pillars["ai-agents"]["target_channels"]) >= 2

    def test_generate_content_across_formats(self, temp_content_engine: ContentEngine) -> None:
        # Blog format
        blog = temp_content_engine.generate_content(
            pillar="ai-agents",
            format_type="blog",
            topic="Harness Engineering Reliability",
        )
        assert blog["id"].startswith("cnt_")
        assert blog["format"] == "blog"
        assert "# Harness Engineering Reliability" in blog["body"]
        assert "metadata" in blog
        assert blog["metadata"]["word_count"] > 20

        # Twitter thread format
        tweet = temp_content_engine.generate_content(
            pillar="one-person-company",
            format_type="twitter",
        )
        assert tweet["format"] == "twitter"
        assert "1/5" in tweet["body"]

        # LinkedIn format
        li = temp_content_engine.generate_content(
            pillar="binh-phap",
            format_type="linkedin",
        )
        assert li["format"] == "linkedin"
        assert "Key Takeaways" in li["body"]

        # YouTube script format
        yt = temp_content_engine.generate_content(
            pillar="solo-founder",
            format_type="youtube_script",
        )
        assert yt["format"] == "youtube_script"
        assert "[HOOK" in yt["body"]

        # Newsletter format
        nl = temp_content_engine.generate_content(
            pillar="zenos",
            format_type="newsletter",
        )
        assert nl["format"] == "newsletter"
        assert "Founder Dispatch" in nl["body"]

    def test_save_and_list_content(self, temp_content_engine: ContentEngine, tmp_path: Path) -> None:
        item = temp_content_engine.generate_content(
            pillar="ai-agents",
            format_type="blog",
            topic="Autonomous Memory Meshes",
        )
        saved = temp_content_engine.save_content(item, output_dir=tmp_path, save_file=True)
        assert saved["saved_to_db"] is True
        assert saved["file_path"] is not None
        assert Path(saved["file_path"]).exists()

        items = temp_content_engine.list_content(status="draft")
        assert len(items) == 1
        assert items[0]["id"] == item["id"]

    def test_publish_lifecycle_and_channel_increment(self, temp_content_engine: ContentEngine) -> None:
        item = temp_content_engine.generate_content(pillar="binh-phap", format_type="blog", channel="blog")
        temp_content_engine.save_content(item)

        # Publish
        pub_res = temp_content_engine.update_status(item["id"], new_status="published")
        assert pub_res["success"] is True
        assert pub_res["status"] == "published"
        assert pub_res["published_at"] is not None

        # Verify channel post counter incremented
        channels = temp_content_engine.get_channel_stats()
        blog_ch = next(c for c in channels if c["channel_id"] == "blog")
        assert blog_ch["posts_published"] > 0

    def test_editorial_calendar_calculation(self, temp_content_engine: ContentEngine) -> None:
        item1 = temp_content_engine.generate_content(pillar="one-person-company")
        temp_content_engine.save_content(item1)

        cal = temp_content_engine.get_calendar()
        assert cal["total_items"] == 1
        assert cal["drafts_count"] == 1
        assert "one-person-company" in cal["pillars"]
        assert cal["pillars"]["one-person-company"]["drafts_count"] == 1

    def test_engine_status(self, temp_content_engine: ContentEngine) -> None:
        st = temp_content_engine.get_status()
        assert st["status"] == "HEALTHY"
        assert st["active_channels"] == 6
        assert st["registered_pillars"] == 5


class TestContentCliCommands:
    """Integration tests for Typer CLI commands."""

    def test_cli_content_overview_json(self) -> None:
        result = runner.invoke(app, ["content", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "HEALTHY"
        assert "calendar" in data

    def test_cli_content_overview_console(self) -> None:
        result = runner.invoke(app, ["content"])
        assert result.exit_code == 0
        assert "Mekong Content Marketing & Editorial Hub" in result.stdout

    def test_cli_content_generate_json(self) -> None:
        result = runner.invoke(
            app,
            [
                "content",
                "generate",
                "--pillar",
                "ai-agents",
                "--format",
                "twitter",
                "--topic",
                "Agentic Self-Repair Loops",
                "--save",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["pillar"] == "ai-agents"
        assert data["format"] == "twitter"
        assert "saved_to_db" in data

    def test_cli_content_calendar(self) -> None:
        result = runner.invoke(app, ["content", "calendar", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "pillars" in data

    def test_cli_content_channels(self) -> None:
        result = runner.invoke(app, ["content", "channels", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert any(c["channel_id"] == "twitter" for c in data)

    def test_cli_content_pillars(self) -> None:
        result = runner.invoke(app, ["content", "pillars", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "binh-phap" in data

    def test_cli_content_lifecycle_and_publish(self) -> None:
        # Generate & save
        gen_res = runner.invoke(
            app,
            ["content", "generate", "--pillar", "solo-founder", "--save", "--json"],
        )
        assert gen_res.exit_code == 0
        item = json.loads(gen_res.stdout)
        cid = item["id"]

        # List
        list_res = runner.invoke(app, ["content", "list", "--status", "draft", "--json"])
        assert list_res.exit_code == 0
        items = json.loads(list_res.stdout)
        assert any(i["id"] == cid for i in items)

        # Publish
        pub_res = runner.invoke(app, ["content", "publish", cid, "--json"])
        assert pub_res.exit_code == 0
        pub_data = json.loads(pub_res.stdout)
        assert pub_data["success"] is True
        assert pub_data["status"] == "published"


class TestContentMcpTools:
    """Parity tests for FastMCP and JSON-RPC MCP servers."""

    def test_scripts_mcp_content_tools(self) -> None:
        from scripts.mcp_server import (
            handle_content_calendar,
            handle_content_channels,
            handle_content_generate,
        )

        gen_out = handle_content_generate({
            "pillar": "ai-agents",
            "format_type": "blog",
            "topic": "MCP Autonomous Content Tool",
        })
        item = json.loads(gen_out)
        assert item["pillar"] == "ai-agents"
        assert item["format"] == "blog"

        cal_out = handle_content_calendar({})
        cal = json.loads(cal_out)
        assert "pillars" in cal

        ch_out = handle_content_channels({})
        channels = json.loads(ch_out)
        assert isinstance(channels, list)

    def test_core_mcp_content_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        gen_out = server._handle_content_generate(
            pillar="one-person-company",
            format_type="twitter",
        )
        item = json.loads(gen_out)
        assert item["pillar"] == "one-person-company"

        cal_out = server._handle_content_calendar()
        cal = json.loads(cal_out)
        assert "total_items" in cal

        ch_out = server._handle_content_channels()
        channels = json.loads(ch_out)
        assert any(c["channel_id"] == "blog" for c in channels)


class TestContentBoundary:
    """Enforce strict standard-library-only core boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        source_path = Path("src/core/content_engine.py")
        assert source_path.exists()
        tree = ast.parse(source_path.read_text(encoding="utf-8"))

        prohibited_modules = {
            "requests",
            "urllib3",
            "httpx",
            "aiohttp",
            "fastapi",
            "pydantic",
            "click",
            "typer",
            "rich",
            "boto3",
            "google",
            "anthropic",
            "openai",
        }

        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        violations = imported_modules.intersection(prohibited_modules)
        assert not violations, f"Boundary violation: content_engine.py imports prohibited modules: {violations}"

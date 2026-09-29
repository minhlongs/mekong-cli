# Mekong CLI — Pure Standard-Library Founder Assessment Tests
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_founder.py — Comprehensive tests for Autonomous Founder Genome & Psychometric Profiling Engine.
Verifies core engine, CLI command suite, dual MCP tools, and zero-dependency standard library boundary.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.founder_engine import FounderEngine, get_founder_engine

runner = CliRunner()
app = build_app()


@pytest.fixture
def clean_engine(tmp_path: Path) -> FounderEngine:
    """Fixture providing an isolated FounderEngine instance with a temporary database."""
    db_file = tmp_path / "founder_test.db"
    return FounderEngine(db_path=db_file)


class TestFounderEngine:
    """Unit tests for the FounderEngine core implementation."""

    def test_engine_init_and_default_seeds(self, clean_engine: FounderEngine) -> None:
        status = clean_engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_founders"] >= 3
        assert status["risk_distribution"]["conservative"] >= 1
        assert status["risk_distribution"]["moderate"] >= 1
        assert status["risk_distribution"]["aggressive"] >= 1

        f = clean_engine.get_founder("sovereign-architect")
        assert f is not None
        assert f["name"] == "sovereign-architect"
        assert f["archetype"] == "Sovereign Architect"
        assert "self_direction" in f["values"]
        assert f["big_five"]["openness"] >= 80

    def test_score_big_five(self, clean_engine: FounderEngine) -> None:
        # Default middle ratings (4 across all)
        scores = clean_engine.score_big_five({})
        assert scores["openness"] == 50
        assert scores["conscientiousness"] == 50
        assert scores["extraversion"] == 50
        assert scores["agreeableness"] == 50
        assert scores["emotional_stability"] == 50
        assert scores["neuroticism"] == 51

        # High extraversion: tipi_01=7, tipi_06=1 (reverse: 8 - 1 = 7) -> raw sum = 14 -> 100
        high_e = clean_engine.score_big_five({"tipi_01": 7, "tipi_06": 1})
        assert high_e["extraversion"] == 100

    def test_score_risk_profile(self, clean_engine: FounderEngine) -> None:
        ratings = {"financial": 8, "operational": 4, "technical": 10}
        scored = clean_engine.score_risk_profile(ratings)
        assert scored["financial"] == 80
        assert scored["operational"] == 40
        assert scored["technical"] == 100
        assert scored["reputational"] == 50  # default 5 -> 50

    def test_extract_biases(self, clean_engine: FounderEngine) -> None:
        biases_input = {
            "bias_confirmation": True,
            "bias_overconfidence": True,
            "bias_sunk_cost": False,
        }
        extracted = clean_engine.extract_biases(biases_input)
        assert "confirmation_bias" in extracted
        assert "overconfidence" in extracted
        assert "sunk_cost_fallacy" not in extracted

    def test_classify_risk_level(self, clean_engine: FounderEngine) -> None:
        # 1 bias, low risk -> conservative
        assert clean_engine.classify_risk_level(1, {"financial": 30}) == "conservative"
        # 4 biases, medium risk -> moderate
        assert clean_engine.classify_risk_level(4, {"financial": 50}) == "moderate"
        # 8 biases, high risk -> aggressive
        assert clean_engine.classify_risk_level(8, {"financial": 80}) == "aggressive"

    def test_assess_founder_and_retrieve(self, clean_engine: FounderEngine) -> None:
        genome = clean_engine.assess_founder(
            name="test-founder-alice",
            mission="Empower indie creators with sovereign agents",
            tipi_responses={"tipi_05": 7, "tipi_10": 1, "tipi_03": 7, "tipi_08": 1},
            values=["self_direction", "achievement"],
            risk_ratings={"financial": 7, "technical": 9},
            bias_responses={"bias_overconfidence": True},
        )
        assert genome["name"] == "test-founder-alice"
        assert genome["archetype"] in ["Sovereign Architect", "Technical Visionary"]
        assert genome["big_five"]["openness"] == 100
        assert genome["big_five"]["conscientiousness"] == 100
        assert "overconfidence" in genome["cognitive_biases"]

        retrieved = clean_engine.get_founder("test-founder-alice")
        assert retrieved is not None
        assert retrieved["id"] == genome["id"]

    def test_assess_founder_update(self, clean_engine: FounderEngine) -> None:
        clean_engine.assess_founder(name="bob", mission="Initial mission")
        updated = clean_engine.assess_founder(name="bob", mission="Updated mission statement")
        assert updated["mission"] == "Updated mission statement"

    def test_list_founders(self, clean_engine: FounderEngine) -> None:
        all_founders = clean_engine.list_founders()
        assert len(all_founders) >= 3

        conservative = clean_engine.list_founders(risk_level="conservative")
        assert len(conservative) >= 1
        for c in conservative:
            assert c["risk_level"] == "conservative"

    def test_analyze_founder(self, clean_engine: FounderEngine) -> None:
        analysis = clean_engine.analyze_founder("sovereign-architect")
        assert analysis["success"] is True
        assert analysis["name"] == "sovereign-architect"
        assert len(analysis["strengths"]) > 0
        assert "personality_summary" in analysis

        err = clean_engine.analyze_founder("nonexistent-founder-xyz")
        assert err["success"] is False
        assert "not found" in err["error"]


class TestFounderCli:
    """CLI tests for `mekong founder` commands."""

    def test_founder_overview_cli(self) -> None:
        result = runner.invoke(app, ["founder"])
        assert result.exit_code == 0
        assert "Mekong Founder Genome" in result.output

    def test_founder_overview_json_cli(self) -> None:
        result = runner.invoke(app, ["founder", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"
        assert "total_founders" in data
        assert "recent_founders" in data

    def test_founder_assess_cli(self) -> None:
        result = runner.invoke(
            app,
            [
                "founder",
                "assess",
                "--name",
                "cli-founder-charlie",
                "--mission",
                "Transform enterprise operations with AI",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "cli-founder-charlie"
        assert "big_five" in data

    def test_founder_review_cli(self) -> None:
        result = runner.invoke(
            app,
            ["founder", "review", "sovereign-architect", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "sovereign-architect"
        assert data["archetype"] == "Sovereign Architect"

    def test_founder_list_cli(self) -> None:
        result = runner.invoke(app, ["founder", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_founder_analyze_cli(self) -> None:
        result = runner.invoke(
            app,
            ["founder", "analyze", "sovereign-architect", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["name"] == "sovereign-architect"
        assert len(data["strengths"]) >= 1


class TestFounderMcpParity:
    """Verifies FastMCP and JSON-RPC 2.0 dual server parity for founder tools."""

    def test_scripts_mcp_founder_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_founder_assess,
            handle_founder_list,
            handle_founder_review,
        )

        # 1. Assess
        assess_res = handle_founder_assess({
            "name": "mcp-founder-test",
            "mission": "MCP Automated Assessment",
            "tipi_responses": {"tipi_01": 7, "tipi_06": 1},
            "values": ["achievement"],
        })
        assess_data = json.loads(assess_res)
        assert assess_data["name"] == "mcp-founder-test"

        # 2. Review
        review_res = handle_founder_review({"founder_id": "mcp-founder-test"})
        review_data = json.loads(review_res)
        assert review_data["name"] == "mcp-founder-test"
        assert review_data["big_five"]["extraversion"] == 100

        # 3. List
        list_res = handle_founder_list({"risk_level": "all", "limit": 10})
        list_data = json.loads(list_res)
        assert isinstance(list_data, list)
        assert any(f["name"] == "mcp-founder-test" for f in list_data)

    def test_core_mcp_server_founder_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        # 1. Assess
        res = server._handle_founder_assess(
            name="core-mcp-founder",
            mission="Core Server Test Founder",
        )
        data = json.loads(res)
        assert data["name"] == "core-mcp-founder"

        # 2. Review
        review_res = server._handle_founder_review(founder_id="core-mcp-founder")
        review_data = json.loads(review_res)
        assert review_data["name"] == "core-mcp-founder"

        # 3. List
        list_res = server._handle_founder_list(limit=20)
        list_data = json.loads(list_res)
        assert any(f["name"] == "core-mcp-founder" for f in list_data)

        # 4. Aliases
        assert server._handle_mekong_founder_assess == server._handle_founder_assess
        assert server._handle_mekong_founder_review == server._handle_founder_review
        assert server._handle_mekong_founder_list == server._handle_founder_list


class TestFounderCoreBoundary:
    """Strict AST standard-library boundary verification for `src/core/founder_engine.py`."""

    def test_no_prohibited_imports_in_founder_engine(self) -> None:
        engine_file = Path("src/core/founder_engine.py")
        assert engine_file.exists(), "src/core/founder_engine.py must exist"

        tree = ast.parse(engine_file.read_text(encoding="utf-8"))

        prohibited_prefixes = (
            "requests",
            "httpx",
            "aiohttp",
            "urllib3",
            "typer",
            "rich",
            "click",
            "fastmcp",
            "mcp",
            "pydantic",
            "openai",
            "anthropic",
            "google",
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in prohibited_prefixes:
                        assert not alias.name.startswith(prefix), (
                            f"Prohibited import '{alias.name}' detected in src/core/founder_engine.py"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for prefix in prohibited_prefixes:
                        assert not node.module.startswith(prefix), (
                            f"Prohibited from-import '{node.module}' detected in src/core/founder_engine.py"
                        )

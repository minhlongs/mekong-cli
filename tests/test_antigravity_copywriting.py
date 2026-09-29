# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_copywriting.py — Comprehensive tests for Conversion Copywriting & Persuasion Engine.
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
from src.core.copywriting_engine import CopywritingEngine, get_copywriting_engine

runner = CliRunner()
app = build_app()


@pytest.fixture
def clean_engine(tmp_path: Path) -> CopywritingEngine:
    """Fixture providing an isolated CopywritingEngine instance using a temporary database."""
    db_file = tmp_path / "copywriting_test.db"
    return CopywritingEngine(db_path=db_file)


class TestCopywritingEngine:
    """Unit tests for the CopywritingEngine core implementation."""

    def test_engine_init_and_status(self, clean_engine: CopywritingEngine) -> None:
        status = clean_engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["registered_formulas"] >= 5
        assert status["registered_styles"] >= 4
        assert status["saved_projects_count"] == 0

    def test_get_formulas(self, clean_engine: CopywritingEngine) -> None:
        formulas = clean_engine.get_formulas()
        assert "pas" in formulas
        assert "aida" in formulas
        assert "bab" in formulas
        assert "fab" in formulas
        assert "4us" in formulas
        assert len(formulas["pas"]["steps"]) == 3

    def test_get_styles(self, clean_engine: CopywritingEngine) -> None:
        styles = clean_engine.get_styles()
        assert "direct_response" in styles
        assert "technical_founder" in styles
        assert "punchy_minimalist" in styles
        assert "storytelling" in styles
        assert len(styles["direct_response"]["rules"]) > 0

    def test_generate_copy_landing_page(self, clean_engine: CopywritingEngine) -> None:
        copy_res = clean_engine.generate_copy(
            product_name="Mekong CLI",
            target_audience="Founders & Developers",
            formula="pas",
            copy_type="landing_page",
            key_benefit="autonomous engineering workflow execution",
            style="direct_response",
        )
        assert copy_res["product_name"] == "Mekong CLI"
        assert copy_res["formula"] == "pas"
        assert copy_res["type"] == "landing_page"
        assert "Mekong CLI" in copy_res["copy_text"]
        assert len(copy_res["metadata"]["sections"]) >= 3

    def test_generate_copy_email(self, clean_engine: CopywritingEngine) -> None:
        copy_res = clean_engine.generate_copy(
            product_name="Mekong Cloud",
            target_audience="CTOs & Engineering Leads",
            formula="aida",
            copy_type="email",
            key_benefit="cut DevOps spend by 40%",
            style="technical_founder",
        )
        assert copy_res["type"] == "email"
        assert copy_res["formula"] == "aida"
        assert "Subject:" in copy_res["copy_text"]

    def test_generate_copy_headline_and_cta_types(self, clean_engine: CopywritingEngine) -> None:
        hl_res = clean_engine.generate_copy(
            product_name="UltraCode",
            target_audience="Engineers",
            copy_type="headline",
        )
        assert hl_res["type"] == "headline"
        assert len(hl_res["copy_text"]) > 0

        cta_res = clean_engine.generate_copy(
            product_name="UltraCode",
            target_audience="Engineers",
            copy_type="cta",
        )
        assert cta_res["type"] == "cta"
        assert len(cta_res["copy_text"]) > 0

    def test_generate_headlines_angles(self, clean_engine: CopywritingEngine) -> None:
        headlines = clean_engine.generate_headlines(
            product_name="Mekong Flow",
            value_prop="scale agency revenues 10x with zero headcount",
            count=5,
        )
        assert len(headlines) == 5
        angles = {h["angle"] for h in headlines}
        assert "Direct / Benefit" in angles
        assert "Question / Intrigue" in angles
        assert any("Mekong Flow" in h["headline"] for h in headlines)

    def test_generate_cta_variations(self, clean_engine: CopywritingEngine) -> None:
        ctas = clean_engine.generate_cta(
            action_goal="start free trial",
            risk_reversal="Cancel anytime. 14-day zero-risk guarantee.",
        )
        assert len(ctas) >= 5
        types = {c["type"] for c in ctas}
        assert "High Urgency" in types
        assert "Low Friction" in types
        assert any("14-day" in c["microcopy"] for c in ctas)

    def test_save_and_list_projects(self, clean_engine: CopywritingEngine) -> None:
        copy_res = clean_engine.generate_copy(
            product_name="SaaS Pilot",
            target_audience="Founders",
            formula="bab",
            copy_type="landing_page",
        )
        saved = clean_engine.save_project(copy_res)
        assert saved["saved_to_db"] is True

        projects = clean_engine.list_projects()
        assert len(projects) == 1
        assert projects[0]["id"] == saved["id"]
        assert projects[0]["product_name"] == "SaaS Pilot"


class TestCopywritingCli:
    """CLI surface tests for `mekong copywriting`."""

    def test_cli_copywriting_overview_json(self) -> None:
        result = runner.invoke(app, ["copywriting", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "HEALTHY"
        assert "formulas" in data
        assert "styles" in data

    def test_cli_copywriting_overview_console(self) -> None:
        result = runner.invoke(app, ["copywriting"])
        assert result.exit_code == 0
        assert "Mekong Conversion Copywriting Engine" in result.stdout

    def test_cli_copywriting_generate_json(self) -> None:
        result = runner.invoke(
            app,
            [
                "copywriting",
                "generate",
                "Mekong Suite",
                "--audience",
                "Venture Builders",
                "--formula",
                "aida",
                "--type",
                "email",
                "--save",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["product_name"] == "Mekong Suite"
        assert data["formula"] == "aida"
        assert data["type"] == "email"
        assert "saved_to_db" in data

    def test_cli_copywriting_generate_console(self) -> None:
        result = runner.invoke(
            app,
            [
                "copywriting",
                "generate",
                "Mekong Test App",
                "--formula",
                "pas",
            ],
        )
        assert result.exit_code == 0
        assert "Copy Output" in result.stdout

    def test_cli_copywriting_headline_json(self) -> None:
        result = runner.invoke(
            app,
            [
                "copywriting",
                "headline",
                "SuperBot",
                "--value",
                "automate daily chores",
                "--count",
                "4",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 4
        assert "SuperBot" in data[0]["headline"]

    def test_cli_copywriting_cta_json(self) -> None:
        result = runner.invoke(
            app,
            [
                "copywriting",
                "cta",
                "book a demo",
                "--reversal",
                "No commitment required",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 5
        assert any(c["type"] == "Low Friction" for c in data)

    def test_cli_copywriting_formulas_json(self) -> None:
        result = runner.invoke(app, ["copywriting", "formulas", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "pas" in data
        assert "aida" in data

    def test_cli_copywriting_styles_json(self) -> None:
        result = runner.invoke(app, ["copywriting", "styles", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "direct_response" in data

    def test_cli_copywriting_list_json(self) -> None:
        # Generate & save one
        runner.invoke(
            app,
            ["copywriting", "generate", "QuickLaunch", "--save", "--json"],
        )
        result = runner.invoke(app, ["copywriting", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert any(p["product_name"] == "QuickLaunch" for p in data)


class TestCopywritingMcpTools:
    """Parity tests for FastMCP and JSON-RPC MCP servers."""

    def test_scripts_mcp_copywriting_tools(self) -> None:
        from scripts.mcp_server import (
            handle_copywriting_cta,
            handle_copywriting_generate,
            handle_copywriting_headline,
        )

        gen_out = handle_copywriting_generate({
            "product_name": "Antigravity Cloud",
            "target_audience": "Full-Stack Devs",
            "formula": "pas",
            "copy_type": "landing_page",
        })
        gen_data = json.loads(gen_out)
        assert gen_data["product_name"] == "Antigravity Cloud"
        assert gen_data["formula"] == "pas"

        hl_out = handle_copywriting_headline({
            "product_name": "Antigravity Cloud",
            "value_prop": "deploy autonomous agents in seconds",
            "count": 3,
        })
        hl_data = json.loads(hl_out)
        assert len(hl_data) == 3

        cta_out = handle_copywriting_cta({
            "action_goal": "deploy now",
            "risk_reversal": "Free tier available forever",
        })
        cta_data = json.loads(cta_out)
        assert len(cta_data) >= 5

    def test_core_mcp_copywriting_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        gen_out = server._handle_copywriting_generate(
            product_name="Core Agent",
            formula="bab",
        )
        gen_data = json.loads(gen_out)
        assert gen_data["product_name"] == "Core Agent"
        assert gen_data["formula"] == "bab"

        hl_out = server._handle_copywriting_headline(
            product_name="Core Agent",
            count=2,
        )
        hl_data = json.loads(hl_out)
        assert len(hl_data) == 2

        cta_out = server._handle_copywriting_cta(action_goal="launch")
        cta_data = json.loads(cta_out)
        assert len(cta_data) >= 5


class TestCopywritingBoundary:
    """Enforce strict standard-library-only core boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        source_path = Path("src/core/copywriting_engine.py")
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
        assert not violations, f"Boundary violation: copywriting_engine.py imports prohibited modules: {violations}"

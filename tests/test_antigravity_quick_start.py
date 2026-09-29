# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_quick_start.py — Verification suite for Autonomous Project Quick-Start Wizard & Template Kickoff Engine.

Tests:
1. QuickStartEngine core functionality (brainstorm, architecture plan, scaffolding, git/ship, revenue roadmap).
2. End-to-end kickoff across archetypes (cli, web, agent, fullstack) and dry-run simulation mode.
3. CLI command surface (`mekong quick-start`) in console, --dry-run, --json, and target directory modes.
4. Native MCP tools parity across FastMCP and fallback JSON-RPC engines.
5. AST standard library boundary verification.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.quick_start_engine import (
    ProjectTemplate,
    QuickStartEngine,
    QuickStartReport,
    get_quick_start_engine,
)


class TestQuickStartEngine:
    """Unit tests for pure standard-library QuickStartEngine."""

    def test_sanitize_name(self) -> None:
        engine = get_quick_start_engine()
        assert engine.sanitize_name("My Super App!") == "my-super-app"
        assert engine.sanitize_name("   test---tool   ") == "test-tool"
        assert engine.sanitize_name("___") == "mekong-app"

    def test_brainstorm_validation(self) -> None:
        engine = get_quick_start_engine()
        b_data = engine.brainstorm("fintech-bot", ProjectTemplate.AGENT)
        assert b_data["project_name"] == "fintech-bot"
        assert b_data["validation_decision"] == "GO"
        assert b_data["confidence_score"] > 0.9
        assert "value_proposition" in b_data
        assert len(b_data["target_personas"]) >= 2
        assert "swot" in b_data
        assert len(b_data["swot"]["strengths"]) >= 1

    def test_plan_architecture(self) -> None:
        engine = get_quick_start_engine()
        p_data = engine.plan_architecture("payment-hub", ProjectTemplate.WEB)
        assert "prd_markdown" in p_data
        assert "mermaid_architecture" in p_data
        assert "flowchart TD" in p_data["mermaid_architecture"]
        assert p_data["milestones_count"] == 5

    def test_revenue_roadmap(self) -> None:
        engine = get_quick_start_engine()
        r_data = engine.revenue_roadmap("analytics-cli", ProjectTemplate.CLI)
        assert "pricing_tiers" in r_data
        assert len(r_data["pricing_tiers"]) == 3
        assert len(r_data["channels"]) >= 3
        assert "$1,000 MRR" in r_data["target_mrr_90d"]

    def test_scaffold_files_cli(self, tmp_path: Path) -> None:
        engine = get_quick_start_engine()
        dest = tmp_path / "my-cli-tool"
        b_data = engine.brainstorm("my-cli-tool", ProjectTemplate.CLI)
        p_data = engine.plan_architecture("my-cli-tool", ProjectTemplate.CLI)
        r_data = engine.revenue_roadmap("my-cli-tool", ProjectTemplate.CLI)

        created = engine.scaffold_files(
            project_name="my-cli-tool",
            template=ProjectTemplate.CLI,
            target_dir=dest,
            brainstorm_data=b_data,
            plan_data=p_data,
            revenue_data=r_data,
            dry_run=False,
        )

        assert len(created) >= 6
        assert (dest / "README.md").exists()
        assert (dest / "plans/plan.md").exists()
        assert (dest / "plans/revenue.md").exists()
        assert (dest / "pyproject.toml").exists()
        assert (dest / "src/main.py").exists()
        assert (dest / "tests/test_main.py").exists()

    def test_verify_and_ship(self, tmp_path: Path) -> None:
        engine = get_quick_start_engine()
        dest = tmp_path / "ship-repo"
        dest.mkdir()
        (dest / "sample.txt").write_text("initial asset", encoding="utf-8")

        res = engine.verify_and_ship(dest, dry_run=False, init_git=True)
        assert res["git_initialized"] is True
        assert res["commit_sha"] is not None
        assert (dest / ".git").is_dir()

    def test_kickoff_end_to_end_agent(self, tmp_path: Path) -> None:
        engine = get_quick_start_engine()
        dest = tmp_path / "solo-agent"

        report = engine.kickoff(
            project_name="solo-agent",
            project_type="agent",
            target_dir=dest,
            dry_run=False,
            init_git=True,
        )

        assert isinstance(report, QuickStartReport)
        assert report.ok is True
        assert report.project_name == "solo-agent"
        assert report.project_type == "agent"
        assert len(report.steps) == 5
        assert (dest / "HARNESS.md").exists()
        assert (dest / "agents/registry.yaml").exists()
        assert (dest / "sops/ceo/sop.md").exists()
        assert (dest / "plans/plan.md").exists()
        assert report.git_initialized is True

        d = report.to_dict()
        assert d["ok"] is True
        assert len(d["steps"]) == 5
        assert len(d["files_created"]) >= 6

    def test_kickoff_dry_run(self, tmp_path: Path) -> None:
        engine = get_quick_start_engine()
        dest = tmp_path / "dry-run-project"

        report = engine.kickoff(
            project_name="dry-run-project",
            project_type="fullstack",
            target_dir=dest,
            dry_run=True,
        )

        assert report.ok is True
        assert not dest.exists()
        for step in report.steps:
            assert step.status == "simulated"


class TestCliQuickStartCommand:
    """Verification for `mekong quick-start` CLI command."""

    def test_cli_quick_start_dry_run_console(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["quick-start", "demo-saas", "--dry-run"])
        assert result.exit_code == 0
        assert "QUICK START KICKOFF" in result.output
        assert "DRY RUN" in result.output
        assert "Brainstorm & Validate" in result.output
        assert "Plan & Architecture" in result.output
        assert "Scaffold & Build" in result.output
        assert "Verify & Ship" in result.output
        assert "Revenue & Monetization" in result.output

    def test_cli_quick_start_dry_run_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["quick-start", "json-test", "--dry-run", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["project_name"] == "json-test"
        assert len(data["steps"]) == 5
        assert isinstance(data["next_steps"], list)

    def test_cli_quick_start_real_scaffold(self, tmp_path: Path) -> None:
        runner = CliRunner()
        app = build_app()
        target = tmp_path / "real-cli"
        result = runner.invoke(app, ["quick-start", "real-cli", "--dir", str(target), "--type", "cli", "--json"])
        assert result.exit_code == 0
        assert target.exists()
        assert (target / "README.md").exists()
        assert (target / "src/main.py").exists()


class TestMcpQuickStartToolsParity:
    """Parity tests for MCP quick-start tools across scripts and core implementations."""

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as smcp

        assert "mekong_quick_start_plan" in smcp.CORE_HANDLERS
        assert "mekong_quick_start_create" in smcp.CORE_HANDLERS

        # Test plan
        res_plan_str = smcp.handle_quick_start_plan({"project_name": "mcp-test-app", "project_type": "cli"})
        res_plan = json.loads(res_plan_str)
        assert res_plan.get("ok") is True
        assert res_plan.get("project_name") == "mcp-test-app"
        assert len(res_plan.get("steps", [])) == 5

        # Test dry-run create
        res_create_str = smcp.handle_quick_start_create({"project_name": "mcp-create-app", "dry_run": True})
        res_create = json.loads(res_create_str)
        assert res_create.get("ok") is True
        assert res_create.get("project_name") == "mcp-create-app"

    def test_src_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_plan_str = server._handle_quick_start_plan(project_name="core-mcp-plan", project_type="agent")
        res_plan = json.loads(res_plan_str)
        assert res_plan.get("ok") is True
        assert res_plan.get("project_name") == "core-mcp-plan"

        res_create_str = server._handle_quick_start_create(project_name="core-mcp-create", dry_run=True)
        res_create = json.loads(res_create_str)
        assert res_create.get("ok") is True

    def test_core_tools_spec_contains_quick_start_tools(self) -> None:
        import scripts.mcp_server as smcp

        names = {t["name"] for t in smcp.CORE_TOOLS_SPEC}
        assert "mekong_quick_start_plan" in names
        assert "mekong_quick_start_create" in names


class TestAstQuickStartCoreBoundary:
    """Assert standard-library-only core boundary adherence for quick_start_engine.py."""

    def test_pure_standard_library_imports(self) -> None:
        core_file = Path("src/core/quick_start_engine.py")
        assert core_file.exists()

        tree = ast.parse(core_file.read_text(encoding="utf-8"))
        allowed_stdlib = {
            "__future__",
            "logging",
            "os",
            "sys",
            "re",
            "time",
            "datetime",
            "json",
            "subprocess",
            "pathlib",
            "dataclasses",
            "enum",
            "typing",
            "src",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_pkg = alias.name.split(".")[0]
                    assert top_pkg in allowed_stdlib, f"Disallowed import: {top_pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_pkg = node.module.split(".")[0]
                    assert top_pkg in allowed_stdlib, f"Disallowed import from: {top_pkg}"

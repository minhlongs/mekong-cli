# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_dev.py — Autonomous Fullstack Developer & Code Quality Test Battery.

Covers:
1. DevEngine core operations (workspace diagnostics, AST audit, scaffolding, PR diff review, refactor advice)
2. Static analysis checks (dynamic execution, shell=True, bare except, credential leaks, long functions)
3. Module scaffolding across service, api, agent, util archetypes with unit tests
4. Pull request diff inspection and automated review verdicts
5. Typer CLI commands (dashboard, audit, scaffold, review, refactor, and --json output)
6. Dual-engine MCP tools (FastMCP & pure JSON-RPC handlers in scripts/ and src/core/)
7. Core boundary compliance (pure standard library, zero vendor SDKs)
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.core.dev_engine import (
    AuditSeverity,
    DevEngine,
    get_dev_engine,
)

runner = CliRunner()


@pytest.fixture
def temp_dev_engine(tmp_path: Path) -> DevEngine:
    """Fixture providing an isolated DevEngine rooted in a temporary directory."""
    return DevEngine(project_root=tmp_path)


class TestDevEngineCore:
    """Test suite for DevEngine workspace inspection, static audit, and scaffolding."""

    def test_developer_status(self, temp_dev_engine: DevEngine) -> None:
        status = temp_dev_engine.get_status()
        assert status.active_branch is not None
        assert status.python_version is not None
        assert status.virtualenv is not None
        assert isinstance(status.debt_markers, int)
        assert isinstance(status.uncommitted_files, int)

    def test_audit_codebase_clean(self, temp_dev_engine: DevEngine, tmp_path: Path) -> None:
        clean_file = tmp_path / "clean_module.py"
        clean_file.write_text(
            '"""Clean module."""\n\n'
            'def add(a: int, b: int) -> int:\n'
            '    """Add two numbers."""\n'
            '    return a + b\n',
            encoding="utf-8",
        )
        report = temp_dev_engine.audit_codebase(target_path=clean_file)
        assert report.total_files_scanned == 1
        assert report.high_count == 0
        assert report.quality_score >= 90
        assert report.grade == "A"

    def test_audit_codebase_hazards(self, temp_dev_engine: DevEngine, tmp_path: Path) -> None:
        hazard_file = tmp_path / "hazard_module.py"
        hazard_file.write_text(
            'import subprocess\n\n'
            'def run_unsafe(cmd: str):\n'
            '    eval("1 + 1")\n'
            '    subprocess.run(cmd, shell=True)\n'
            '    api_key = "dummy_secret_token_value_for_testing_12345"\n'
            '    try:\n'
            '        pass\n'
            '    except:\n'
            '        pass\n',
            encoding="utf-8",
        )
        report = temp_dev_engine.audit_codebase(target_path=hazard_file)
        assert report.total_files_scanned == 1
        assert report.high_count >= 2  # eval, shell=True, hardcoded secret
        assert report.medium_count >= 1  # bare except
        assert report.quality_score < 70

        patterns = [f.code_pattern for f in report.findings]
        assert any("eval" in p for p in patterns)
        assert any("shell=True" in p for p in patterns)
        assert any("bare except" in p for p in patterns)

    def test_scaffold_service_module(self, temp_dev_engine: DevEngine, tmp_path: Path) -> None:
        # Dry run first
        dry_res = temp_dev_engine.scaffold_module("payment_gateway", module_type="service", dry_run=True)
        assert dry_res.success is True
        assert dry_res.module_name == "payment_gateway"
        assert dry_res.module_type == "service"
        assert any("dry-run" in f for f in dry_res.files_created)

        # Real execution
        real_res = temp_dev_engine.scaffold_module("payment_gateway", module_type="service", dry_run=False)
        assert real_res.success is True
        assert len(real_res.files_created) == 2

        src_path = tmp_path / "src" / "services" / "payment_gateway.py"
        test_path = tmp_path / "tests" / "test_payment_gateway_service.py"
        assert src_path.exists()
        assert test_path.exists()

        content = src_path.read_text(encoding="utf-8")
        assert "class PaymentGatewayService:" in content
        assert "def execute(" in content

    def test_review_diff(self, temp_dev_engine: DevEngine) -> None:
        # Clean diff
        clean_diff = "diff --git a/file.py b/file.py\n+def add(a, b):\n+    return a + b\n"
        rep_clean = temp_dev_engine.review_diff(diff_text=clean_diff)
        assert rep_clean.status == "approved"
        assert rep_clean.files_changed == 1
        assert rep_clean.insertions == 2

        # Hazard diff
        hazard_diff = "diff --git a/file.py b/file.py\n+    eval(user_input)\n+    # TODO: fix vulnerability\n"
        rep_hazard = temp_dev_engine.review_diff(diff_text=hazard_diff)
        assert rep_hazard.status == "changes_requested"
        assert len(rep_hazard.findings) >= 2

    def test_analyze_refactor(self, temp_dev_engine: DevEngine, tmp_path: Path) -> None:
        test_file = tmp_path / "monolith.py"
        lines = ["# Monolith file\n"]
        # Add 120 lines to a function to trigger refactoring advice
        lines.append("def huge_function():\n")
        for i in range(100):
            lines.append(f"    x_{i} = {i}\n")
        lines.append("    return True\n")
        test_file.write_text("".join(lines), encoding="utf-8")

        advice = temp_dev_engine.analyze_refactor(target_file=test_file)
        assert advice.total_lines > 90
        assert advice.complexity_risk in ("moderate", "high")
        assert any("huge_function" in ap for ap in advice.anti_patterns_found)


class TestDevCliCommands:
    """Test suite for Typer CLI commands under `mekong dev`."""

    def test_cli_dev_overview_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(app, ["dev", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "active_branch" in data
        assert "uncommitted_files" in data
        assert "python_version" in data

    def test_cli_dev_overview_console(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(app, ["dev"])
        assert result.exit_code == 0
        assert "DEVELOPER WORKBENCH" in result.output or "Workspace" in result.output

    def test_cli_dev_audit_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(app, ["dev", "audit", "src/core", "--severity", "high", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "quality_score" in data
        assert "findings" in data

    def test_cli_dev_scaffold_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(
            app,
            [
                "dev",
                "scaffold",
                "billing_calculator",
                "--type",
                "service",
                "--dry-run",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["module_name"] == "billing_calculator"
        assert data["success"] is True

    def test_cli_dev_review_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(app, ["dev", "review", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "status" in data
        assert "diff_summary" in data

    def test_cli_dev_refactor_json(self, tmp_path: Path) -> None:
        from src.cli.app_setup import build_app

        dummy = tmp_path / "dummy.py"
        dummy.write_text("def test(): return 1\n", encoding="utf-8")

        app = build_app()
        result = runner.invoke(app, ["dev", "refactor", str(dummy), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["target_file"] == str(dummy)
        assert "complexity_risk" in data


class TestDevMcpTools:
    """Test suite for MCP dev tools across scripts/ and src/core/."""

    def test_scripts_mcp_dev_tools(self) -> None:
        import scripts.mcp_server as mcp_scripts

        assert "mekong_dev_audit" in mcp_scripts.CORE_HANDLERS
        assert "mekong_dev_scaffold" in mcp_scripts.CORE_HANDLERS
        assert "mekong_dev_review" in mcp_scripts.CORE_HANDLERS

        # Test audit
        audit_out = mcp_scripts.handle_dev_audit({"path": "src/core/dev_engine.py"})
        audit = json.loads(audit_out)
        assert "quality_score" in audit

        # Test scaffold
        scaff_out = mcp_scripts.handle_dev_scaffold({
            "name": "mcp_sample",
            "module_type": "api",
            "dry_run": True,
        })
        scaff = json.loads(scaff_out)
        assert scaff["module_name"] == "mcp_sample"
        assert scaff["success"] is True

        # Test review
        rev_out = mcp_scripts.handle_dev_review({})
        rev = json.loads(rev_out)
        assert "status" in rev

    def test_core_mcp_dev_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        audit_out = server._handle_dev_audit(path="src/core/dev_engine.py")
        audit = json.loads(audit_out)
        assert "quality_score" in audit

        scaff_out = server._handle_dev_scaffold(name="core_sample", module_type="agent", dry_run=True)
        scaff = json.loads(scaff_out)
        assert scaff["module_name"] == "core_sample"

        rev_out = server._handle_dev_review()
        rev = json.loads(rev_out)
        assert "status" in rev


class TestDevBoundary:
    """Ensure src/core/dev_engine.py complies with zero vendor SDK import boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        engine_file = Path(__file__).resolve().parents[1] / "src" / "core" / "dev_engine.py"
        assert engine_file.exists(), f"Missing {engine_file}"

        tree = ast.parse(engine_file.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "aiohttp", "openai", "anthropic", "google", "boto3"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed module import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import module: {pkg}"

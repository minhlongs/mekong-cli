# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_cto.py — Verification suite for Autonomous CTO Architecture & Review Suite.

Tests:
1. CTOEngine core functionality (ADR generation, code/security review, scorecard, stack health, 3-horizon roadmap).
2. Code review pattern detection (eval/exec, hardcoded secrets, shell=True, bare except, FIXME markers).
3. CLI command surface (`mekong cto` subcommands) in console and --json modes.
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
from src.core.cto_engine import (
    ADRRecord,
    CodeReviewReport,
    CTOEngine,
    EngineeringScorecard,
    Severity,
    get_cto_engine,
)


@pytest.fixture
def temp_cto_repo(tmp_path: Path) -> Path:
    """Create a temporary repository with clean and problematic source files."""
    repo = tmp_path / "cto-test-repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "CTO Tester"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "cto@mekong.ai"], cwd=repo, check=True, capture_output=True)

    # 1. Clean file
    src_dir = repo / "src"
    src_dir.mkdir()
    (src_dir / "clean_service.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n",
        encoding="utf-8",
    )

    # 2. File with security and code smell issues
    (src_dir / "risky_script.py").write_text(
        "import subprocess\n\n"
        "def run_risky():\n"
        "    api_key = 'sk_live_1234567890abcdef'\n"
        "    eval('1 + 2')\n"
        "    subprocess.run('ls -la', shell=True)\n"
        "    try:\n"
        "        pass\n"
        "    except:\n"
        "        pass\n"
        "    # FIXME: refactor this risky code\n",
        encoding="utf-8",
    )

    # Tests dir
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_sample.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname = 'test-proj'\n", encoding="utf-8")
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True, capture_output=True)

    return repo


class TestCTOEngine:
    """Unit tests for pure standard-library CTOEngine."""

    def test_generate_adr(self, temp_cto_repo: Path) -> None:
        engine = CTOEngine(repo_dir=temp_cto_repo)
        adr = engine.generate_adr(
            title="Event Streaming Architecture",
            context="Need real-time telemetry streaming",
            decision="Implement standard-library SSE and WebSocket hub",
            export=True,
        )

        assert isinstance(adr, ADRRecord)
        assert adr.number == 1
        assert adr.title == "Event Streaming Architecture"
        assert adr.status == "Accepted"
        assert "ADR-001" in adr.to_markdown()

        exported_file = temp_cto_repo / "reports" / "cto" / "architect" / "ADR-001-event-streaming-architecture.md"
        assert exported_file.exists()
        assert "Event Streaming Architecture" in exported_file.read_text(encoding="utf-8")

    def test_run_code_review_security_detection(self, temp_cto_repo: Path) -> None:
        engine = CTOEngine(repo_dir=temp_cto_repo)
        report = engine.run_code_review()

        assert isinstance(report, CodeReviewReport)
        assert report.ok is True
        assert report.files_scanned >= 2
        assert report.total_findings >= 4
        assert report.passed is False  # Blocker findings present

        rule_ids = {f.rule_id for f in report.findings}
        assert "SEC001-DYNAMIC-EXEC" in rule_ids
        assert "SEC002-HARDCODED-SECRET" in rule_ids
        assert "SEC003-SHELL-TRUE" in rule_ids
        assert "REL001-BARE-EXCEPT-PASS" in rule_ids
        assert "MNT001-FIXME-MARKER" in rule_ids

    def test_run_code_review_clean(self, temp_cto_repo: Path) -> None:
        engine = CTOEngine(repo_dir=temp_cto_repo)
        report = engine.run_code_review(target_path="src/clean_service.py")

        assert report.ok is True
        assert report.total_findings == 0
        assert report.passed is True

    def test_compute_scorecard(self, temp_cto_repo: Path) -> None:
        engine = CTOEngine(repo_dir=temp_cto_repo)
        sc = engine.compute_scorecard()

        assert isinstance(sc, EngineeringScorecard)
        assert sc.ok is True
        assert 0 <= sc.composite_score <= 100
        assert sc.grade in ("A+", "A", "B", "C", "D")
        assert "test_score" in sc.metrics
        assert "git_score" in sc.metrics
        assert len(sc.recommendations) >= 1

    def test_check_health(self, temp_cto_repo: Path) -> None:
        engine = CTOEngine(repo_dir=temp_cto_repo)
        health = engine.check_health()

        assert health.ok is True
        assert health.git_clean is True
        assert health.uncommitted_files == 0
        assert health.repo_branch == "main"
        assert len(health.python_version) > 0

    def test_generate_roadmap(self, temp_cto_repo: Path) -> None:
        engine = CTOEngine(repo_dir=temp_cto_repo)
        roadmap = engine.generate_roadmap()

        assert roadmap.ok is True
        assert "now" in roadmap.horizons
        assert "next" in roadmap.horizons
        assert "later" in roadmap.horizons
        assert roadmap.total_initiatives >= 3

    def test_executive_summary(self, temp_cto_repo: Path) -> None:
        engine = CTOEngine(repo_dir=temp_cto_repo)
        summary = engine.executive_summary()

        assert summary["ok"] is True
        assert "scorecard" in summary
        assert "health" in summary
        assert "top_priorities" in summary


class TestCliCtoCommand:
    """Verification for `mekong cto` CLI command surface."""

    def test_cli_cto_overview_console(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cto"])
        assert result.exit_code == 0
        assert "CTO EXECUTIVE BRIEFING" in result.output
        assert "Engineering Scorecard Metrics" in result.output

    def test_cli_cto_overview_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cto", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "scorecard" in data
        assert "health" in data

    def test_cli_cto_architect_console(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            ["cto", "architect", "Event Gateway", "--context", "Streaming requirement", "--decision", "Use SSE"],
        )
        assert result.exit_code == 0
        assert "ADR-" in result.output
        assert "Event Gateway" in result.output

    def test_cli_cto_architect_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cto", "architect", "Microservices Boundary", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["title"] == "Microservices Boundary"
        assert data["status"] == "Accepted"

    def test_cli_cto_review_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cto", "review", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "severity_counts" in data
        assert isinstance(data["findings"], list)

    def test_cli_cto_scorecard_json(self, tmp_path: Path) -> None:
        runner = CliRunner()
        app = build_app()
        export_file = tmp_path / "scorecard.json"
        result = runner.invoke(app, ["cto", "scorecard", "--export", str(export_file), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "composite_score" in data
        assert export_file.exists()

    def test_cli_cto_health_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cto", "health", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "git_clean" in data

    def test_cli_cto_roadmap_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cto", "roadmap", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "horizons" in data


class TestMcpCtoToolsParity:
    """Parity tests for MCP CTO tools across scripts and core implementations."""

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as smcp

        assert "mekong_cto_scorecard" in smcp.CORE_HANDLERS
        assert "mekong_cto_review" in smcp.CORE_HANDLERS
        assert "mekong_cto_architect" in smcp.CORE_HANDLERS

        # Test scorecard
        res_sc_str = smcp.handle_cto_scorecard({})
        res_sc = json.loads(res_sc_str)
        assert res_sc.get("ok") is True
        assert "composite_score" in res_sc

        # Test review
        res_rev_str = smcp.handle_cto_review({})
        res_rev = json.loads(res_rev_str)
        assert res_rev.get("ok") is True
        assert "severity_counts" in res_rev

        # Test architect
        res_adr_str = smcp.handle_cto_architect({"title": "MCP Architecture Test"})
        res_adr = json.loads(res_adr_str)
        assert res_adr.get("title") == "MCP Architecture Test"

    def test_src_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_sc_str = server._handle_cto_scorecard()
        res_sc = json.loads(res_sc_str)
        assert res_sc.get("ok") is True

        res_rev_str = server._handle_cto_review()
        res_rev = json.loads(res_rev_str)
        assert res_rev.get("ok") is True

        res_adr_str = server._handle_cto_architect(title="Core MCP Architecture Test")
        res_adr = json.loads(res_adr_str)
        assert res_adr.get("title") == "Core MCP Architecture Test"

    def test_core_tools_spec_contains_cto_tools(self) -> None:
        import scripts.mcp_server as smcp

        names = {t["name"] for t in smcp.CORE_TOOLS_SPEC}
        assert "mekong_cto_scorecard" in names
        assert "mekong_cto_review" in names
        assert "mekong_cto_architect" in names


class TestAstCtoCoreBoundary:
    """Assert standard-library-only core boundary adherence for cto_engine.py."""

    def test_pure_standard_library_imports(self) -> None:
        core_file = Path("src/core/cto_engine.py")
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
            "pytest",
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

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_daily.py — Verification suite for Autonomous Daily Executive Briefing & Standup Engine.

Tests:
1. DailyBriefingEngine core functionality (git activity parsing, debt scanning, system health, focus synthesis).
2. CLI command (mekong daily) in console, --json, --no-todos, and --export modes.
3. Native MCP tools parity across FastMCP and fallback JSON-RPC engines.
4. AST standard library boundary verification.
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
from src.core.daily_briefing import (
    CommitSummary,
    DailyBriefingEngine,
    DailyBriefingReport,
    DebtItem,
    get_daily_briefing_engine,
)


@pytest.fixture
def temp_daily_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository with mock commit history and source files containing debt markers."""
    repo = tmp_path / "daily-test-repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Briefing Tester"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "tester@mekong.ai"], cwd=repo, check=True, capture_output=True)

    # File 1: Python module with a TODO
    py_file = repo / "sample_service.py"
    py_file.write_text(
        "# sample_service.py\n"
        "def compute_roi():\n"
        "    # TODO: optimize calculation algorithm for scale\n"
        "    return 42\n",
        encoding="utf-8",
    )

    # File 2: Markdown docs with a FIXME
    md_file = repo / "README.md"
    md_file.write_text(
        "# Standup Test\n"
        "<!-- FIXME: document multi-tenant configuration params -->\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat(service): add initial compute roi logic"], cwd=repo, check=True, capture_output=True)

    # Second commit
    py_file.write_text(
        py_file.read_text(encoding="utf-8") + "\ndef health_probe():\n    return 'OK'\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "sample_service.py"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "chore: add health probe function"], cwd=repo, check=True, capture_output=True)

    # Leave an uncommitted dirty file
    untracked_file = repo / "scratch_notes.txt"
    untracked_file.write_text("WIP thoughts on queue metrics\n", encoding="utf-8")

    return repo


class TestDailyBriefingEngine:
    """Unit tests for pure standard-library DailyBriefingEngine."""

    def test_collect_git_activity(self, temp_daily_repo: Path) -> None:
        engine = DailyBriefingEngine(repo_dir=temp_daily_repo)
        activity = engine.collect_git_activity(since="7 days ago")

        assert activity["ok"] is True
        assert activity["current_branch"] == "main"
        assert activity["commits_count"] >= 2
        assert len(activity["recent_commits"]) >= 2
        assert any("feat(service)" in c.message for c in activity["recent_commits"])
        assert "scratch_notes.txt" in activity["dirty_files"] or activity["dirty_count"] >= 1

    def test_scan_codebase_debt(self, temp_daily_repo: Path) -> None:
        engine = DailyBriefingEngine(repo_dir=temp_daily_repo)
        debt = engine.scan_codebase_debt(max_items=10)

        assert len(debt) >= 2
        markers = {item.marker for item in debt}
        assert "TODO" in markers
        assert "FIXME" in markers

        todo_item = next(item for item in debt if item.marker == "TODO")
        assert "optimize calculation algorithm" in todo_item.text.lower()
        assert todo_item.line > 0

    def test_synthesize_today_focus(self, temp_daily_repo: Path) -> None:
        engine = DailyBriefingEngine(repo_dir=temp_daily_repo)
        activity = engine.collect_git_activity(since="24 hours ago")
        debt = engine.scan_codebase_debt(max_items=10)
        health = engine.check_system_health()

        priorities = engine.synthesize_today_focus(git_act=activity, debt_items=debt, health=health)
        assert len(priorities) >= 1
        assert any(isinstance(p, str) and len(p) > 5 for p in priorities)

    def test_generate_full_report(self, temp_daily_repo: Path) -> None:
        engine = DailyBriefingEngine(repo_dir=temp_daily_repo)
        report = engine.generate_report(since="7 days ago", include_debt=True)

        assert isinstance(report, DailyBriefingReport)
        assert report.ok is True
        assert report.current_branch == "main"
        assert report.commits_count >= 2
        assert len(report.debt_items) >= 2
        assert len(report.focus_priorities) >= 1

        d = report.to_dict()
        assert d["ok"] is True
        assert "commits_count" in d
        assert "recent_commits" in d
        assert "debt_items" in d
        assert "queue_depth" in d
        assert "focus_priorities" in d
        assert len(d["debt_items"]) >= 2


class TestCliDailyCommand:
    """Verification for `mekong daily` CLI command."""

    def test_cli_daily_console_mode(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["daily", "--since", "7 days ago"])
        assert result.exit_code == 0
        assert "DAILY REPORT" in result.output
        assert "Recent Git Activity" in result.output
        assert "Today's Strategic Focus" in result.output

    def test_cli_daily_json_mode(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["daily", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "commits_count" in data
        assert "focus_priorities" in data
        assert isinstance(data["focus_priorities"], list)

    def test_cli_daily_no_todos_flag(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["daily", "--no-todos", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert len(data["debt_items"]) == 0

    def test_cli_daily_export_file(self, tmp_path: Path) -> None:
        export_file = tmp_path / "briefing.json"
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["daily", "--export", str(export_file)])
        assert result.exit_code == 0
        assert export_file.exists()
        content = json.loads(export_file.read_text(encoding="utf-8"))
        assert content["ok"] is True
        assert "focus_priorities" in content


class TestMcpDailyToolsParity:
    """Parity tests for MCP daily tools across scripts and core implementations."""

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as smcp

        assert "mekong_daily_report" in smcp.CORE_HANDLERS
        assert "mekong_daily_focus" in smcp.CORE_HANDLERS

        # Test daily report
        res_report_str = smcp.handle_daily_report({"since": "7 days ago", "include_todos": True})
        res_report = json.loads(res_report_str)
        assert res_report.get("ok") is True
        assert "commits_count" in res_report
        assert "focus_priorities" in res_report

        # Test daily focus
        res_focus_str = smcp.handle_daily_focus({})
        res_focus = json.loads(res_focus_str)
        assert res_focus.get("ok") is True
        assert "focus_priorities" in res_focus
        assert isinstance(res_focus["focus_priorities"], list)

    def test_src_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_report_str = server._handle_daily_report(since="7 days ago", include_todos=True)
        res_report = json.loads(res_report_str)
        assert res_report.get("ok") is True
        assert "commits_count" in res_report

        res_focus_str = server._handle_daily_focus()
        res_focus = json.loads(res_focus_str)
        assert res_focus.get("ok") is True
        assert "focus_priorities" in res_focus

    def test_core_tools_spec_contains_daily_tools(self) -> None:
        import scripts.mcp_server as smcp

        names = {t["name"] for t in smcp.CORE_TOOLS_SPEC}
        assert "mekong_daily_report" in names
        assert "mekong_daily_focus" in names


class TestAstDailyCoreBoundary:
    """Assert standard-library-only core boundary adherence for daily_briefing.py."""

    def test_pure_standard_library_imports(self) -> None:
        core_file = Path("src/core/daily_briefing.py")
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

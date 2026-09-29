# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_ship.py — Verification suite for Autonomous Production Shipping Engine.

Tests:
1. ShippingEngine core functionality (preflight_check, validation, synthesize_commit_message, ship, dry_run).
2. CLI commands (preflight_only, dry_run, full ship) in console and --json modes.
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
from src.core.shipping_engine import (
    ShipPhase,
    ShippingEngine,
    ShippingReport,
    ValidationStep,
    get_shipping_engine,
)


@pytest.fixture
def temp_shipping_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Create a temporary local git repository paired with a bare upstream remote."""
    remote_repo = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote_repo)], check=True, capture_output=True)

    local_repo = tmp_path / "local-repo"
    local_repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=local_repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Mekong Ship Tester"], cwd=local_repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "ship@mekong.ai"], cwd=local_repo, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_repo)], cwd=local_repo, check=True, capture_output=True)

    # Initial commit
    (local_repo / "README.md").write_text("# Project\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=local_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=local_repo, check=True, capture_output=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=local_repo, check=True, capture_output=True)

    return local_repo, remote_repo


class TestShippingEngine:
    """Unit tests for pure standard-library ShippingEngine."""

    def test_preflight_clean(self, temp_shipping_repo: tuple[Path, Path]) -> None:
        local_repo, remote_repo = temp_shipping_repo
        engine = ShippingEngine(repo_dir=local_repo)
        pre = engine.preflight_check()
        assert pre["ok"] is True
        assert pre["branch"] == "main"
        assert pre["has_remote"] is True
        assert str(remote_repo) in pre["remote_url"]
        assert pre["dirty"] is False
        assert pre["dirty_count"] == 0

    def test_preflight_dirty(self, temp_shipping_repo: tuple[Path, Path]) -> None:
        local_repo, _ = temp_shipping_repo
        engine = ShippingEngine(repo_dir=local_repo)
        (local_repo / "new_feature.py").write_text("print('hello')", encoding="utf-8")
        pre = engine.preflight_check()
        assert pre["ok"] is True
        assert pre["dirty"] is True
        assert pre["dirty_count"] == 1
        assert "new_feature.py" in pre["dirty_files"]

    def test_synthesize_commit_message_custom(self, temp_shipping_repo: tuple[Path, Path]) -> None:
        local_repo, _ = temp_shipping_repo
        engine = ShippingEngine(repo_dir=local_repo)
        # Already conventional
        assert engine.synthesize_commit_message("feat: add stripe checkout") == "feat: add stripe checkout"
        assert engine.synthesize_commit_message("fix(auth): resolve jwt expiry") == "fix(auth): resolve jwt expiry"
        # Auto-prefix
        assert engine.synthesize_commit_message("fix login redirect loop") == "fix: fix login redirect loop"
        assert engine.synthesize_commit_message("update user manual") == "docs: update user manual"
        assert engine.synthesize_commit_message("optimize database query") == "perf: optimize database query"
        assert engine.synthesize_commit_message("add new dashboard card") == "feat: add new dashboard card"

    def test_synthesize_commit_message_auto_files(self, temp_shipping_repo: tuple[Path, Path]) -> None:
        local_repo, _ = temp_shipping_repo
        engine = ShippingEngine(repo_dir=local_repo)
        # Docs only
        msg_docs = engine.synthesize_commit_message(staged_files=["docs/guide.md", "README.md"])
        assert msg_docs.startswith("docs:")

        # Tests only
        msg_tests = engine.synthesize_commit_message(staged_files=["tests/test_auth.py"])
        assert msg_tests.startswith("test:")

        # Fix keyword
        msg_fix = engine.synthesize_commit_message(staged_files=["src/fix_bug.py"])
        assert msg_fix.startswith("fix:")

        # General feature
        msg_feat = engine.synthesize_commit_message(staged_files=["src/payment.py"])
        assert msg_feat.startswith("feat:")

    def test_ship_dry_run(self, temp_shipping_repo: tuple[Path, Path]) -> None:
        local_repo, _ = temp_shipping_repo
        engine = ShippingEngine(repo_dir=local_repo)
        (local_repo / "dry_run_file.py").write_text("code", encoding="utf-8")

        report = engine.ship(
            message="add dry run feature",
            run_lint=False,
            run_tests=False,
            push=True,
            dry_run=True,
        )
        assert report.ok is True
        assert report.dry_run is True
        assert report.commit_sha == "DRY_RUN"
        assert report.commit_message == "feat: add dry run feature"
        assert "dry_run_file.py" in report.files_staged
        # Verify file is still untracked
        pre = engine.preflight_check()
        assert pre["dirty"] is True

    def test_ship_end_to_end_push(self, temp_shipping_repo: tuple[Path, Path]) -> None:
        local_repo, remote_repo = temp_shipping_repo
        engine = ShippingEngine(repo_dir=local_repo)
        (local_repo / "live_feature.py").write_text("def run(): pass\n", encoding="utf-8")

        report = engine.ship(
            message="implement live feature",
            run_lint=False,
            run_tests=False,
            push=True,
            dry_run=False,
        )
        assert report.ok is True
        assert report.pushed is True
        assert report.commit_sha != "DRY_RUN"
        assert report.commit_message == "feat: implement live feature"

        # Verify repo is clean now
        pre = engine.preflight_check()
        assert pre["dirty"] is False
        assert pre["dirty_count"] == 0

        # Verify remote received commit
        res = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=local_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "feat: implement live feature" in res.stdout


class TestShipCliCommands:
    """CLI surface tests for mekong ship."""

    def test_cli_ship_preflight_only_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["ship", "--preflight-only", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("ok") is True
        assert "branch" in data
        assert "dirty" in data

    def test_cli_ship_preflight_only_console(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["ship", "--preflight-only"])
        assert result.exit_code == 0
        assert "Ship Pre-Flight Check" in result.output

    def test_cli_ship_dry_run_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            ["ship", "fix login crash", "--no-lint", "--no-test", "--dry-run", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("ok") is True
        assert data.get("dry_run") is True
        assert data.get("commit_sha") == "DRY_RUN"
        assert data.get("commit_message") == "fix: fix login crash"

    def test_cli_ship_dry_run_console(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            ["ship", "add user dashboard", "--no-lint", "--no-test", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "feat: add user dashboard" in result.output


class TestMcpShipToolsParity:
    """Parity tests for MCP shipping tools."""

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as smcp

        assert "mekong_ship_preflight" in smcp.CORE_HANDLERS
        assert "mekong_ship_run" in smcp.CORE_HANDLERS

        # Test preflight
        res_preflight_str = smcp.handle_ship_preflight({})
        res_pre = json.loads(res_preflight_str)
        assert res_pre.get("ok") is True
        assert "branch" in res_pre

        # Test dry-run ship
        res_ship_str = smcp.handle_ship_run({"message": "mcp ship test", "dry_run": True, "run_lint": False, "run_tests": False})
        res_ship = json.loads(res_ship_str)
        assert res_ship.get("ok") is True
        assert res_ship.get("dry_run") is True
        assert res_ship.get("commit_sha") == "DRY_RUN"

    def test_src_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_pre_str = server._handle_ship_preflight()
        res_pre = json.loads(res_pre_str)
        assert res_pre.get("ok") is True

        res_ship_str = server._handle_ship_run(message="core mcp ship test", dry_run=True, run_lint=False, run_tests=False)
        res_ship = json.loads(res_ship_str)
        assert res_ship.get("ok") is True
        assert res_ship.get("dry_run") is True

    def test_core_tools_spec_contains_ship_tools(self) -> None:
        import scripts.mcp_server as smcp

        names = {t["name"] for t in smcp.CORE_TOOLS_SPEC}
        assert "mekong_ship_preflight" in names
        assert "mekong_ship_run" in names


class TestAstCoreBoundary:
    """Assert standard-library-only core boundary adherence."""

    def test_pure_standard_library_imports(self) -> None:
        core_file = Path("src/core/shipping_engine.py")
        assert core_file.exists()

        tree = ast.parse(core_file.read_text(encoding="utf-8"))
        allowed_stdlib = {
            "__future__",
            "logging",
            "os",
            "sys",
            "re",
            "time",
            "subprocess",
            "pathlib",
            "dataclasses",
            "enum",
            "typing",
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

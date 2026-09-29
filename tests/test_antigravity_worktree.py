# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_worktree.py — Verification suite for Git Worktree Mesh.

Tests:
1. WorktreeManager core functionality (slugify, detect_prefix, repo_info, create, list, status, remove, prune).
2. CLI commands (create, list, status, remove, prune, info) in console and --json modes.
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
from src.core.worktree_manager import (
    WorktreeManager,
    WorktreeRecord,
    detect_prefix,
    get_worktree_manager,
    slugify,
)


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository with initial commit and .env.example."""
    repo = tmp_path / "test-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Mekong Tester"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "tester@mekong.ai"], cwd=repo, check=True, capture_output=True)

    # Create dummy initial files
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    (repo / ".env.example").write_text("API_KEY=secret_123\n", encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True, capture_output=True)
    return repo


class TestWorktreeManager:
    """Unit tests for pure standard-library WorktreeManager."""

    def test_slugify(self) -> None:
        assert slugify("Add OAuth2 Auth") == "add-oauth2-auth"
        assert slugify("fix/bug-in-parser.py") == "fix-bug-in-parser"
        assert slugify("  hello   world!  ") == "hello-world"
        assert slugify("---already-slugged---") == "already-slugged"
        assert slugify("") == "feature"
        # Truncation test
        long_text = "a" * 80
        assert len(slugify(long_text, max_length=30)) == 30

    def test_detect_prefix(self) -> None:
        assert detect_prefix("fix critical payment timeout") == "fix"
        assert detect_prefix("bug in database session pool") == "fix"
        assert detect_prefix("refactor gateway router") == "refactor"
        assert detect_prefix("update readme documentation") == "docs"
        assert detect_prefix("add chaos test suite") == "test"
        assert detect_prefix("optimize token serialization latency") == "perf"
        assert detect_prefix("bump dependency versions") == "chore"
        assert detect_prefix("implement new dashboard widget") == "feat"

    def test_repo_info(self, temp_git_repo: Path) -> None:
        wm = WorktreeManager(repo_dir=temp_git_repo)
        info = wm.get_repo_info()
        assert info["ok"] is True
        assert Path(info["repo_path"]).resolve() == temp_git_repo.resolve()
        assert info["base_branch"] == "main"
        assert info["current_branch"] == "main"
        assert info["dirty"] is False
        assert info["dirty_count"] == 0

    def test_repo_info_dirty_detection(self, temp_git_repo: Path) -> None:
        wm = WorktreeManager(repo_dir=temp_git_repo)
        (temp_git_repo / "dirty_file.txt").write_text("uncommitted", encoding="utf-8")
        info = wm.get_repo_info()
        assert info["ok"] is True
        assert info["dirty"] is True
        assert info["dirty_count"] == 1
        assert "dirty_file.txt" in info["dirty_files"]

    def test_create_worktree_dry_run(self, temp_git_repo: Path) -> None:
        wm = WorktreeManager(repo_dir=temp_git_repo)
        rec = wm.create_worktree(feature="checkout speedup", dry_run=True)
        assert rec.commit == "DRY_RUN"
        assert rec.branch == "perf/checkout-speedup"
        assert not Path(rec.path).exists()

    def test_create_worktree_and_list(self, temp_git_repo: Path) -> None:
        wm = WorktreeManager(repo_dir=temp_git_repo)
        rec = wm.create_worktree(feature="new agent feature")
        assert rec.branch == "feat/new-agent-feature"
        assert Path(rec.path).exists()
        assert (Path(rec.path) / "README.md").exists()
        # Verify .env.example was copied to .env
        assert (Path(rec.path) / ".env").exists()
        assert "API_KEY=secret_123" in (Path(rec.path) / ".env").read_text(encoding="utf-8")

        worktrees = wm.list_worktrees()
        assert len(worktrees) == 2
        branches = [w.branch for w in worktrees]
        assert "main" in branches
        assert "feat/new-agent-feature" in branches

    def test_create_worktree_no_prefix(self, temp_git_repo: Path) -> None:
        wm = WorktreeManager(repo_dir=temp_git_repo)
        rec = wm.create_worktree(feature="hotfix-urgent", no_prefix=True)
        assert rec.branch == "hotfix-urgent"
        assert Path(rec.path).exists()
        wm.remove_worktree(path_or_name=rec.branch, force=True)

    def test_status_clean_and_divergence(self, temp_git_repo: Path) -> None:
        wm = WorktreeManager(repo_dir=temp_git_repo)
        rec = wm.create_worktree(feature="status check feature")
        stat = wm.status(path_or_branch=rec.branch)
        assert stat["ok"] is True
        assert stat["worktree"]["branch"] == "feat/status-check-feature"
        assert stat["dirty"] is False
        assert stat["ahead"] == 0
        assert stat["behind"] == 0

        # Add commit in worktree and test divergence
        wt_path = Path(rec.path)
        (wt_path / "new_work.txt").write_text("done", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=wt_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Worktree commit"], cwd=wt_path, check=True, capture_output=True)

        stat_after = wm.status(path_or_branch=rec.branch)
        assert stat_after["ahead"] == 1
        assert stat_after["behind"] == 0

    def test_remove_and_prune(self, temp_git_repo: Path) -> None:
        wm = WorktreeManager(repo_dir=temp_git_repo)
        rec = wm.create_worktree(feature="temp to remove")
        assert Path(rec.path).exists()

        success = wm.remove_worktree(path_or_name=rec.branch, force=True)
        assert success is True
        assert not Path(rec.path).exists()

        worktrees = wm.list_worktrees()
        assert len(worktrees) == 1
        assert worktrees[0].branch == "main"

        pruned = wm.prune_worktrees(dry_run=True)
        assert isinstance(pruned, list)


class TestWorktreeCliCommands:
    """CLI surface tests for mekong worktree commands."""

    def test_cli_worktree_info_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["worktree", "info", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("ok") is True
        assert "repo_path" in data
        assert "base_branch" in data

    def test_cli_worktree_info_console(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["worktree", "info"])
        assert result.exit_code == 0
        assert "Repository Topology & Worktree Config" in result.output

    def test_cli_worktree_list_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["worktree", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(w.get("is_main") for w in data)

    def test_cli_worktree_list_console(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["worktree", "list"])
        assert result.exit_code == 0
        assert "Git Worktree Mesh" in result.output

    def test_cli_worktree_status_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["worktree", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("ok") is True
        assert "worktree" in data

    def test_cli_worktree_create_dry_run_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["worktree", "create", "payment gateway", "--dry-run", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("ok") is True
        assert data.get("dry_run") is True
        assert data["worktree"]["branch"] == "feat/payment-gateway"

    def test_cli_worktree_create_dry_run_console(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["worktree", "create", "fix login bug", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "fix/login-bug" in result.output

    def test_cli_worktree_prune_dry_run_json(self) -> None:
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["worktree", "prune", "--dry-run", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("ok") is True
        assert "pruned" in data


class TestMcpWorktreeToolsParity:
    """Parity tests for MCP tools across FastMCP and fallback pure-Python engines."""

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as smcp

        assert "mekong_worktree_create" in smcp.CORE_HANDLERS
        assert "mekong_worktree_list" in smcp.CORE_HANDLERS
        assert "mekong_worktree_status" in smcp.CORE_HANDLERS
        assert "mekong_worktree_remove" in smcp.CORE_HANDLERS

        # Test dry-run create
        res_create_str = smcp.handle_worktree_create({"feature": "mcp-agent-task", "dry_run": True})
        res_create = json.loads(res_create_str)
        assert res_create.get("ok") is True
        assert res_create.get("dry_run") is True
        assert res_create["worktree"]["branch"] == "feat/mcp-agent-task"

        # Test list
        res_list_str = smcp.handle_worktree_list({})
        res_list = json.loads(res_list_str)
        assert res_list.get("ok") is True
        assert "worktrees" in res_list
        assert res_list["count"] >= 1

        # Test status
        res_status_str = smcp.handle_worktree_status({})
        res_status = json.loads(res_status_str)
        assert res_status.get("ok") is True

        # Test remove missing arg
        res_remove_fail_str = smcp.handle_worktree_remove({})
        res_remove_fail = json.loads(res_remove_fail_str)
        assert res_remove_fail.get("ok") is False

    def test_src_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Test dry run create
        res_create_str = server._handle_worktree_create(feature="core-mcp-feature", dry_run=True)
        res_create = json.loads(res_create_str)
        assert res_create.get("ok") is True
        assert res_create.get("dry_run") is True
        assert res_create["worktree"]["branch"] == "feat/core-mcp-feature"

        # Test list
        res_list_str = server._handle_worktree_list()
        res_list = json.loads(res_list_str)
        assert res_list.get("ok") is True
        assert res_list["count"] >= 1

        # Test status
        res_status_str = server._handle_worktree_status()
        res_status = json.loads(res_status_str)
        assert res_status.get("ok") is True

    def test_core_tools_spec_contains_worktree_tools(self) -> None:
        import scripts.mcp_server as smcp

        names = {t["name"] for t in smcp.CORE_TOOLS_SPEC}
        assert "mekong_worktree_create" in names
        assert "mekong_worktree_list" in names
        assert "mekong_worktree_status" in names
        assert "mekong_worktree_remove" in names


class TestAstCoreBoundary:
    """Assert standard-library-only core boundary adherence."""

    def test_pure_standard_library_imports(self) -> None:
        core_file = Path("src/core/worktree_manager.py")
        assert core_file.exists()

        tree = ast.parse(core_file.read_text(encoding="utf-8"))
        allowed_stdlib = {
            "__future__",
            "logging",
            "os",
            "sys",
            "re",
            "shutil",
            "subprocess",
            "pathlib",
            "dataclasses",
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

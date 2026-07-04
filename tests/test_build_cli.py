"""Tests for the ``mekong build from-plan`` CLI command.

Loads build_app directly (same pattern as test_company_init_cli).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import build + plan sub-apps directly
from src.cli.commands.build import app as build_app
from src.cli.commands.plan import app as plan_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _invoke_build(argv: list[str], working_dir: Path):
    cwd = os.getcwd()
    os.chdir(working_dir)
    try:
        return runner.invoke(build_app, argv)
    finally:
        os.chdir(cwd)


def _init_and_plan(tmp_path: Path, lang: str = "en") -> None:
    """Init company and run plan from-init (mutates tmp_path in-place)."""
    from src.core.company_init import CompanyConfig, init_company

    cfg = CompanyConfig(
        company_name="BuildTestCo",
        product_type="saas",
        scenario="hybrid",
        budget_tier="minimal",
        primary_language=lang,
    )
    init_company(cfg, base_dir=tmp_path)

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(plan_app, [])
        if result.exception:
            raise result.exception
    finally:
        os.chdir(cwd)


# ---------------------------------------------------------------------------
# Contract: preconditions
# ---------------------------------------------------------------------------


class TestPreconditions:
    def test_errors_without_spec(self, tmp_path: Path) -> None:
        result = _invoke_build([], tmp_path)
        assert result.exit_code == 1

    def test_error_mentions_plan(self, tmp_path: Path) -> None:
        result = _invoke_build([], tmp_path)
        combined = (result.stdout + (result.stderr or "")).lower()
        assert "spec" in combined or "plan" in combined


# ---------------------------------------------------------------------------
# Contract: successful run
# ---------------------------------------------------------------------------


class TestSuccessfulRun:
    def test_creates_tasks_todo(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        result = _invoke_build([], tmp_path)
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        assert (tmp_path / ".mekong" / "TASKS.todo").exists()

    def test_tasks_todo_has_checklist_format(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        _invoke_build([], tmp_path)
        content = (tmp_path / ".mekong" / "TASKS.todo").read_text(encoding="utf-8")
        assert "- [ ]" in content, "Expected checklist format"

    def test_tasks_contain_required_phases(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        _invoke_build([], tmp_path)
        content = (tmp_path / ".mekong" / "TASKS.todo").read_text(encoding="utf-8")
        for phase in ("research", "implement", "test", "review"):
            assert f"[{phase}]" in content, f"Missing phase '{phase}'"

    def test_tasks_count_is_nonzero(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        _invoke_build([], tmp_path)
        content = (tmp_path / ".mekong" / "TASKS.todo").read_text(encoding="utf-8")
        checklist_items = content.count("- [ ]")
        assert checklist_items > 0, "Expected at least one task"

    def test_tasks_are_numbered(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        _invoke_build([], tmp_path)
        content = (tmp_path / ".mekong" / "TASKS.todo").read_text(encoding="utf-8")
        assert "001." in content, "Expected numbered tasks"


# ---------------------------------------------------------------------------
# Contract: --dry-run
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_exits_zero(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        result = _invoke_build(["--dry-run"], tmp_path)
        assert result.exit_code == 0

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        _invoke_build(["--dry-run"], tmp_path)
        assert not (tmp_path / ".mekong" / "TASKS.todo").exists()

    def test_dry_run_lists_domains(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        result = _invoke_build(["--dry-run"], tmp_path)
        assert result.exit_code == 0
        # Preview should list actual domain keywords, not metadata noise
        assert "User authentication" in result.stdout
        assert "Total:" in result.stdout

    def test_dry_run_vi_locale(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path, lang="vi")
        result = _invoke_build(["--dry-run"], tmp_path)
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Contract: --force overwrites
# ---------------------------------------------------------------------------


class TestForceFlag:
    def test_no_force_on_existing(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        _invoke_build([], tmp_path)
        # Re-run without force -> error
        result = _invoke_build([], tmp_path)
        assert result.exit_code == 1

    def test_force_overwrites(self, tmp_path: Path) -> None:
        _init_and_plan(tmp_path)
        _invoke_build([], tmp_path)
        # Overwrite with force
        result = _invoke_build(["--force"], tmp_path)
        assert result.exit_code == 0

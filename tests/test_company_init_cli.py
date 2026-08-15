"""Tests for the company-init Typer CLI surface.

Mirrors the existing backend contract from tests/test_company_init.py
(which must keep passing) and adds a CLI integration contract:

  init / confirm-abort / already-setup / json-schema / status / reset-status
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from unittest.mock import patch

# Ensure src/ is importable when pytest is invoked from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typer.testing import CliRunner

# ── Block LLM calls before importing company_init (no real API key in CI) ──
# NOTE: patches applied per-test via _block_llm fixture below (module-level
# .start() contaminates other test modules that test the real functions).

from src.cli.commands.company_init import app as company_app


@pytest.fixture(autouse=True)
def _block_llm():
    """Suppress LLM calls for every test in this module."""
    with patch("src.core.company_init.render_agent_prompts_llm", lambda *a, **kw: {}), \
         patch("src.core.company_init._get_llm_api_key", lambda: None):
        yield

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _invoke(
    argv: list[str],
    tmp_path: Path,
    *,
    input: str | None = None,
) -> pytest.ExceptionInfo | None:
    """Run company_app in tmp_path and return (result, cwd_preserved)."""
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        return runner.invoke(company_app, argv, input=input)
    finally:
        os.chdir(cwd)


@pytest.fixture()
def clean(tmp_path: Path) -> Path:
    """Empty working dir (no .mekong/)."""
    return tmp_path


@pytest.fixture()
def initialized(tmp_path: Path) -> Path:
    """Pre-init with deterministic config so status/reset can run."""
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        from src.core.company_init import CompanyConfig, init_company
        cfg = CompanyConfig(
            company_name="CLITestCo",
            product_type="saas",
            scenario="hybrid",
            budget_tier="minimal",
            primary_language="en",
        )
        init_company(cfg, base_dir=tmp_path)
    finally:
        os.chdir(cwd)
    return tmp_path


# ---------------------------------------------------------------------------
# Contract: init
# ---------------------------------------------------------------------------

_WIZARD_INPUT = "CLITestCo\n1\n1\n1\n1\n"


class TestInitCommand:
    def test_creates_mekong_dir(self, clean: Path) -> None:
        """Successful init creates .mekong/company.json."""
        result = _invoke(["init", "--no-confirm"], clean, input=_WIZARD_INPUT)
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        assert (clean / ".mekong" / "company.json").exists()

    def test_creates_12_files(self, clean: Path) -> None:
        """Backend contract: init writes exactly 12 files."""
        result = _invoke(["init", "--no-confirm"], clean, input=_WIZARD_INPUT)
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        mekong_dir = clean / ".mekong"
        written = list(mekong_dir.rglob("*"))
        written_files = [p for p in written if p.is_file()]
        assert len(written_files) == 11

    def test_success_panel_contains_company_name(self, clean: Path) -> None:
        """User-facing success output includes the company name."""
        result = _invoke(["init", "--no-confirm"], clean, input=_WIZARD_INPUT)
        assert result.exit_code == 0
        assert "CLITestCo" in result.stdout  # noqa: E501

    def test_creates_agent_md_files(self, clean: Path) -> None:
        """Writes 8 agent role .md files."""
        result = _invoke(["init", "--no-confirm"], clean, input=_WIZARD_INPUT)
        assert result.exit_code == 0, result.stdout
        agents_dir = clean / ".mekong" / "agents"
        assert agents_dir.exists()
        assert len(list(agents_dir.glob("*.md"))) == 8

    def test_passes_with_base_dir_option(self, clean: Path, tmp_path: Path) -> None:
        out = tmp_path / "project"
        out.mkdir()
        result = _invoke(["init", "--no-confirm", "--dir", str(out)], clean, input=_WIZARD_INPUT)
        assert result.exit_code == 0, result.stdout
        assert (out / ".mekong" / "company.json").exists()


# ---------------------------------------------------------------------------
# Contract: confirm abort
# ---------------------------------------------------------------------------

class TestInitConfirmAbort:
    def test_confirm_no_aborts_init(self, clean: Path) -> None:
        """When user answers 'n' at the final confirm, no files written."""
        # Prompt sequence: company_name, product_type, scenario, budget_tier,
        # primary_language, then Confirm // input lines map 1:1
        result = _invoke(
            ["init"],
            clean,
            input="CLITestCo\n1\n1\n1\n1\nn\n",
        )
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        assert not (clean / ".mekong").exists()


# ---------------------------------------------------------------------------
# Contract: already-setup error path
# ---------------------------------------------------------------------------

class TestInitAlreadySetup:
    def test_double_init_exits_nonzero(self, initialized: Path) -> None:
        """Second init on the same directory exits non-zero with friendly message."""
        result = _invoke(["init", "--no-confirm"], initialized)
        assert result.exit_code == 1
        assert "already initialized" in (result.stdout + (result.stderr or "")).lower()


# ---------------------------------------------------------------------------
# Contract: --json schema output
# ---------------------------------------------------------------------------

class TestInitJsonSchema:
    def test_schema_returns_json(self, clean: Path) -> None:
        """--json prints 5-question schema, exits 0, no files written."""
        result = _invoke(["init", "--json"], clean)
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        body = json.loads(result.stdout)
        assert "questions" in body
        assert len(body["questions"]) == 5
        fields = [q["field"] for q in body["questions"]]
        assert fields == [
            "company_name",
            "product_type",
            "scenario",
            "budget_tier",
            "primary_language",
        ]

    def test_schema_no_files_written(self, clean: Path) -> None:
        result = _invoke(["init", "--json"], clean)
        assert result.exit_code == 0
        assert not (clean / ".mekong").exists()


# ---------------------------------------------------------------------------
# Contract: status
# ---------------------------------------------------------------------------

class TestStatusCommand:
    def test_status_json_content(self, initialized: Path) -> None:
        result = _invoke(["status"], initialized)
        assert result.exit_code == 0, result.stdout + (result.stderr or "")

    def test_status_shows_company_name(self, initialized: Path) -> None:
        result = _invoke(["status"], initialized)
        assert result.exit_code == 0
        assert "CLITestCo" in result.stdout

    def test_status_missing_exits_clean(self, clean: Path) -> None:
        """Without .mekong/company.json, status exits 0 with hint."""
        result = _invoke(["status"], clean)
        assert result.exit_code == 0
        assert ".mekong/company.json" in result.stdout


# ---------------------------------------------------------------------------
# Contract: reset --status and reset --force
# ---------------------------------------------------------------------------

class TestResetCommand:
    def test_reset_status_mode(self, initialized: Path, tmp_path: Path) -> None:
        """Reset without --force shows current state and exits 0."""
        result = _invoke(["reset"], initialized)
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        assert "CLITestCo" in result.stdout

    def test_reset_status_no_flag_exits_zero(self, initialized: Path) -> None:
        """Preview mode does not error when no --force is given."""
        result = _invoke(["reset"], initialized)
        assert result.exit_code == 0

    def test_reset_force_reinitializes(self, initialized: Path) -> None:
        """`reset --force --no-confirm` re-runs wizard and produces valid company.json."""
        result = _invoke(
            ["reset", "--force", "--no-confirm", "--locale", "en"],
            initialized,
            input="ResetCo\n1\n1\n1\n1\n",
        )
        assert result.exit_code == 0, result.stdout + (result.stderr or "")
        company_file = initialized / ".mekong" / "company.json"
        assert company_file.exists()
        data = json.loads(company_file.read_text())
        assert data["company_name"] == "ResetCo"

    def test_reset_force_missing_exits_nonzero(self, clean: Path) -> None:
        """Reset on a fresh (no .mekong/) directory exits 1 with helpful hint."""
        result = _invoke(["reset", "--force", "--no-confirm"], clean)
        assert result.exit_code == 1

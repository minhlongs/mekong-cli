"""Tests for `agent-core eval` CLI subcommand.

Pattern: direct function call + capsys (NOT CliRunner — see memory.md trap).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_core import cli
from agent_core.evals import EvalRunSummary
from agent_core.memory import SeedMemory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_dataset(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "smoke.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


SMOKE_DATA = {
    "name": "smoke",
    "cases": [
        {"id": "greet", "prompt": "Say hello", "expect_substring": "[offline]"},
        {"id": "echo", "prompt": "Echo: offline", "expect_substring": "offline"},
    ],
}


def _make_memory(tmp_path: Path) -> SeedMemory:
    return SeedMemory(root=tmp_path / "ac")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_eval_cmd_offline_exit_zero(tmp_path, monkeypatch, capsys):
    """Smoke run with --offline stub passes all cases → exit 0 (no exception)."""
    ds_path = _write_dataset(tmp_path, SMOKE_DATA)
    mem = _make_memory(tmp_path)
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)

    # Should complete without raising typer.Exit(1)
    cli.eval_cmd(
        dataset=ds_path,
        baseline_run_id=0,
        as_json=False,
        offline=True,
        mekongd_url=None,
        threshold=0.05,
    )

    out = capsys.readouterr().out
    assert "TOTAL" in out
    assert "smoke" in out


def test_eval_cmd_offline_output_contains_case_ids(tmp_path, monkeypatch, capsys):
    ds_path = _write_dataset(tmp_path, SMOKE_DATA)
    mem = _make_memory(tmp_path)
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)

    cli.eval_cmd(
        dataset=ds_path,
        baseline_run_id=0,
        as_json=False,
        offline=True,
        mekongd_url=None,
        threshold=0.05,
    )

    out = capsys.readouterr().out
    assert "greet" in out
    assert "echo" in out


def test_eval_cmd_records_run_in_memory(tmp_path, monkeypatch):
    ds_path = _write_dataset(tmp_path, SMOKE_DATA)
    mem = _make_memory(tmp_path)
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)

    cli.eval_cmd(
        dataset=ds_path,
        baseline_run_id=0,
        as_json=False,
        offline=True,
        mekongd_url=None,
        threshold=0.05,
    )

    runs = mem.recent_eval_runs("smoke", limit=5)
    assert len(runs) == 1
    assert runs[0]["dataset_name"] == "smoke"
    assert runs[0]["passed"] == 2  # both cases pass with _OfflineLLM


def test_eval_cmd_json_output(tmp_path, monkeypatch, capsys):
    ds_path = _write_dataset(tmp_path, SMOKE_DATA)
    mem = _make_memory(tmp_path)
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)

    cli.eval_cmd(
        dataset=ds_path,
        baseline_run_id=0,
        as_json=True,
        offline=True,
        mekongd_url=None,
        threshold=0.05,
    )

    out = capsys.readouterr().out
    data = json.loads(out.strip())
    assert data["dataset"] == "smoke"
    assert data["passed"] == 2
    assert data["total"] == 2
    assert data["regressions"] == []
    assert "run_id" in data


def test_eval_cmd_regression_exits_nonzero(tmp_path, monkeypatch, capsys):
    """Second run with all-fail LLM triggers regression exit code 1."""
    import click

    ds_path = _write_dataset(tmp_path, SMOKE_DATA)
    mem = _make_memory(tmp_path)
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)

    # First run: all pass (offline stub)
    cli.eval_cmd(
        dataset=ds_path,
        baseline_run_id=0,
        as_json=False,
        offline=True,
        mekongd_url=None,
        threshold=0.05,
    )

    # Patch run_dataset to return all-fail summary for second run
    fail_summary = EvalRunSummary(
        dataset_name="smoke",
        total_score=0.0,
        total_weight=2.0,
        passed_count=0,
        total_count=2,
    )
    monkeypatch.setattr(cli, "run_dataset", lambda cases, llm: fail_summary)

    # typer.Exit raises click.exceptions.Exit (not SystemExit) when called directly
    with pytest.raises(click.exceptions.Exit) as exc_info:
        cli.eval_cmd(
            dataset=ds_path,
            baseline_run_id=0,
            as_json=False,
            offline=True,
            mekongd_url=None,
            threshold=0.05,
        )
    assert exc_info.value.exit_code == 1


def test_eval_cmd_smoke_fixture_end_to_end(monkeypatch, tmp_path, capsys):
    """Run against the real fixtures/evals/smoke.json with offline stub."""
    fixture = (
        Path(__file__).parent.parent / "fixtures" / "evals" / "smoke.json"
    )
    assert fixture.exists(), f"Fixture missing: {fixture}"

    mem = _make_memory(tmp_path)
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)

    cli.eval_cmd(
        dataset=fixture,
        baseline_run_id=0,
        as_json=False,
        offline=True,
        mekongd_url=None,
        threshold=0.05,
    )

    out = capsys.readouterr().out
    assert "TOTAL" in out
    assert "smoke" in out

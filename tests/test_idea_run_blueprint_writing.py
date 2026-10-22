"""Tests pinning `mk idea run` blueprint writing, --dry-run, --deep autopilot reach, and CLI flags."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from src.cli.idea_commands import app as idea_app

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAIN_IDEA = "A tenant invoicing app for Vietnamese SME accounting firms"
DEEP_IDEA = "open-core CLI for billing is a good idea"
runner = CliRunner()


def _idea_run(tmp_path: Path, idea: str, *extra: str) -> tuple[dict[str, Any], list[Path]]:
    """Invoke `mk idea run` writing under tmp_path; return (payload, files left on disk)."""
    out = tmp_path / "blueprint"
    res = runner.invoke(idea_app, ["run", idea, "--json", *extra, "--output-dir", str(out), "--repo-root", str(REPO_ROOT)])
    assert res.exit_code == 0, res.stdout
    return json.loads(res.stdout), sorted(out.iterdir()) if out.exists() else []


def _isolate_autopilot(monkeypatch: Any, tmp_path: Path) -> None:
    """IdeaLoop hardcodes REPO_ROOT for its run dir; point it at tmp_path so no repo state is written."""
    import mekong.autopilot.idea_loop as idea_loop_module

    monkeypatch.setattr(idea_loop_module, "REPO_ROOT", tmp_path / "loop")


def test_idea_run_writes_blueprint_files_to_output_dir(tmp_path: Path) -> None:
    """A plain (non-open-core) run must persist a multi-file blueprint, company.json included."""
    _, on_disk = _idea_run(tmp_path, PLAIN_IDEA)
    assert len(on_disk) > 1, f"expected multiple blueprint files on disk, got {on_disk}"
    assert any(p.name == "company.json" for p in on_disk), f"company.json missing from {[p.name for p in on_disk]}"
    for p in on_disk:
        assert p.is_file() and p.read_text(encoding="utf-8").strip(), f"blueprint file not written: {p}"


def test_idea_run_json_lists_only_paths_that_exist_on_disk(tmp_path: Path) -> None:
    """Every entry in `written` must be a real file, not a planned path."""
    payload, _ = _idea_run(tmp_path, PLAIN_IDEA)
    assert payload["written"], "expected a non-empty `written` list"
    for entry in payload["written"]:
        assert Path(entry).is_file(), f"`written` reports a path that does not exist: {entry}"


def test_idea_run_dry_run_writes_nothing_but_still_reports_files(tmp_path: Path) -> None:
    """--dry-run must leave the output dir untouched while still describing the plan."""
    payload, on_disk = _idea_run(tmp_path, PLAIN_IDEA, "--dry-run")
    assert payload["written"], "expected the dry-run to still report the planned file set"
    assert payload["flags"]["dry_run"] is True
    assert not on_disk, f"dry-run wrote to the output dir: {on_disk}"


def test_idea_run_deep_reaches_autopilot_and_still_writes_blueprint(tmp_path: Path, monkeypatch: Any) -> None:
    """--deep must reach the autopilot, report it, and write the blueprint regardless of its outcome.

    No LLM client is importable here, so IdeaLoop records a truthful `llm error` with ok=False;
    the offline degradation is the expected path. This pins that the loop was actually driven and
    reported (run_id / ok / audit_log), not that it succeeded.
    """
    _isolate_autopilot(monkeypatch, tmp_path)
    payload, on_disk = _idea_run(tmp_path, DEEP_IDEA, "--deep")

    deep_run = payload.get("deep_run")
    assert deep_run is not None, f"--deep did not reach the autopilot: keys={sorted(payload)}"
    for field in ("run_id", "ok", "audit_log"):
        assert field in deep_run, f"deep_run is missing {field}: {sorted(deep_run)}"
    assert deep_run["run_id"] and isinstance(deep_run["ok"], bool) and deep_run["reason"]
    assert Path(deep_run["audit_log"]).is_file(), f"autopilot audit log missing: {deep_run['audit_log']}"
    assert (tmp_path / "loop" / ".mekong").exists(), "autopilot run dir was not isolated under tmp_path"

    assert "company.json" in [p.name for p in on_disk], f"blueprint missing after the deep run: {[p.name for p in on_disk]}"


def test_idea_run_deep_dry_run_plans_without_disk_writes(tmp_path: Path, monkeypatch: Any) -> None:
    """`--deep --dry-run` must combine planning, the autopilot, and zero disk writes."""
    _isolate_autopilot(monkeypatch, tmp_path)
    payload, on_disk = _idea_run(tmp_path, DEEP_IDEA, "--deep", "--dry-run")
    assert all(k in payload["deep_run"] for k in ("run_id", "ok", "audit_log")), sorted(payload.get("deep_run", {}))
    assert "company.json" in payload["written"], f"planned set lacks company.json: {payload['written']}"
    assert not on_disk, f"dry-run wrote to the output dir: {on_disk}"


def test_idea_help_lists_dry_run_and_drops_auto_and_parallel() -> None:
    res = runner.invoke(idea_app, ["run", "--help"])
    assert res.exit_code == 0, res.stdout
    assert "--auto" not in res.stdout, "--auto should no longer be an `idea run` flag"
    assert "--parallel" not in res.stdout, "--parallel should no longer be an `idea run` flag"
    assert "--dry-run" in res.stdout, "--dry-run must be advertised by `idea run`"

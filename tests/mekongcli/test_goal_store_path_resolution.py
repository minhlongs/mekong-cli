# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Regression tests for goal store path resolution and gate anchoring.

Locks the behaviour that caused goals to vanish across working directories
and verification gates to pass vacuously.

Note: tests pass an explicit ``db_path`` so the user-level default in
``~/.mekong`` is never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mekongcli.core.goal_engine import SQLiteGoalStore, resolve_goal_db_path
from src.mekongcli.core.verification import VerificationPipeline, resolve_repo_root


def test_repo_local_store_is_not_shadowed_by_home(tmp_path: Path, monkeypatch) -> None:
    """An existing repo-local store must keep winning over the home default.

    The two stores hold independent histories (on this machine: ~1k repo-local
    goals vs ~64 home goals, zero shared ids). Letting the home path win would
    silently hide the repo-local history.
    """
    workdir = tmp_path / "work"
    workdir.mkdir()
    local_db = workdir / ".mekong" / "goals.sqlite3"
    local_db.parent.mkdir(parents=True)
    local_db.write_text("")
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.delenv("MEKONG_GOAL_DB", raising=False)
    monkeypatch.chdir(workdir)

    resolved = resolve_goal_db_path(None)

    assert resolved == (workdir / ".mekong" / "goals.sqlite3")
    assert resolved.is_absolute()
    assert resolved != fake_home / ".mekong" / "goals.sqlite3"


def test_default_store_path_is_home_anchored(tmp_path: Path, monkeypatch) -> None:
    """Default path must not depend on the process working directory."""
    fake_home = tmp_path / "fakehome"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.delenv("MEKONG_GOAL_DB", raising=False)
    # Run from a directory with no local .mekong so the home branch is taken.
    clean = tmp_path / "clean"
    clean.mkdir()
    monkeypatch.chdir(clean)

    resolved = resolve_goal_db_path(None)

    assert resolved == fake_home / ".mekong" / "goals.sqlite3"


def test_resolution_is_identical_from_any_directory(
    tmp_path: Path, monkeypatch
) -> None:
    """Same resolution from two different working directories."""
    fake_home = tmp_path / "home2"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.delenv("MEKONG_GOAL_DB", raising=False)

    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()

    monkeypatch.chdir(dir_a)
    from_a = resolve_goal_db_path(None)
    monkeypatch.chdir(dir_b)
    from_b = resolve_goal_db_path(None)

    assert from_a == from_b
    assert Path.cwd() == dir_b  # confirms the chdir above actually took effect


def test_store_path_is_absolute_and_survives_chdir(tmp_path: Path, monkeypatch) -> None:
    """A relative repo-local path breaks on the first chdir after construction."""
    workdir = tmp_path / "work"
    local_db = workdir / ".mekong" / "goals.sqlite3"
    local_db.parent.mkdir(parents=True)
    local_db.write_text("")
    # Pin the home directory so a fixture regression cannot reach the real
    # developer database, which holds genuine goal history.
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.delenv("MEKONG_GOAL_DB", raising=False)
    monkeypatch.chdir(workdir)

    store = SQLiteGoalStore()
    assert Path(str(store.db_path)).is_absolute()
    assert store.db_path == local_db.resolve()

    (workdir / "subdir").mkdir()
    monkeypatch.chdir(workdir / "subdir")
    store.list_goals()  # previously raised OperationalError


def test_clean_gate_output_is_not_treated_as_vacuous(tmp_path: Path) -> None:
    """A genuine clean result must still pass (criterion 3, pass direction)."""
    from src.mekongcli.core.execution import LocalExecutor
    from src.mekongcli.core.verification.gates import _looks_vacuous

    (tmp_path / "ok.py").write_text("VALUE = 1\n")
    outcome = LocalExecutor(tmp_path, timeout_seconds=60).run("ruff check .")

    assert outcome.success
    assert not _looks_vacuous(outcome.stdout or "", outcome.stderr or "")


def test_empty_target_gate_output_is_treated_as_vacuous(tmp_path: Path) -> None:
    """A gate that examined nothing must fail (criterion 3, fail direction)."""
    from src.mekongcli.core.execution import LocalExecutor
    from src.mekongcli.core.verification.gates import _looks_vacuous

    (tmp_path / "empty").mkdir()
    outcome = LocalExecutor(tmp_path / "empty", timeout_seconds=60).run("ruff check .")

    assert outcome.success  # exits 0, yet
    assert _looks_vacuous(outcome.stdout or "", outcome.stderr or "")  # must fail


def test_ruff_success_banner_is_not_a_vacuous_marker() -> None:
    """Direct guard: ruff's normal success banner must never be rejected.

    A prior revision listed the banner in the markers, which made a genuinely
    clean repo permanently fail the standard profile.
    """
    from src.mekongcli.core.verification.gates import _VACUOUS_PASS_MARKERS

    assert "All checks passed!" not in _VACUOUS_PASS_MARKERS


def test_vacuous_gate_record_preserves_raw_exit_code(tmp_path: Path) -> None:
    """The persisted record must stay auditable when a gate exits 0 but fails."""
    from src.mekongcli.core.verification import VerificationGate, VerificationPipeline

    (tmp_path / "empty").mkdir()
    pipeline = VerificationPipeline(
        cwd=tmp_path,
        gates=(VerificationGate("ruff", "ruff check .", timeout_seconds=60),),
    )
    pipeline.cwd = tmp_path / "empty"
    passed, results = pipeline.run()

    assert passed is False  # exit 0, yet the gate fails
    record = results[0]
    assert record["passed"] is False
    assert record["exit_code_success"] is True
    assert record["vacuous_output"] is True


def test_repo_root_falls_back_to_start_when_no_marker(tmp_path: Path, monkeypatch) -> None:
    """With no src/main.py anywhere up the chain, anchoring returns the start."""
    from src.mekongcli.core.verification import resolve_repo_root

    monkeypatch.setenv("MEKONG_ROOT", str(tmp_path / "absent"))
    leaf = tmp_path / "no" / "src" / "marker"
    leaf.mkdir(parents=True)

    assert resolve_repo_root(leaf) == leaf.resolve()


def test_env_override_takes_precedence(tmp_path: Path, monkeypatch) -> None:
    override = tmp_path / "custom.sqlite3"
    monkeypatch.setenv("MEKONG_GOAL_DB", str(override))

    assert resolve_goal_db_path(None) == override


def test_explicit_argument_takes_precedence(tmp_path: Path, monkeypatch) -> None:
    explicit = tmp_path / "explicit.sqlite3"
    monkeypatch.setenv("MEKONG_GOAL_DB", str(tmp_path / "ignored.sqlite3"))

    assert resolve_goal_db_path(explicit) == explicit


def test_repo_root_ignores_invocation_directory(tmp_path: Path) -> None:
    """Gates must anchor to the project root, not the caller's directory."""
    nested = tmp_path / "deeply" / "nested" / "subdir"
    nested.mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("# stub\n")
    monkeypatched = pytest.MonkeyPatch()
    monkeypatched.setenv("MEKONG_ROOT", "")

    assert resolve_repo_root(nested) == tmp_path.resolve()

    monkeypatched.undo()


def test_repo_root_prefers_env_var(tmp_path: Path, monkeypatch) -> None:
    env_root = tmp_path / "envroot"
    (env_root / "src").mkdir(parents=True)
    (env_root / "src" / "main.py").write_text("# stub\n")
    monkeypatch.setenv("MEKONG_ROOT", str(env_root))

    assert resolve_repo_root(tmp_path) == env_root.resolve()


def test_gate_target_is_sanitised_for_repo_root(tmp_path: Path, monkeypatch) -> None:
    """Pipeline must rewrite an arbitrary cwd to the real project root."""
    this_repo = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("MEKONG_ROOT", str(this_repo))
    monkeypatch.delenv("MEKONG_GOAL_DB", raising=False)

    foreign = tmp_path / "somewhere_else"
    foreign.mkdir()

    pipeline = VerificationPipeline(cwd=foreign)

    assert pipeline.cwd == this_repo.resolve()


def test_store_init_from_explicit_path_does_not_touch_home(tmp_path: Path) -> None:
    """Existing behaviour preserved: explicit paths are honoured verbatim."""
    target = tmp_path / "goals.sqlite3"

    store = SQLiteGoalStore(target)

    assert store.db_path == target
    assert target.exists()

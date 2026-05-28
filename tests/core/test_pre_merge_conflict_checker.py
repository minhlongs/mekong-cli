"""Tests for src/core/pre_merge_conflict_checker.py."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.core.pre_merge_conflict_checker import (
    ConflictFile, MergeCheckResult,
    check_merge_conflicts, format_conflict_report, get_merge_base,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _base_repo(tmp_path: Path) -> Path:
    _git(["init", "-b", "main"], tmp_path)
    _git(["config", "user.email", "t@t.com"], tmp_path)
    _git(["config", "user.name", "T"], tmp_path)
    return tmp_path


@pytest.fixture()
def clean_repo(tmp_path: Path) -> Path:
    """main + feature branch with no overlapping edits."""
    p = _base_repo(tmp_path)
    (p / "a.txt").write_text("line1\n")
    _git(["add", "."], p); _git(["commit", "-m", "init"], p)

    _git(["checkout", "-b", "feature"], p)
    (p / "b.txt").write_text("feature-only\n")
    _git(["add", "."], p); _git(["commit", "-m", "feat"], p)
    _git(["checkout", "main"], p)
    return p


@pytest.fixture()
def conflict_repo(tmp_path: Path) -> Path:
    """main + feature both modify the same line in a.txt."""
    p = _base_repo(tmp_path)
    (p / "a.txt").write_text("shared\n")
    _git(["add", "."], p); _git(["commit", "-m", "init"], p)

    _git(["checkout", "-b", "feature"], p)
    (p / "a.txt").write_text("feature edit\n")
    _git(["add", "."], p); _git(["commit", "-m", "feature edit"], p)

    _git(["checkout", "main"], p)
    (p / "a.txt").write_text("main edit\n")
    _git(["add", "."], p); _git(["commit", "-m", "main edit"], p)
    return p


# ---------------------------------------------------------------------------
# get_merge_base
# ---------------------------------------------------------------------------

def test_get_merge_base_returns_sha(clean_repo: Path) -> None:
    base = get_merge_base("main", "feature", str(clean_repo))
    assert len(base) == 40 and all(c in "0123456789abcdef" for c in base)


def test_get_merge_base_raises_non_repo(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        get_merge_base("main", "feature", str(tmp_path))


# ---------------------------------------------------------------------------
# check_merge_conflicts — clean merge
# ---------------------------------------------------------------------------

def test_clean_merge_no_conflicts(clean_repo: Path) -> None:
    r = check_merge_conflicts("feature", "main", str(clean_repo))
    assert r.has_conflicts is False
    assert r.conflicting_files == []
    assert r.source_branch == "feature" and r.target_branch == "main"
    assert r.checked_at > 0


# ---------------------------------------------------------------------------
# check_merge_conflicts — conflicting merge
# ---------------------------------------------------------------------------

def test_conflict_detected(conflict_repo: Path) -> None:
    r = check_merge_conflicts("feature", "main", str(conflict_repo))
    assert r.has_conflicts is True
    paths = [cf.path for cf in r.conflicting_files]
    assert any("a.txt" in p for p in paths), f"Expected a.txt in {paths}"


def test_conflict_files_have_type(conflict_repo: Path) -> None:
    r = check_merge_conflicts("feature", "main", str(conflict_repo))
    for cf in r.conflicting_files:
        assert cf.conflict_type and isinstance(cf.path, str) and cf.path


# ---------------------------------------------------------------------------
# check_merge_conflicts — error cases
# ---------------------------------------------------------------------------

def test_raises_non_repo(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        check_merge_conflicts("a", "b", str(tmp_path))


# ---------------------------------------------------------------------------
# format_conflict_report
# ---------------------------------------------------------------------------

def test_report_clean(clean_repo: Path) -> None:
    r = check_merge_conflicts("feature", "main", str(clean_repo))
    report = format_conflict_report(r)
    assert "Clean" in report and "feature" in report and "main" in report


def test_report_with_conflicts() -> None:
    r = MergeCheckResult(
        has_conflicts=True,
        conflicting_files=[
            ConflictFile("src/foo.py", "content"),
            ConflictFile("docs/bar.md", "add/add"),
        ],
        source_branch="feature", target_branch="main", checked_at=1000.0,
    )
    report = format_conflict_report(r)
    assert "CONFLICTS FOUND" in report
    assert "src/foo.py" in report and "docs/bar.md" in report
    assert "Manually edit" in report  # hint for "content"


def test_report_unknown_conflict_type() -> None:
    r = MergeCheckResult(
        has_conflicts=True,
        conflicting_files=[ConflictFile("x.py", "novel/type")],
        source_branch="a", target_branch="b", checked_at=0.0,
    )
    report = format_conflict_report(r)
    assert "novel/type" in report and "Resolve manually" in report

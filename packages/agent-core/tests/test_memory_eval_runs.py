"""Tests for SeedMemory eval_runs table — record_eval_run + recent_eval_runs."""

from __future__ import annotations

from agent_core.memory import SeedMemory


def test_record_eval_run_returns_positive_id(tmp_memory: SeedMemory):
    run_id = tmp_memory.record_eval_run(
        dataset_name="smoke",
        dataset_hash="abc123",
        score=3.0,
        passed=3,
        total=4,
        details={"cases": []},
    )
    assert isinstance(run_id, int)
    assert run_id > 0


def test_recent_eval_runs_empty_when_none(tmp_memory: SeedMemory):
    runs = tmp_memory.recent_eval_runs("nonexistent")
    assert runs == []


def test_recent_eval_runs_returns_correct_fields(tmp_memory: SeedMemory):
    tmp_memory.record_eval_run(
        dataset_name="smoke",
        dataset_hash="deadbeef",
        score=2.0,
        passed=2,
        total=3,
        details={"cases": [{"id": "x", "passed": True}]},
    )
    runs = tmp_memory.recent_eval_runs("smoke")
    assert len(runs) == 1
    r = runs[0]
    assert r["dataset_name"] == "smoke"
    assert r["dataset_hash"] == "deadbeef"
    assert r["score"] == 2.0
    assert r["passed"] == 2
    assert r["total"] == 3
    assert r["details"]["cases"][0]["id"] == "x"


def test_recent_eval_runs_ordered_newest_first(tmp_memory: SeedMemory):
    for i in range(3):
        tmp_memory.record_eval_run(
            dataset_name="smoke",
            dataset_hash=f"hash{i}",
            score=float(i),
            passed=i,
            total=3,
            details={},
        )
    runs = tmp_memory.recent_eval_runs("smoke", limit=3)
    # newest inserted last → score=2 should be first
    assert runs[0]["score"] == 2.0
    assert runs[1]["score"] == 1.0
    assert runs[2]["score"] == 0.0


def test_recent_eval_runs_respects_limit(tmp_memory: SeedMemory):
    for _i in range(5):
        tmp_memory.record_eval_run(
            dataset_name="ds",
            dataset_hash="h",
            score=1.0,
            passed=1,
            total=1,
            details={},
        )
    runs = tmp_memory.recent_eval_runs("ds", limit=2)
    assert len(runs) == 2


def test_recent_eval_runs_isolates_by_dataset_name(tmp_memory: SeedMemory):
    tmp_memory.record_eval_run(
        dataset_name="alpha", dataset_hash="h1", score=1.0, passed=1, total=1, details={}
    )
    tmp_memory.record_eval_run(
        dataset_name="beta", dataset_hash="h2", score=0.0, passed=0, total=1, details={}
    )
    alpha_runs = tmp_memory.recent_eval_runs("alpha")
    beta_runs = tmp_memory.recent_eval_runs("beta")
    assert len(alpha_runs) == 1
    assert len(beta_runs) == 1
    assert alpha_runs[0]["score"] == 1.0
    assert beta_runs[0]["score"] == 0.0


def test_record_eval_run_ids_are_autoincrement(tmp_memory: SeedMemory):
    id1 = tmp_memory.record_eval_run(
        dataset_name="x", dataset_hash="h", score=1.0, passed=1, total=1, details={}
    )
    id2 = tmp_memory.record_eval_run(
        dataset_name="x", dataset_hash="h", score=1.0, passed=1, total=1, details={}
    )
    assert id2 > id1

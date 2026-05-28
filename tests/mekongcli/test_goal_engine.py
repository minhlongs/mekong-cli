from __future__ import annotations

from pathlib import Path

from src.mekongcli.core.goal_engine import GoalEngine, GoalStatus, SQLiteGoalStore, TaskStatus
from src.mekongcli.core.verification import VerificationGate, VerificationPipeline


class MemorySink:
    def __init__(self) -> None:
        self.entries = []

    def record(self, entry) -> None:
        self.entries.append(entry)


def build_engine(tmp_path: Path) -> GoalEngine:
    return GoalEngine(
        store=SQLiteGoalStore(tmp_path / "goals.sqlite3"),
        cwd=tmp_path,
        memory_store=MemorySink(),
    )


def test_goal_create_persists_task_graph_and_criteria(tmp_path: Path) -> None:
    engine = build_engine(tmp_path)
    goal = engine.create_goal("Build production-grade forex multi-agent platform")

    snapshot = engine.status(goal.id)

    assert goal.status == GoalStatus.PLANNED
    assert snapshot["goal"]["title"] == "Build production-grade forex multi-agent platform"
    assert len(snapshot["tasks"]) == 7
    assert {task["role"] for task in snapshot["tasks"]} >= {
        "architect",
        "backend",
        "infra",
        "qa",
        "security",
        "docs",
        "reviewer",
    }
    assert len(snapshot["criteria"]) == 4
    assert snapshot["checkpoints"][0]["label"] == "goal-created"


def test_goal_run_completes_tasks_and_satisfies_with_none_profile(tmp_path: Path) -> None:
    engine = build_engine(tmp_path)
    goal = engine.create_goal("Ship autonomous engineering OS")

    result = engine.run_goal(goal.id, verification_profile="none")
    snapshot = engine.status(goal.id)

    assert result.status == GoalStatus.SATISFIED
    assert all(task["status"] == TaskStatus.COMPLETED.value for task in snapshot["tasks"])
    assert snapshot["verification"]["passed"] is True
    assert all(item["satisfied"] is True for item in snapshot["criteria"])
    assert len(snapshot["events"]) >= 3
    assert len(snapshot["memory"]) >= 2


def test_goal_run_rejects_unknown_verification_profile(tmp_path: Path) -> None:
    engine = build_engine(tmp_path)
    goal = engine.create_goal("Invalid profile mission")

    try:
        engine.run_goal(goal.id, verification_profile="bogus")
    except ValueError as exc:
        assert "Unknown verification profile" in str(exc)
        assert "none, smoke, standard" in str(exc)
    else:
        raise AssertionError("unknown profile should fail before verification runs")

    snapshot = engine.status(goal.id)
    assert snapshot["goal"]["status"] == GoalStatus.PLANNED.value
    assert all(task["status"] == TaskStatus.PENDING.value for task in snapshot["tasks"])
    assert snapshot["verification"] is None


def test_goal_cancel_blocks_future_run(tmp_path: Path) -> None:
    engine = build_engine(tmp_path)
    goal = engine.create_goal("Cancelled mission")
    engine.cancel_goal(goal.id)

    try:
        engine.run_goal(goal.id, verification_profile="none")
    except RuntimeError as exc:
        assert "cancelled" in str(exc)
    else:
        raise AssertionError("cancelled goal should not run")


def test_goal_store_survives_new_engine_instance(tmp_path: Path) -> None:
    db_path = tmp_path / "goals.sqlite3"
    engine = GoalEngine(store=SQLiteGoalStore(db_path), cwd=tmp_path, memory_store=MemorySink())
    goal = engine.create_goal("Persistent mission")

    resumed = GoalEngine(store=SQLiteGoalStore(db_path), cwd=tmp_path, memory_store=MemorySink())
    snapshot = resumed.status(goal.id)

    assert snapshot["goal"]["id"] == goal.id
    assert len(snapshot["tasks"]) == 7


def test_verification_missing_binary_records_failed_gate(tmp_path: Path) -> None:
    pipeline = VerificationPipeline(
        cwd=tmp_path,
        gates=(
            VerificationGate(
                "missing-tool",
                "definitely-missing-mekong-verifier",
            ),
        ),
    )

    passed, results = pipeline.run()

    assert passed is False
    assert results[0]["passed"] is False
    assert results[0]["exit_code"] == 127
    assert "No such file or directory" in str(results[0]["blocked_reason"])


def test_verification_pipeline_rejects_unknown_profile(tmp_path: Path) -> None:
    try:
        VerificationPipeline.for_profile("bogus", tmp_path)
    except ValueError as exc:
        assert "Unknown verification profile" in str(exc)
    else:
        raise AssertionError("unknown profile should not fall back to standard gates")


def test_goal_run_parallel_completes_tasks_with_none_profile(tmp_path: Path) -> None:
    engine = build_engine(tmp_path)
    goal = engine.create_goal("Ship parallel autonomous engine")

    result = engine.run_goal_parallel(goal.id, verification_profile="none", max_workers=3)
    snapshot = engine.status(goal.id)

    assert result.status == GoalStatus.SATISFIED
    assert all(task["status"] == TaskStatus.COMPLETED.value for task in snapshot["tasks"])
    assert snapshot["verification"]["passed"] is True
    assert all(item["satisfied"] is True for item in snapshot["criteria"])
    assert len(snapshot["events"]) >= 3



def test_goal_run_parallel_completes_tasks_and_satisfies_with_none_profile(tmp_path: Path) -> None:
    engine = build_engine(tmp_path)
    goal = engine.create_goal("Ship parallel engine OS")

    result = engine.run_goal_parallel(goal.id, verification_profile="none")
    snapshot = engine.status(goal.id)

    assert result.status == GoalStatus.SATISFIED
    assert all(task["status"] == TaskStatus.COMPLETED.value for task in snapshot["tasks"])
    assert snapshot["verification"]["passed"] is True
    assert all(item["satisfied"] is True for item in snapshot["criteria"])
    assert len(snapshot["events"]) >= 3
    assert len(snapshot["memory"]) >= 2

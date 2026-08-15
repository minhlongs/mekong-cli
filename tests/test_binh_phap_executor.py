"""Tests for Binh Phap DAG executor and recovery.

Covers:
- ExecutionState: load/save/mark round-trip, missing file, corrupted file
- Executor: run, resume, dry_run, fallback chain, skip already-completed, skip deps
- Recovery: resolve, evaluate, should_retry, should_escalate, fallback_targets
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

try:
    from src.binh_phap.dag import DagDefinition, ChapterNode
    from src.binh_phap.executor import (
        ExecutionResult,
        ExecutionState,
        Executor,
    )
except ImportError:  # pragma: no cover — modules not yet implemented
    pytest.skip(
        "binh_phap modules (dag, executor, recovery) not yet implemented",
        allow_module_level=True,
    )
from src.binh_phap.recovery import (
    evaluate,
    escalate,
    fallback_targets,
    register,
    should_escalate,
    should_retry,
)


# ---------- fixtures ----------

@pytest.fixture()
def tmp_state(tmp_path: Path) -> Path:
    return tmp_path / "state.json"


@pytest.fixture()
def simple_dag() -> DagDefinition:
    """3-node linear DAG: 1->2->3."""
    chapters = {
        1: ChapterNode(1, "Alpha", "agent-a", ["cmd-a"], "rule-a"),
        2: ChapterNode(2, "Beta",  "agent-b", ["cmd-b"], "rule-b"),
        3: ChapterNode(3, "Gamma", "agent-c", ["cmd-c"], "rule-c"),
    }
    edges = {1: [], 2: [1], 3: [2]}
    return DagDefinition(chapters=chapters, edges=edges, human_only=frozenset())


@pytest.fixture()
def fallback_dag() -> DagDefinition:
    """DAG where ch 8 on timeout → fallback to [1, 7]."""
    ch8 = ChapterNode(8, "Ops", "ops-agent", ["op"], "rule-ops")
    ch7 = ChapterNode(7, "Debug", "dbg-agent", ["dbg"], "rule-debug")
    ch1 = ChapterNode(1, "Init", "init", ["setup"], "rule-init")
    chapters = {8: ch8, 7: ch7, 1: ch1}
    edges = {8: [7, 1], 7: [1], 1: []}
    return DagDefinition(chapters=chapters, edges=edges, human_only=frozenset())


# ---------- ExecutionState ----------

class TestExecutionState:
    def test_no_file_returns_empty(self, tmp_state: Path) -> None:
        st = ExecutionState.load(tmp_state)
        assert st.completed == frozenset()
        assert st.failed == {}
        assert st.results == {}

    def test_round_trip(self, tmp_state: Path) -> None:
        st = ExecutionState(tmp_state)
        st.mark(ExecutionResult(chapter=1, status="success", started_at="t1", finished_at="t2"))
        st.mark(ExecutionResult(chapter=2, status="failed", error="boom", started_at="t3"))
        st.save()
        loaded = ExecutionState.load(tmp_state)
        assert loaded.completed == frozenset({1})
        assert loaded.failed == {2: "boom"}
        assert 1 in loaded.results
        assert loaded.results[1].status == "success"

    def test_corrupted_file_resets(self, tmp_state: Path) -> None:
        tmp_state.write_text("NOT JSON{", encoding="utf-8")
        st = ExecutionState.load(tmp_state)
        assert st.completed == frozenset()
        assert "failed" not in st.__dict__ or st.failed == {}

    def test_updated_at_stamps(self, tmp_state: Path) -> None:
        st = ExecutionState(tmp_state)
        assert st.updated_at is None
        st.mark(ExecutionResult(chapter=1, status="success"))
        assert st.updated_at is not None


# ---------- Executor.run ----------

class TestExecutorRun:
    def test_all_succeed(self, simple_dag: DagDefinition, tmp_path: Path) -> None:
        sp = tmp_path / "s.json"
        ex = Executor(dag=simple_dag, state_path=sp)
        res = ex.run()
        for r in res.values():
            assert r.status in ("success", "skipped")
        assert len(ex.state.completed) == 3

    def test_skip_already_completed(self, simple_dag: DagDefinition, tmp_path: Path) -> None:
        sp = tmp_path / "s.json"
        ex = Executor(dag=simple_dag, state_path=sp)
        ex.run()
        assert len(ex.state.completed) == 3
        ex2 = Executor(dag=simple_dag, state_path=sp)
        captured: list = []
        def spy(self2, ch: int):
            captured.append(ch)
            return ExecutionResult(chapter=ch, status="success")
        with patch.object(Executor, "_execute_chapter", spy):
            ex2.run()
        # Nothing executed — all chapters already done
        assert captured == []

    def test_dry_run(self, simple_dag: DagDefinition, tmp_path: Path) -> None:
        sp = tmp_path / "s.json"
        ex = Executor(dag=simple_dag, state_path=sp, dry_run=True)
        res = ex.run()
        assert all(r.status == "success" for r in res.values())
        assert len(ex.state.completed) == 3

    def test_skip_human_only(self, tmp_path: Path) -> None:
        ch6 = ChapterNode(6, "About", "human", ["ref"], "rule")
        chapters = {1: ChapterNode(1, "A", "a", ["x"], "r"), 6: ch6}
        edges = {1: [], 6: [1]}
        dag = DagDefinition(chapters=chapters, edges=edges, human_only=frozenset({6}))
        sp = tmp_path / "s.json"
        ex = Executor(dag=dag, state_path=sp)
        ex.run()
        # Ch 6 must be present but not marked success (no fetch needed; exec skips)
        assert 1 in ex.state.completed
        assert 6 not in ex.state.completed
        assert 6 in ex.state.results
        assert ex.state.results[6].status == "skipped"

    def test_resume(self, simple_dag: DagDefinition, tmp_path: Path) -> None:
        sp = tmp_path / "s.json"
        ex = Executor(dag=simple_dag, state_path=sp)
        # Pretend ch1 already done
        ex.state.mark(ExecutionResult(chapter=1, status="success"))
        ex.state.save()
        ex2 = Executor(dag=simple_dag, state_path=sp)
        ex2.run()
        # Only 2 and 3 should have run
        assert 1 in ex2.state.completed
        assert all(ex2.state.results[c].status == "success" for c in [2, 3])


# ---------- Executor.fallback ----------

class TestExecutorFallback:
    def test_fallback_chain(self, fallback_dag: DagDefinition, tmp_path: Path) -> None:
        """Ch 8 fails → activator runs fallbacks 1 then 7."""
        sp = tmp_path / "s.json"
        ex = Executor(dag=fallback_dag, state_path=sp)

        calls: list[int] = []

        def fake(self2, ch: int) -> ExecutionResult:
            calls.append(ch)
            # Ch8 always fails; ch1 and ch7 succeed
            if ch == 8:
                return ExecutionResult(chapter=ch, status="failed", error="timeout")
            return ExecutionResult(chapter=ch, status="success")

        with patch.object(Executor, "_execute_chapter", fake):
            ex.run()
        # 8 fails → fallback 1 then fallback 7
        assert 8 in calls
        assert 1 in calls
        assert 7 in calls


# ---------- Recovery ----------

class TestRecovery:
    def setup_method(self) -> None:
        # Reset registry for each test
        from src.binh_phap import recovery as rec
        rec._STRATEGIES.clear()  # pylint: disable=protected-access
        # Order: specific chapter strategies first, then global, then true default last
        register("ch8:timeout", rec.RecoveryStrategy(
            failure_pattern="timeout", max_attempts=2, action="fallback",
            fallback_chapters=[1, 7], human_ok=False
        ))
        register("default:auth", rec.RecoveryStrategy(
            failure_pattern="auth|quota|forbidden", max_attempts=1, action="escalate", human_ok=True
        ))
        retry_default = rec.RecoveryStrategy(
            failure_pattern="", max_attempts=3, action="retry", human_ok=False
        )
        register("default", retry_default)
        register("default:retry", retry_default)

    def test_retry(self) -> None:
        assert should_retry(1, 0, "network timeout") is True
        assert should_retry(1, 3, "network timeout") is False

    def test_escalate_auth(self) -> None:
        assert should_escalate(1, 0, "auth token expired") is True
        assert should_escalate(1, 0, "plain error") is False

    def test_fallback_timeout(self) -> None:
        assert fallback_targets(8, 1, "timeout") == [1, 7]
        assert fallback_targets(8, 1, "plain") == []

    def test_evaluate(self) -> None:
        d = evaluate(8, 1, "timeout on fetch")
        assert d.action == "fallback"
        assert d.fallback_chapters == [1, 7]
        assert d.next_attempts == 1  # max=2, attempt=1

    def test_default_abort(self) -> None:
        from src.binh_phap import recovery as rec
        # Override the shared "default:retry" from setup_method with abort for this test
        rec.register("default", rec.RecoveryStrategy(
            failure_pattern="", max_attempts=3, action="abort", human_ok=False,
        ))
        d = evaluate(99, 99, "unrecognized")
        assert d.action == "abort"

    def test_escalate_logs(self, caplog: pytest.LogCaptureFixture) -> None:  # type: ignore[name-defined]
        import logging
        caplog.set_level(logging.ERROR)
        escalate(5, "quota exhausted")
        assert any("ESCALATE" in r.message for r in caplog.records)

"""Unit tests for src/core/agent_process_lifecycle_manager.py."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager(max_concurrent: int = 5) -> "ProcessManager":
    from src.core.agent_process_lifecycle_manager import ProcessManager
    mock_bus = MagicMock()
    return ProcessManager(max_concurrent=max_concurrent, event_bus=mock_bus)


# ---------------------------------------------------------------------------
# ProcessState enum
# ---------------------------------------------------------------------------

class TestProcessState:
    def test_values_are_strings(self):
        from src.core.agent_process_lifecycle_manager import ProcessState
        assert ProcessState.IDLE == "idle"
        assert ProcessState.RUNNING == "running"
        assert ProcessState.CRASHED == "crashed"

    def test_all_states_present(self):
        from src.core.agent_process_lifecycle_manager import ProcessState
        states = {s.value for s in ProcessState}
        assert {"idle", "spawning", "running", "stopping", "crashed"}.issubset(states)


# ---------------------------------------------------------------------------
# AgentProcess dataclass
# ---------------------------------------------------------------------------

class TestAgentProcess:
    def test_defaults_set(self):
        from src.core.agent_process_lifecycle_manager import AgentProcess, ProcessState
        proc = AgentProcess(agent_id="abc", agent_type="worker", state=ProcessState.IDLE)
        assert proc.pid is None
        assert proc.metadata == {}
        assert proc.started_at > 0

    def test_metadata_not_shared_across_instances(self):
        from src.core.agent_process_lifecycle_manager import AgentProcess, ProcessState
        p1 = AgentProcess("id1", "type", ProcessState.IDLE)
        p2 = AgentProcess("id2", "type", ProcessState.IDLE)
        p1.metadata["key"] = "val"
        assert "key" not in p2.metadata


# ---------------------------------------------------------------------------
# ProcessManager.spawn
# ---------------------------------------------------------------------------

class TestSpawn:
    def test_spawn_returns_running_process(self):
        from src.core.agent_process_lifecycle_manager import ProcessState
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        assert proc.state == ProcessState.RUNNING
        assert proc.agent_type == "worker"

    def test_spawn_assigns_unique_id(self):
        mgr = _make_manager()
        p1 = mgr.spawn("worker")
        p2 = mgr.spawn("worker")
        assert p1.agent_id != p2.agent_id

    def test_spawn_registers_process(self):
        mgr = _make_manager()
        proc = mgr.spawn("coder")
        assert mgr.get_process(proc.agent_id) is proc

    def test_spawn_emits_job_started_event(self):
        from src.core.agent_process_lifecycle_manager import ProcessManager
        from src.core.event_bus import EventType
        mock_bus = MagicMock()
        mgr = ProcessManager(event_bus=mock_bus)
        proc = mgr.spawn("worker")
        mock_bus.emit.assert_called_with(
            EventType.JOB_STARTED,
            {"agent_id": proc.agent_id, "agent_type": "worker"},
        )

    def test_spawn_with_config_stored(self):
        mgr = _make_manager()
        cfg = {"goal": "build auth"}
        proc = mgr.spawn("coder", config=cfg)
        assert mgr._spawn_configs[proc.agent_id] == cfg

    def test_spawn_config_stored_correctly(self):
        """spawn stores config in _spawn_configs keyed by agent_id."""
        mgr = _make_manager()
        cfg = {"goal": "test", "tier": "fast"}
        proc = mgr.spawn("worker", config=cfg)
        stored = mgr._spawn_configs[proc.agent_id]
        assert stored["goal"] == "test"
        assert stored["tier"] == "fast"

    def test_spawn_raises_when_at_capacity(self):
        mgr = _make_manager(max_concurrent=2)
        mgr.spawn("w1")
        mgr.spawn("w2")
        with pytest.raises(RuntimeError, match="Max concurrent"):
            mgr.spawn("w3")

    def test_spawn_allowed_exactly_at_capacity(self):
        mgr = _make_manager(max_concurrent=3)
        mgr.spawn("a")
        mgr.spawn("b")
        proc = mgr.spawn("c")  # should not raise
        assert proc is not None


# ---------------------------------------------------------------------------
# ProcessManager.kill
# ---------------------------------------------------------------------------

class TestKill:
    def test_kill_returns_true_for_known_agent(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        assert mgr.kill(proc.agent_id) is True

    def test_kill_returns_false_for_unknown_agent(self):
        mgr = _make_manager()
        assert mgr.kill("nonexistent") is False

    def test_kill_removes_process_from_registry(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        mgr.kill(proc.agent_id)
        assert mgr.get_process(proc.agent_id) is None

    def test_kill_emits_job_completed_event(self):
        from src.core.agent_process_lifecycle_manager import ProcessManager
        from src.core.event_bus import EventType
        mock_bus = MagicMock()
        mgr = ProcessManager(event_bus=mock_bus)
        proc = mgr.spawn("worker")
        mock_bus.reset_mock()
        mgr.kill(proc.agent_id)
        args = mock_bus.emit.call_args[0]
        assert args[0] == EventType.JOB_COMPLETED
        assert args[1]["agent_id"] == proc.agent_id

    def test_kill_reduces_running_count(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        assert mgr.running_count == 1
        mgr.kill(proc.agent_id)
        assert mgr.running_count == 0

    def test_kill_clears_crash_callbacks(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        mgr.on_crash(proc.agent_id, lambda aid: None)
        mgr.kill(proc.agent_id)
        assert proc.agent_id not in mgr._crash_callbacks


# ---------------------------------------------------------------------------
# ProcessManager.get_process / list_processes
# ---------------------------------------------------------------------------

class TestGetAndList:
    def test_get_process_returns_none_for_unknown(self):
        mgr = _make_manager()
        assert mgr.get_process("unknown") is None

    def test_list_processes_empty_initially(self):
        mgr = _make_manager()
        assert mgr.list_processes() == []

    def test_list_processes_contains_spawned(self):
        mgr = _make_manager()
        p1 = mgr.spawn("w1")
        p2 = mgr.spawn("w2")
        procs = mgr.list_processes()
        assert p1 in procs
        assert p2 in procs

    def test_list_processes_returns_copy(self):
        mgr = _make_manager()
        mgr.spawn("worker")
        lst = mgr.list_processes()
        lst.clear()
        assert len(mgr.list_processes()) == 1


# ---------------------------------------------------------------------------
# ProcessManager.on_crash / report_crash
# ---------------------------------------------------------------------------

class TestCrashHandling:
    def test_report_crash_marks_state_as_crashed(self):
        from src.core.agent_process_lifecycle_manager import ProcessState
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        mgr.report_crash(proc.agent_id)
        assert proc.state == ProcessState.CRASHED

    def test_report_crash_invokes_callbacks(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        cb = MagicMock()
        mgr.on_crash(proc.agent_id, cb)
        mgr.report_crash(proc.agent_id)
        cb.assert_called_once_with(proc.agent_id)

    def test_report_crash_invokes_multiple_callbacks(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        cb1, cb2 = MagicMock(), MagicMock()
        mgr.on_crash(proc.agent_id, cb1)
        mgr.on_crash(proc.agent_id, cb2)
        mgr.report_crash(proc.agent_id)
        cb1.assert_called_once()
        cb2.assert_called_once()

    def test_report_crash_emits_health_warning(self):
        from src.core.agent_process_lifecycle_manager import ProcessManager
        from src.core.event_bus import EventType
        mock_bus = MagicMock()
        mgr = ProcessManager(event_bus=mock_bus)
        proc = mgr.spawn("worker")
        mock_bus.reset_mock()
        mgr.report_crash(proc.agent_id)
        args = mock_bus.emit.call_args[0]
        assert args[0] == EventType.HEALTH_WARNING

    def test_report_crash_on_unknown_agent_is_noop(self):
        mgr = _make_manager()
        mgr.report_crash("nonexistent")  # should not raise

    def test_crashing_callback_exception_doesnt_propagate(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")

        def bad_cb(aid):
            raise RuntimeError("callback failure")

        mgr.on_crash(proc.agent_id, bad_cb)
        # Should not raise
        mgr.report_crash(proc.agent_id)

    def test_subsequent_callbacks_called_after_failing_one(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        good_cb = MagicMock()

        mgr.on_crash(proc.agent_id, lambda aid: (_ for _ in ()).throw(RuntimeError("boom")))
        mgr.on_crash(proc.agent_id, good_cb)
        mgr.report_crash(proc.agent_id)
        good_cb.assert_called_once()


# ---------------------------------------------------------------------------
# ProcessManager.restart
# ---------------------------------------------------------------------------

class TestRestart:
    def test_restart_returns_new_process(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        new_proc = mgr.restart(proc.agent_id)
        assert new_proc.agent_id != proc.agent_id
        assert new_proc.agent_type == "worker"

    def test_restart_removes_old_process(self):
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        old_id = proc.agent_id
        mgr.restart(proc.agent_id)
        assert mgr.get_process(old_id) is None

    def test_restart_preserves_original_config(self):
        mgr = _make_manager()
        cfg = {"model": "fast"}
        proc = mgr.spawn("worker", config=cfg)
        new_proc = mgr.restart(proc.agent_id)
        assert mgr._spawn_configs[new_proc.agent_id] == cfg

    def test_restart_unknown_agent_raises_key_error(self):
        mgr = _make_manager()
        with pytest.raises(KeyError, match="Unknown agent_id"):
            mgr.restart("nonexistent_id")

    def test_restart_new_process_is_running(self):
        from src.core.agent_process_lifecycle_manager import ProcessState
        mgr = _make_manager()
        proc = mgr.spawn("worker")
        new_proc = mgr.restart(proc.agent_id)
        assert new_proc.state == ProcessState.RUNNING


# ---------------------------------------------------------------------------
# running_count / capacity_available
# ---------------------------------------------------------------------------

class TestCapacity:
    def test_running_count_zero_initially(self):
        mgr = _make_manager()
        assert mgr.running_count == 0

    def test_running_count_increments_on_spawn(self):
        mgr = _make_manager()
        mgr.spawn("w1")
        assert mgr.running_count == 1
        mgr.spawn("w2")
        assert mgr.running_count == 2

    def test_capacity_available_true_initially(self):
        mgr = _make_manager(max_concurrent=3)
        assert mgr.capacity_available is True

    def test_capacity_available_false_when_full(self):
        mgr = _make_manager(max_concurrent=2)
        mgr.spawn("w1")
        mgr.spawn("w2")
        assert mgr.capacity_available is False

    def test_capacity_restored_after_kill(self):
        mgr = _make_manager(max_concurrent=1)
        proc = mgr.spawn("worker")
        assert mgr.capacity_available is False
        mgr.kill(proc.agent_id)
        assert mgr.capacity_available is True

    def test_crashed_process_still_counts_as_not_running(self):
        mgr = _make_manager(max_concurrent=2)
        proc = mgr.spawn("worker")
        mgr.report_crash(proc.agent_id)
        # CRASHED != RUNNING, so running_count should be 0
        assert mgr.running_count == 0


# ---------------------------------------------------------------------------
# get_process_manager singleton
# ---------------------------------------------------------------------------

class TestGetProcessManager:
    def test_returns_same_instance(self):
        import src.core.agent_process_lifecycle_manager as mod
        original = mod._default_manager
        mod._default_manager = None
        try:
            m1 = mod.get_process_manager()
            m2 = mod.get_process_manager()
            assert m1 is m2
        finally:
            mod._default_manager = original

    def test_returns_process_manager_instance(self):
        from src.core.agent_process_lifecycle_manager import ProcessManager, get_process_manager
        import src.core.agent_process_lifecycle_manager as mod
        original = mod._default_manager
        mod._default_manager = None
        try:
            mgr = get_process_manager()
            assert isinstance(mgr, ProcessManager)
        finally:
            mod._default_manager = original

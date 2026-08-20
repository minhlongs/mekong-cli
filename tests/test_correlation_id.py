"""Tests for mission correlation ID in MekongCoreRuntimeImpl."""

import unittest

from src.core.memory_separation import MemoryTier
from src.core.mission_tracer import MissionTracer
from src.core.runtime_adapter import MekongCoreRuntimeImpl


class _FakeDispatcher:
    def dispatch(self, task, agent=None):
        return {"ok": True, "task_id": task.id}


class _FakeToolRegistry:
    def register(self, tool, **kwargs):
        pass

    def execute(self, tool_id, params):
        return {"ok": True}

    def list_tools(self):
        return []


class TestRuntimeMissionTracking(unittest.TestCase):
    """Test mission tracking fields on MekongCoreRuntimeImpl."""

    def _make_runtime(self, **kwargs):
        defaults = dict(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        defaults.update(kwargs)
        return MekongCoreRuntimeImpl(**defaults)

    def test_start_mission_sets_mission_id(self):
        """start_mission assigns a mission_id string."""
        runtime = self._make_runtime()
        mid = runtime.start_mission("deploy api")
        assert isinstance(mid, str)
        assert mid.startswith("mission_")
        assert runtime._mission_id == mid

    def test_start_mission_with_tracer(self):
        """start_mission delegates to tracer when provided."""
        tracer = MissionTracer()
        runtime = self._make_runtime()
        runtime.start_mission("build", tracer=tracer)
        missions = tracer.list_missions()
        assert len(missions) == 1
        assert missions[0]["goal"] == "build"

    def test_mission_id_defaults_to_none(self):
        """_mission_id is None before start_mission is called."""
        runtime = self._make_runtime()
        assert runtime._mission_id is None

    def test_mission_tracer_defaults_to_none(self):
        """_mission_tracer is None when no tracer is provided."""
        runtime = self._make_runtime()
        assert runtime._mission_tracer is None

    def test_start_mission_without_tracer(self):
        """start_mission works without a tracer, only sets _mission_id."""
        runtime = self._make_runtime()
        mid = runtime.start_mission("simple task")
        assert runtime._mission_id == mid
        assert runtime._mission_tracer is None

    def test_destroy_clears_mission_fields(self):
        """destroy clears mission tracking fields."""
        tracer = MissionTracer()
        runtime = self._make_runtime()
        runtime.start_mission("task", tracer=tracer)
        assert runtime._mission_id is not None
        assert runtime._mission_tracer is not None
        runtime.destroy()
        assert runtime._mission_id is None
        assert runtime._mission_tracer is None

    def test_multiple_missions_update_id(self):
        """Each start_mission call overwrites the previous mission_id."""
        runtime = self._make_runtime()
        mid1 = runtime.start_mission("first")
        mid2 = runtime.start_mission("second")
        assert mid1 != mid2
        assert runtime._mission_id == mid2


class TestRuntimeMemoryTierSeparation(unittest.TestCase):
    """Memory tier separation wired into the runtime lifecycle."""

    def _make_runtime(self, **kwargs):
        defaults = dict(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        defaults.update(kwargs)
        return MekongCoreRuntimeImpl(**defaults)

    def test_runtime_uses_memory_separation_by_default(self):
        """MekongCoreRuntimeImpl defaults to MemorySeparation backend."""
        from src.core.memory_separation import MemorySeparation

        runtime = self._make_runtime()
        assert isinstance(runtime._memory_separation, MemorySeparation)

    def test_remember_stores_in_session_tier(self):
        """remember() writes to SESSION tier so the next mission can flush it."""
        from src.core.runtime_adapter import Task, AgentId, Step

        runtime = self._make_runtime()
        runtime.start_mission("task")
        task = Task(
            id="t1",
            step=Step(id="step-0", description="do thing", params={}),
            agent=AgentId(name="default"),
        )
        result = runtime.execute(task)
        obs = runtime.observe(result)
        runtime.remember(obs)
        session_keys = runtime._memory_separation.list_by_tier(MemoryTier.SESSION)
        assert len(session_keys) == 1
        assert "obs-t1" in session_keys

    def test_start_mission_flushes_prior_session_memory(self):
        """Each start_mission clears SESSION-tier entries from the prior run."""
        runtime = self._make_runtime()
        runtime.start_mission("first")
        # Simulate a session entry left over from the prior mission.
        runtime._memory_separation.store("leftover", b"data", tier=MemoryTier.SESSION)
        assert len(runtime._memory_separation.list_by_tier(MemoryTier.SESSION)) == 1
        runtime.start_mission("second")
        assert runtime._memory_separation.list_by_tier(MemoryTier.SESSION) == []

    def test_flush_session_returns_count(self):
        """flush_session() returns the number of SESSION entries deleted."""
        runtime = self._make_runtime()
        runtime._memory_separation.store("s1", b"a", tier=MemoryTier.SESSION)
        runtime._memory_separation.store("s2", b"b", tier=MemoryTier.SESSION)
        runtime._memory_separation.store("p1", b"c", tier=MemoryTier.PERSISTENT)
        deleted = runtime.flush_session()
        assert deleted == 2
        assert runtime._memory_separation.list_by_tier(MemoryTier.SESSION) == []
        assert runtime._memory_separation.list_by_tier(MemoryTier.PERSISTENT) == ["p1"]

    def test_destroy_clears_memory_separation(self):
        """destroy() releases the memory separation layer."""
        runtime = self._make_runtime()
        runtime.start_mission("task")
        assert runtime._memory_separation is not None
        runtime.destroy()
        assert runtime._memory_separation is None


if __name__ == "__main__":
    unittest.main()

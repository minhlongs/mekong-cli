"""Tests for mission correlation ID in MekongCoreRuntimeImpl."""

import unittest

from src.core.mission_tracer import MissionTracer
from src.core.runtime_adapter import MekongCoreRuntimeImpl


class _FakeDispatcher:
    def dispatch(self, task):
        return None


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


if __name__ == "__main__":
    unittest.main()

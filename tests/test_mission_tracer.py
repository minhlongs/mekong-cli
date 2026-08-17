"""Tests for mission-level trace correlation."""

import unittest

from src.core.mission_tracer import MissionRecord, MissionTracer


class TestMissionRecord(unittest.TestCase):
    """Verify MissionRecord dataclass defaults."""

    def test_defaults(self):
        rec = MissionRecord(mission_id="m1", goal="deploy")
        assert rec.mission_id == "m1"
        assert rec.goal == "deploy"
        assert rec.status == "running"
        assert rec.steps == []
        assert rec.completed_at is None
        assert rec.created_at is not None

    def test_with_metadata(self):
        rec = MissionRecord(
            mission_id="m2",
            goal="test",
            metadata={"source": "unit_test"},
        )
        assert rec.metadata["source"] == "unit_test"


class TestMissionTracer(unittest.TestCase):
    """Test MissionTracer lifecycle operations."""

    def setUp(self):
        self.tracer = MissionTracer()

    def test_start_mission_returns_id(self):
        """start_mission returns a string mission_id."""
        mid = self.tracer.start_mission("build project")
        assert isinstance(mid, str)
        assert mid.startswith("mission_")

    def test_log_step_appends_to_mission(self):
        """log_step appends a step entry to the mission."""
        mid = self.tracer.start_mission("deploy")
        self.tracer.log_step(mid, "run tests", {"passed": True})
        record = self.tracer.get_mission(mid)
        assert record is not None
        assert len(record.steps) == 1
        assert record.steps[0]["step"] == "run tests"
        assert record.steps[0]["result"]["passed"] is True

    def test_log_step_unknown_mission_ignored(self):
        """log_step for unknown mission_id is silently ignored."""
        self.tracer.log_step("mission_unknown", "step", {})
        # No exception raised

    def test_end_mission_sets_status(self):
        """end_mission updates status and sets completed_at."""
        mid = self.tracer.start_mission("optimize")
        summary = self.tracer.end_mission(mid, "success")
        assert summary is not None
        assert summary["status"] == "success"
        assert summary["completed_at"] is not None

    def test_end_mission_returns_summary(self):
        """end_mission returns a summary dict with expected fields."""
        mid = self.tracer.start_mission("deploy api")
        self.tracer.log_step(mid, "compile", {"ok": True})
        summary = self.tracer.end_mission(mid, "success")
        assert summary is not None
        assert summary["mission_id"] == mid
        assert summary["goal"] == "deploy api"
        assert summary["step_count"] == 1
        assert summary["created_at"] is not None

    def test_end_mission_unknown_returns_none(self):
        """end_mission returns None for unknown mission_id."""
        assert self.tracer.end_mission("mission_ghost", "fail") is None

    def test_get_mission_returns_record(self):
        """get_mission returns MissionRecord for valid ID."""
        mid = self.tracer.start_mission("task")
        record = self.tracer.get_mission(mid)
        assert isinstance(record, MissionRecord)
        assert record.mission_id == mid

    def test_get_mission_unknown_returns_none(self):
        """get_mission returns None for unknown ID."""
        assert self.tracer.get_mission("mission_nope") is None

    def test_list_missions_returns_all(self):
        """list_missions returns summary for every started mission."""
        self.tracer.start_mission("m1")
        self.tracer.start_mission("m2")
        self.tracer.start_mission("m3")
        missions = self.tracer.list_missions()
        assert len(missions) == 3
        goals = {m["goal"] for m in missions}
        assert goals == {"m1", "m2", "m3"}

    def test_list_missions_step_count(self):
        """list_missions reflects step count correctly."""
        mid = self.tracer.start_mission("complex")
        for i in range(4):
            self.tracer.log_step(mid, f"step-{i}", {"idx": i})
        missions = self.tracer.list_missions()
        assert len(missions) == 1
        assert missions[0]["step_count"] == 4

    def test_mission_record_independent(self):
        """Each mission gets its own isolated record."""
        mid1 = self.tracer.start_mission("task-1")
        mid2 = self.tracer.start_mission("task-2")
        self.tracer.log_step(mid1, "step-1", {})
        assert len(self.tracer.get_mission(mid1).steps) == 1
        assert len(self.tracer.get_mission(mid2).steps) == 0


if __name__ == "__main__":
    unittest.main()

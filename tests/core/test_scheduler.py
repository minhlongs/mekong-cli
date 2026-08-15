"""Tests for src/core/scheduler.py."""

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.scheduler import Scheduler, ScheduledJob


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scheduler(tmp_path) -> Scheduler:
    """Return a Scheduler that writes to a tmp file, not loading anything."""
    config = str(tmp_path / "schedule.yaml")
    return Scheduler(config_path=config)


# ---------------------------------------------------------------------------
# ScheduledJob dataclass
# ---------------------------------------------------------------------------

class TestScheduledJob:
    def test_default_values(self):
        job = ScheduledJob(
            id="abc",
            name="test",
            goal="do something",
            job_type="interval",
        )
        assert job.enabled is True
        assert job.last_run == 0.0
        assert job.run_count == 0
        assert job.interval_seconds == 0
        assert job.daily_time == ""
        assert job.next_run == 0.0


# ---------------------------------------------------------------------------
# Scheduler initialisation
# ---------------------------------------------------------------------------

class TestSchedulerInit:
    def test_starts_empty_when_no_config_file(self, tmp_path):
        s = _scheduler(tmp_path)
        assert s.job_count == 0

    def test_is_not_running_on_init(self, tmp_path):
        s = _scheduler(tmp_path)
        assert s.is_running is False

    def test_custom_config_path_respected(self, tmp_path):
        config = str(tmp_path / "custom.yaml")
        s = Scheduler(config_path=config)
        assert s._config_path == config


# ---------------------------------------------------------------------------
# add_job
# ---------------------------------------------------------------------------

class TestAddJob:
    def test_add_interval_job(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("backup", "run backup", job_type="interval", interval_seconds=60)
        assert job.name == "backup"
        assert job.goal == "run backup"
        assert job.job_type == "interval"
        assert s.job_count == 1

    def test_add_daily_job(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("daily-report", "generate report", job_type="daily", daily_time="08:00")
        assert job.job_type == "daily"
        assert job.daily_time == "08:00"
        assert job.next_run > time.time()  # should be in the future

    def test_interval_next_run_is_in_future(self, tmp_path):
        s = _scheduler(tmp_path)
        before = time.time()
        job = s.add_job("x", "goal", interval_seconds=300)
        assert job.next_run >= before + 300

    def test_add_multiple_jobs_have_unique_ids(self, tmp_path):
        s = _scheduler(tmp_path)
        j1 = s.add_job("a", "goal a")
        j2 = s.add_job("b", "goal b")
        assert j1.id != j2.id

    def test_add_job_persists_to_file(self, tmp_path):
        s = _scheduler(tmp_path)
        s.add_job("persist", "check persistence")
        config = Path(s._config_path)
        assert config.exists()
        content = config.read_text()
        assert "persist" in content


# ---------------------------------------------------------------------------
# remove_job
# ---------------------------------------------------------------------------

class TestRemoveJob:
    def test_remove_existing_job_returns_true(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("to_remove", "goal")
        result = s.remove_job(job.id)
        assert result is True
        assert s.job_count == 0

    def test_remove_nonexistent_job_returns_false(self, tmp_path):
        s = _scheduler(tmp_path)
        result = s.remove_job("nonexistent_id")
        assert result is False

    def test_remove_updates_file(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("temp_job", "goal")
        s.remove_job(job.id)
        content = Path(s._config_path).read_text()
        assert "temp_job" not in content


# ---------------------------------------------------------------------------
# list_jobs / get_job
# ---------------------------------------------------------------------------

class TestListAndGetJobs:
    def test_list_jobs_empty(self, tmp_path):
        s = _scheduler(tmp_path)
        assert s.list_jobs() == []

    def test_list_jobs_returns_all(self, tmp_path):
        s = _scheduler(tmp_path)
        s.add_job("a", "goal a")
        s.add_job("b", "goal b")
        jobs = s.list_jobs()
        assert len(jobs) == 2

    def test_get_job_by_id(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("findme", "my goal")
        found = s.get_job(job.id)
        assert found is job

    def test_get_job_returns_none_for_unknown(self, tmp_path):
        s = _scheduler(tmp_path)
        assert s.get_job("does_not_exist") is None


# ---------------------------------------------------------------------------
# get_due_jobs
# ---------------------------------------------------------------------------

class TestGetDueJobs:
    def test_no_due_jobs_when_fresh(self, tmp_path):
        s = _scheduler(tmp_path)
        s.add_job("future_job", "goal", interval_seconds=9999)
        assert s.get_due_jobs() == []

    def test_due_job_returned(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("past_job", "goal", interval_seconds=0)
        job.next_run = time.time() - 1  # force it into the past
        due = s.get_due_jobs()
        assert job in due

    def test_disabled_job_not_returned(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("disabled", "goal")
        job.next_run = time.time() - 1
        job.enabled = False
        assert s.get_due_jobs() == []


# ---------------------------------------------------------------------------
# mark_completed
# ---------------------------------------------------------------------------

class TestMarkCompleted:
    def test_increments_run_count(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("counting", "goal")
        job.next_run = time.time() - 1
        assert job.run_count == 0
        s.mark_completed(job)
        assert job.run_count == 1

    def test_updates_last_run(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("timing", "goal")
        before = time.time()
        s.mark_completed(job)
        assert job.last_run >= before

    def test_interval_job_next_run_pushed_forward(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("interval_fwd", "goal", interval_seconds=120)
        before = time.time()
        s.mark_completed(job)
        assert job.next_run >= before + 120

    def test_daily_job_next_run_is_in_future(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("daily_fwd", "goal", job_type="daily", daily_time="23:59")
        job.next_run = time.time() - 1
        s.mark_completed(job)
        assert job.next_run > time.time()


# ---------------------------------------------------------------------------
# set_run_callback / is_running / stop
# ---------------------------------------------------------------------------

class TestCallbackAndRunState:
    def test_set_run_callback(self, tmp_path):
        s = _scheduler(tmp_path)
        cb = MagicMock(return_value={"status": "ok"})
        s.set_run_callback(cb)
        assert s._run_callback is cb

    def test_stop_sets_running_false(self, tmp_path):
        s = _scheduler(tmp_path)
        s._running = True
        s.stop()
        assert s.is_running is False


# ---------------------------------------------------------------------------
# tick (async)
# ---------------------------------------------------------------------------

class TestTick:
    def test_tick_no_due_jobs_returns_empty(self, tmp_path):
        s = _scheduler(tmp_path)
        s.add_job("future", "goal", interval_seconds=9999)

        results = asyncio.run(s.tick())
        assert results == []

    def test_tick_executes_due_job_with_callback(self, tmp_path):
        s = _scheduler(tmp_path)
        cb = MagicMock(return_value={"status": "done"})
        s.set_run_callback(cb)

        job = s.add_job("due_now", "goal", interval_seconds=0)
        job.next_run = time.time() - 1

        with patch("src.core.scheduler.get_event_bus") as mock_bus:
            mock_bus.return_value = MagicMock()
            results = asyncio.run(s.tick())

        assert len(results) == 1
        assert results[0]["status"] == "done"
        cb.assert_called_once_with("goal")

    def test_tick_skipped_when_no_callback(self, tmp_path):
        s = _scheduler(tmp_path)
        job = s.add_job("no_cb_job", "goal", interval_seconds=0)
        job.next_run = time.time() - 1

        with patch("src.core.scheduler.get_event_bus") as mock_bus:
            mock_bus.return_value = MagicMock()
            results = asyncio.run(s.tick())

        assert results[0]["status"] == "skipped"

    def test_tick_handles_callback_exception(self, tmp_path):
        s = _scheduler(tmp_path)
        cb = MagicMock(side_effect=RuntimeError("boom"))
        s.set_run_callback(cb)

        job = s.add_job("boom_job", "goal", interval_seconds=0)
        job.next_run = time.time() - 1

        with patch("src.core.scheduler.get_event_bus") as mock_bus:
            mock_bus.return_value = MagicMock()
            results = asyncio.run(s.tick())

        assert results[0]["status"] == "error"
        assert "boom" in results[0]["error"]

    def test_tick_emits_job_started_and_completed_events(self, tmp_path):
        s = _scheduler(tmp_path)
        s.set_run_callback(MagicMock(return_value={"status": "ok"}))
        job = s.add_job("evt_job", "goal", interval_seconds=0)
        job.next_run = time.time() - 1

        mock_bus = MagicMock()
        emitted_events = []
        mock_bus.emit.side_effect = lambda etype, data: emitted_events.append(etype)

        from src.core.event_bus import EventType

        with (
            patch("src.core.scheduler.get_event_bus", return_value=mock_bus),
            patch("src.core.scheduler.EventType", EventType),
        ):
            asyncio.run(s.tick())

        assert EventType.JOB_STARTED in emitted_events
        assert EventType.JOB_COMPLETED in emitted_events


# ---------------------------------------------------------------------------
# _next_daily_run (static method)
# ---------------------------------------------------------------------------

class TestNextDailyRun:
    def test_returns_future_timestamp(self):
        future = Scheduler._next_daily_run("23:59")
        assert future > time.time()

    def test_invalid_time_falls_back_to_9am(self):
        future = Scheduler._next_daily_run("INVALID")
        # Should not raise; result should be after now
        assert future > time.time()

    def test_past_time_scheduled_tomorrow(self):
        # "00:01" is almost always in the past today, so should push to tomorrow
        now = datetime.now()
        past_time = "00:01"
        ts = Scheduler._next_daily_run(past_time)
        dt = datetime.fromtimestamp(ts)
        # Result should be within the next 25 hours
        assert dt > now
        assert dt < now + timedelta(hours=25)


# ---------------------------------------------------------------------------
# _save / _load (persistence round-trip)
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_save_and_reload_preserves_jobs(self, tmp_path):
        pytest.importorskip("yaml")

        s1 = _scheduler(tmp_path)
        j = s1.add_job("persist_me", "save and reload goal", interval_seconds=42)
        original_id = j.id

        s2 = _scheduler(tmp_path)
        assert s2.job_count == 1
        reloaded = s2.get_job(original_id)
        assert reloaded is not None
        assert reloaded.name == "persist_me"
        assert reloaded.interval_seconds == 42

    def test_load_ignores_corrupt_yaml(self, tmp_path):
        config = tmp_path / "schedule.yaml"
        config.write_text("jobs:\n  - id: [[[CORRUPT", encoding="utf-8")
        s = Scheduler(config_path=str(config))
        assert s.job_count == 0

    def test_load_skips_entry_without_id(self, tmp_path):
        config = tmp_path / "schedule.yaml"
        config.write_text("jobs:\n  - name: no_id_job\n    goal: x\n    job_type: interval\n    interval_seconds: 10\n    daily_time: '09:00'\n    enabled: true\n    last_run: 0.0\n    next_run: 0.0\n    run_count: 0\n", encoding="utf-8")
        pytest.importorskip("yaml")
        s = Scheduler(config_path=str(config))
        # Entry without id should be skipped
        assert s.job_count == 0

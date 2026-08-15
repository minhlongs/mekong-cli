"""
Tests for daemon health monitoring: LearningJournal, HeartbeatScheduler,
WorkerPool.health_check, and overall health observability.

Covers:
- Journal write/read/success-rate
- Heartbeat parsing from HEARTBEAT.md
- Cron expression parsing
- is_due scheduling logic
- Loop file discovery
- Worker health categorization
- Alert writing on failure
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

from src.daemon.journal import LearningJournal
from src.daemon.heartbeat_scheduler import HeartbeatScheduler, ScheduledTask
from src.daemon.worker_pool import WorkerPool, WorkerInfo, WorkerState


# ---------------------------------------------------------------------------
# LearningJournal
# ---------------------------------------------------------------------------

class TestLearningJournal:
    """Journal records missions and computes success rate."""

    def test_record_mission_creates_file(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        journal.record_mission("deploy feature", "medium", success=True, duration=12.5)
        assert (tmp_path / "journal.jsonl").exists()

    def test_record_writes_valid_json(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        journal.record_mission("task", "simple", success=True, duration=1.0)
        lines = (tmp_path / "journal.jsonl").read_text().strip().split("\n")
        data = json.loads(lines[0])
        assert data["mission"] == "task"
        assert data["complexity"] == "simple"
        assert data["success"] is True

    def test_record_mission_with_error(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        journal.record_mission("bad task", "complex", success=False, duration=2.0, error="timeout")
        entries = journal.recent()
        assert entries[0].error == "timeout"
        assert entries[0].success is False

    def test_recent_returns_last_n_entries(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        for i in range(10):
            journal.record_mission(f"task {i}", "simple", success=True, duration=1.0)
        recent = journal.recent(limit=3)
        assert len(recent) == 3
        assert recent[-1].mission == "task 9"

    def test_recent_returns_empty_when_no_file(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "nonexistent.jsonl"))
        assert journal.recent() == []

    def test_success_rate_all_success(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        for _ in range(5):
            journal.record_mission("task", "simple", success=True, duration=1.0)
        assert journal.success_rate() == 1.0

    def test_success_rate_all_failure(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        for _ in range(5):
            journal.record_mission("task", "simple", success=False, duration=1.0)
        assert journal.success_rate() == 0.0

    def test_success_rate_mixed(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        for i in range(4):
            journal.record_mission("task", "simple", success=(i % 2 == 0), duration=1.0)
        rate = journal.success_rate()
        assert rate == 0.5

    def test_success_rate_empty_journal_returns_zero(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        assert journal.success_rate() == 0.0

    def test_record_truncates_long_mission_name(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        long_name = "x" * 500
        journal.record_mission(long_name, "simple", success=True, duration=0.1)
        entries = journal.recent()
        assert len(entries[0].mission) <= 200

    def test_journal_creates_parent_dirs(self, tmp_path):
        deep_path = tmp_path / "deep" / "nested" / "journal.jsonl"
        journal = LearningJournal(journal_path=str(deep_path))
        journal.record_mission("task", "simple", success=True, duration=1.0)
        assert deep_path.exists()

    def test_multiple_records_accumulate(self, tmp_path):
        journal = LearningJournal(journal_path=str(tmp_path / "journal.jsonl"))
        for i in range(5):
            journal.record_mission(f"mission {i}", "simple", success=True, duration=float(i))
        assert len(journal.recent(100)) == 5


# ---------------------------------------------------------------------------
# HeartbeatScheduler — parsing and scheduling
# ---------------------------------------------------------------------------

class TestHeartbeatSchedulerParseCron:
    """Cron expression parsing."""

    def test_every_n_minutes(self):
        interval, hour, weekday = HeartbeatScheduler._parse_cron("*/15 * * * *")
        assert interval == 15
        assert hour is None
        assert weekday is None

    def test_daily_at_fixed_hour(self):
        interval, hour, weekday = HeartbeatScheduler._parse_cron("0 9 * * *")
        assert interval == 1440
        assert hour == 9
        assert weekday is None

    def test_weekly_specific_day(self):
        interval, hour, weekday = HeartbeatScheduler._parse_cron("0 8 * * 1")
        assert hour == 8
        assert weekday == 1

    def test_multiple_days_returns_daily(self):
        interval, hour, weekday = HeartbeatScheduler._parse_cron("0 8 * * 1,3,5")
        assert interval == 1440
        assert hour == 8

    def test_malformed_cron_returns_defaults(self):
        interval, hour, weekday = HeartbeatScheduler._parse_cron("invalid")
        assert interval == 60
        assert hour is None


class TestHeartbeatSchedulerParseMarkdown:
    """HEARTBEAT.md parsing into ScheduledTask list."""

    def _make_scheduler(self, tmp_path):
        return HeartbeatScheduler(project_root=str(tmp_path))

    def test_parse_hourly_tasks(self, tmp_path):
        hb = tmp_path / "HEARTBEAT.md"
        hb.write_text("""## Every 1 Hour\n- [ ] **Check leads** `mekong lead-scan`\n""")
        scheduler = self._make_scheduler(tmp_path)
        tasks = scheduler.parse_heartbeat("root", hb)
        assert len(tasks) == 1
        assert tasks[0].interval_minutes == 60
        assert tasks[0].command == "mekong lead-scan"

    def test_parse_daily_tasks_with_time(self, tmp_path):
        hb = tmp_path / "HEARTBEAT.md"
        hb.write_text("""## Daily at 09:00\n- [ ] **Morning report** `mekong report`\n""")
        scheduler = self._make_scheduler(tmp_path)
        tasks = scheduler.parse_heartbeat("root", hb)
        assert tasks[0].interval_minutes == 1440
        assert tasks[0].cron_hour == 9

    def test_parse_weekly_tasks(self, tmp_path):
        hb = tmp_path / "HEARTBEAT.md"
        hb.write_text("""## Weekly on Monday\n- [ ] **Weekly review** `mekong weekly`\n""")
        scheduler = self._make_scheduler(tmp_path)
        tasks = scheduler.parse_heartbeat("root", hb)
        assert tasks[0].interval_minutes == 10080
        assert tasks[0].cron_weekday == 0  # Monday

    def test_parse_task_without_command_is_tier2(self, tmp_path):
        hb = tmp_path / "HEARTBEAT.md"
        hb.write_text("""## Every 1 Hour\n- [ ] **Think deeply about business**\n""")
        scheduler = self._make_scheduler(tmp_path)
        tasks = scheduler.parse_heartbeat("root", hb)
        assert len(tasks) == 1
        assert tasks[0].tier == 2
        assert tasks[0].command is None

    def test_parse_task_with_command_is_tier1(self, tmp_path):
        hb = tmp_path / "HEARTBEAT.md"
        hb.write_text("""## Hourly\n- [ ] **Build** `npm build`\n""")
        scheduler = self._make_scheduler(tmp_path)
        tasks = scheduler.parse_heartbeat("root", hb)
        assert tasks[0].tier == 1

    def test_parse_30min_section(self, tmp_path):
        hb = tmp_path / "HEARTBEAT.md"
        hb.write_text("""## Every 30 Minutes\n- [ ] **Ping** `echo ping`\n""")
        scheduler = self._make_scheduler(tmp_path)
        tasks = scheduler.parse_heartbeat("root", hb)
        assert tasks[0].interval_minutes == 30

    def test_empty_heartbeat_returns_no_tasks(self, tmp_path):
        hb = tmp_path / "HEARTBEAT.md"
        hb.write_text("# No tasks here\n")
        scheduler = self._make_scheduler(tmp_path)
        tasks = scheduler.parse_heartbeat("root", hb)
        assert tasks == []


class TestHeartbeatSchedulerIsDue:
    """is_due checks interval and time constraints."""

    def _make_scheduler(self, tmp_path):
        return HeartbeatScheduler(project_root=str(tmp_path))

    def test_never_run_task_is_due_when_no_constraints(self, tmp_path):
        scheduler = self._make_scheduler(tmp_path)
        task = ScheduledTask(description="task", interval_minutes=60)
        assert scheduler.is_due(task, datetime.now()) is True

    def test_recently_run_task_is_not_due(self, tmp_path):
        scheduler = self._make_scheduler(tmp_path)
        task = ScheduledTask(description="task", interval_minutes=60, last_run=datetime.now())
        assert scheduler.is_due(task, datetime.now()) is False

    def test_expired_task_is_due(self, tmp_path):
        scheduler = self._make_scheduler(tmp_path)
        task = ScheduledTask(
            description="task",
            interval_minutes=1,
            last_run=datetime.now() - timedelta(minutes=5),
        )
        assert scheduler.is_due(task, datetime.now()) is True

    def test_hour_constraint_blocks_wrong_hour(self, tmp_path):
        scheduler = self._make_scheduler(tmp_path)
        task = ScheduledTask(description="task", interval_minutes=1440, cron_hour=3)
        # Run at wrong hour
        now = datetime.now().replace(hour=14)
        assert scheduler.is_due(task, now) is False

    def test_hour_constraint_passes_correct_hour(self, tmp_path):
        scheduler = self._make_scheduler(tmp_path)
        task = ScheduledTask(description="task", interval_minutes=1440, cron_hour=9)
        now = datetime.now().replace(hour=9)
        assert scheduler.is_due(task, now) is True

    def test_weekday_constraint_blocks_wrong_day(self, tmp_path):
        scheduler = self._make_scheduler(tmp_path)
        task = ScheduledTask(description="task", interval_minutes=10080, cron_weekday=0)  # Monday
        # Find a non-Monday
        now = datetime(2026, 4, 7)  # Tuesday
        assert scheduler.is_due(task, now) is False

    def test_weekday_constraint_passes_correct_day(self, tmp_path):
        scheduler = self._make_scheduler(tmp_path)
        task = ScheduledTask(description="task", interval_minutes=10080, cron_weekday=0)  # Monday
        now = datetime(2026, 4, 6)  # Monday
        assert scheduler.is_due(task, now) is True


class TestHeartbeatSchedulerDiscoverLoops:
    """Loop config file loading from .mekong/loops/."""

    def test_discover_loops_empty_dir(self, tmp_path):
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        loops = scheduler.discover_loops()
        assert loops == []

    def test_discover_loops_loads_json(self, tmp_path):
        loops_dir = tmp_path / ".mekong" / "loops"
        loops_dir.mkdir(parents=True)
        loop_config = {
            "name": "lead-scan",
            "description": "Scan for new leads",
            "enabled": True,
            "schedule": {"cron": "0 9 * * *"},
            "tier1_check": {"command": "mekong lead-scan"},
            "model_tier": "fast",
        }
        (loops_dir / "lead-scan.json").write_text(json.dumps(loop_config))
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        loops = scheduler.discover_loops()
        assert len(loops) == 1
        assert "lead-scan" in loops[0].description

    def test_discover_loops_skips_disabled(self, tmp_path):
        loops_dir = tmp_path / ".mekong" / "loops"
        loops_dir.mkdir(parents=True)
        loop_config = {
            "name": "disabled-loop",
            "description": "Should not load",
            "enabled": False,
            "schedule": {"cron": "*/5 * * * *"},
        }
        (loops_dir / "disabled.json").write_text(json.dumps(loop_config))
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        loops = scheduler.discover_loops()
        assert loops == []

    def test_discover_loops_handles_invalid_json(self, tmp_path):
        loops_dir = tmp_path / ".mekong" / "loops"
        loops_dir.mkdir(parents=True)
        (loops_dir / "bad.json").write_text("NOT JSON{{{")
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        # Should not raise
        loops = scheduler.discover_loops()
        assert loops == []


class TestHeartbeatSchedulerConfig:
    """Heartbeat config loading from heartbeat-config.json."""

    def test_default_config_when_no_file(self, tmp_path):
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        assert scheduler.config.enabled is True
        assert scheduler.config.max_concurrent == 3

    def test_loads_config_from_file(self, tmp_path):
        cfg_dir = tmp_path / ".mekong"
        cfg_dir.mkdir(parents=True)
        cfg = {
            "enabled": True,
            "check_interval": 30,
            "max_concurrent": 5,
            "workspaces": ["ws1", "ws2"],
        }
        (cfg_dir / "heartbeat-config.json").write_text(json.dumps(cfg))
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        assert scheduler.config.check_interval == 30
        assert scheduler.config.max_concurrent == 5


class TestHeartbeatSchedulerDiscoverHeartbeats:
    """HEARTBEAT.md discovery."""

    def test_discovers_root_heartbeat(self, tmp_path):
        (tmp_path / "HEARTBEAT.md").write_text("## Hourly\n- [ ] **task** `cmd`\n")
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        found = scheduler.discover_heartbeats()
        assert any(ws == "root" for ws, _ in found)

    def test_no_heartbeat_returns_empty(self, tmp_path):
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        found = scheduler.discover_heartbeats()
        assert found == []


class TestHeartbeatSchedulerAlert:
    """Alert writing on task failure."""

    def test_alert_writes_to_log_file(self, tmp_path):
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        # Ensure mekong_dir exists so _alert can write the log
        scheduler.mekong_dir.mkdir(parents=True, exist_ok=True)
        task = ScheduledTask(description="failing task", workspace="root")
        scheduler._alert(task, "exit code 1")
        alert_file = tmp_path / ".mekong" / "jidoka-alerts.log"
        assert alert_file.exists()
        content = alert_file.read_text()
        assert "failing task" in content
        assert "exit code 1" in content

    def test_alert_appends_on_multiple_failures(self, tmp_path):
        scheduler = HeartbeatScheduler(project_root=str(tmp_path))
        scheduler.mekong_dir.mkdir(parents=True, exist_ok=True)
        task = ScheduledTask(description="task", workspace="root")
        scheduler._alert(task, "error 1")
        scheduler._alert(task, "error 2")
        alert_file = tmp_path / ".mekong" / "jidoka-alerts.log"
        lines = alert_file.read_text().strip().split("\n")
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# WorkerPool health_check (integrated health view)
# ---------------------------------------------------------------------------

class TestWorkerPoolHealthCheck:
    """Health check categorizes workers correctly."""

    def _add_worker(self, pool, name, state=WorkerState.IDLE, capability="general"):
        from datetime import datetime
        pool.workers[name] = WorkerInfo(
            id=name, name=name, capability=capability,
            state=state, started_at=datetime.now().isoformat(),
        )

    @patch.object(WorkerPool, "refresh_status")
    def test_healthy_includes_idle_and_busy(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "idle-worker", WorkerState.IDLE)
        self._add_worker(pool, "busy-worker", WorkerState.BUSY)
        health = pool.health_check()
        assert "idle-worker" in health["healthy"]
        assert "busy-worker" in health["healthy"]

    @patch.object(WorkerPool, "refresh_status")
    def test_degraded_includes_errored(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "broken", WorkerState.ERRORED)
        health = pool.health_check()
        assert "broken" in health["degraded"]

    @patch.object(WorkerPool, "refresh_status")
    def test_unhealthy_includes_offline(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "offline-worker", WorkerState.OFFLINE)
        health = pool.health_check()
        assert "offline-worker" in health["unhealthy"]

    @patch.object(WorkerPool, "refresh_status")
    def test_empty_pool_all_categories_empty(self, mock_refresh):
        pool = WorkerPool()
        health = pool.health_check()
        assert health["healthy"] == []
        assert health["degraded"] == []
        assert health["unhealthy"] == []

    @patch.object(WorkerPool, "refresh_status")
    def test_health_check_updates_last_check_timestamp(self, mock_refresh):
        pool = WorkerPool()
        before = pool._last_health_check
        pool.health_check()
        assert pool._last_health_check > before

    @patch.object(WorkerPool, "refresh_status")
    def test_stopping_workers_go_to_unhealthy(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "stopping", WorkerState.STOPPING)
        health = pool.health_check()
        assert "stopping" in health["unhealthy"]

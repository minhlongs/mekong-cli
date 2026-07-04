"""Tests for src/daemon/mission_control.py — mission control module."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pm2_process(name: str, status: str = "online", cpu: float = 1.0,
                      memory: int = 1024 * 1024 * 50, uptime: int = 60000,
                      restarts: int = 0, pid: int = 1234) -> dict:
    return {
        "pid": pid,
        "pm2_env": {
            "name": name,
            "status": status,
            "pm_uptime": uptime,
            "restart_time": restarts,
        },
        "monit": {
            "cpu": cpu,
            "memory": memory,
        },
    }


def _make_completed_result(stdout: str, returncode: int = 0):
    r = MagicMock(spec=subprocess.CompletedProcess)
    r.returncode = returncode
    r.stdout = stdout
    return r


# ---------------------------------------------------------------------------
# _run_pm2
# ---------------------------------------------------------------------------

class TestRunPm2:
    def test_calls_subprocess_run(self):
        from src.daemon.mission_control import _run_pm2
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed_result("[]")
            _run_pm2(["jlist"])
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            assert args[0][0] == "pm2"
            assert "jlist" in args[0]

    def test_passes_mekong_root_in_env(self):
        from src.daemon.mission_control import _run_pm2, MEKONG_ROOT
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed_result("[]")
            _run_pm2(["jlist"])
            _, kwargs = mock_run.call_args
            assert kwargs["env"]["MEKONG_ROOT"] == str(MEKONG_ROOT)


# ---------------------------------------------------------------------------
# get_worker_status
# ---------------------------------------------------------------------------

class TestGetWorkerStatus:
    def test_returns_empty_when_pm2_fails(self):
        from src.daemon.mission_control import get_worker_status
        with patch("src.daemon.mission_control._run_pm2") as mock_pm2:
            mock_pm2.return_value = _make_completed_result("", returncode=1)
            result = get_worker_status()
            assert result == []

    def test_returns_empty_on_empty_stdout(self):
        from src.daemon.mission_control import get_worker_status
        with patch("src.daemon.mission_control._run_pm2") as mock_pm2:
            mock_pm2.return_value = _make_completed_result("   ")
            result = get_worker_status()
            assert result == []

    def test_returns_empty_on_invalid_json(self):
        from src.daemon.mission_control import get_worker_status
        with patch("src.daemon.mission_control._run_pm2") as mock_pm2:
            mock_pm2.return_value = _make_completed_result("not-json")
            result = get_worker_status()
            assert result == []

    def test_filters_non_daemon_processes(self):
        from src.daemon.mission_control import get_worker_status
        processes = [
            _make_pm2_process("my-web-app"),   # no daemon keyword
            _make_pm2_process("my-worker"),    # has "worker"
        ]
        with patch("src.daemon.mission_control._run_pm2") as mock_pm2:
            mock_pm2.return_value = _make_completed_result(json.dumps(processes))
            result = get_worker_status()
            assert len(result) == 1
            assert result[0].name == "my-worker"

    def test_includes_all_daemon_keywords(self):
        from src.daemon.mission_control import get_worker_status
        keywords = ["worker", "daemon", "dispatcher", "scheduler", "heartbeat", "jidoka", "learning"]
        processes = [_make_pm2_process(f"my-{kw}") for kw in keywords]
        with patch("src.daemon.mission_control._run_pm2") as mock_pm2:
            mock_pm2.return_value = _make_completed_result(json.dumps(processes))
            result = get_worker_status()
            assert len(result) == len(keywords)

    def test_maps_fields_correctly(self):
        from src.daemon.mission_control import get_worker_status
        proc = _make_pm2_process(
            name="my-worker",
            status="online",
            cpu=25.5,
            memory=1024 * 1024 * 100,  # 100 MB in bytes
            uptime=120000,
            restarts=3,
            pid=9999,
        )
        with patch("src.daemon.mission_control._run_pm2") as mock_pm2:
            mock_pm2.return_value = _make_completed_result(json.dumps([proc]))
            result = get_worker_status()
            w = result[0]
            assert w.name == "my-worker"
            assert w.status == "online"
            assert w.cpu == 25.5
            assert abs(w.memory_mb - 100.0) < 0.1
            assert w.uptime_ms == 120000
            assert w.restarts == 3
            assert w.pid == 9999

    def test_handles_missing_monit_fields(self):
        from src.daemon.mission_control import get_worker_status
        proc = {"pid": None, "pm2_env": {"name": "my-daemon", "status": "offline"}, "monit": {}}
        with patch("src.daemon.mission_control._run_pm2") as mock_pm2:
            mock_pm2.return_value = _make_completed_result(json.dumps([proc]))
            result = get_worker_status()
            assert result[0].cpu == 0.0
            assert result[0].memory_mb == 0.0


# ---------------------------------------------------------------------------
# _calculate_throughput
# ---------------------------------------------------------------------------

class TestCalculateThroughput:
    def test_returns_zero_when_journal_missing(self, tmp_path):
        from src.daemon import mission_control
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            result = mission_control._calculate_throughput()
            assert result == 0.0

    def test_returns_zero_when_no_completed_missions(self, tmp_path):
        from src.daemon import mission_control
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": []}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            result = mission_control._calculate_throughput()
            assert result == 0.0

    def test_calculates_throughput_correctly(self, tmp_path):
        from src.daemon import mission_control
        now = datetime.now()
        missions = [
            {"completed_at": (now - timedelta(minutes=30)).isoformat(), "status": "success"},
            {"completed_at": (now - timedelta(minutes=20)).isoformat(), "status": "success"},
            {"completed_at": (now - timedelta(minutes=10)).isoformat(), "status": "success"},
        ]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            result = mission_control._calculate_throughput()
            assert result > 0.0

    def test_excludes_old_missions(self, tmp_path):
        from src.daemon import mission_control
        now = datetime.now()
        missions = [
            {"completed_at": (now - timedelta(hours=2)).isoformat(), "status": "success"},
        ]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            result = mission_control._calculate_throughput()
            assert result == 0.0

    def test_returns_zero_on_invalid_json(self, tmp_path):
        from src.daemon import mission_control
        journal = tmp_path / "missions.json"
        journal.write_text("bad json")
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            result = mission_control._calculate_throughput()
            assert result == 0.0


# ---------------------------------------------------------------------------
# _calculate_success_rate
# ---------------------------------------------------------------------------

class TestCalculateSuccessRate:
    def test_returns_100_when_journal_missing(self, tmp_path):
        from src.daemon import mission_control
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control._calculate_success_rate() == 100.0

    def test_returns_100_when_no_missions(self, tmp_path):
        from src.daemon import mission_control
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": []}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control._calculate_success_rate() == 100.0

    def test_calculates_rate_correctly(self, tmp_path):
        from src.daemon import mission_control
        missions = [
            {"status": "success"},
            {"status": "success"},
            {"status": "failure"},
            {"status": "success"},
        ]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            rate = mission_control._calculate_success_rate()
            assert abs(rate - 75.0) < 0.01

    def test_considers_only_last_100(self, tmp_path):
        from src.daemon import mission_control
        # 50 old failures + 100 recent successes
        old = [{"status": "failure"}] * 50
        recent = [{"status": "success"}] * 100
        missions = old + recent
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            rate = mission_control._calculate_success_rate()
            assert rate == 100.0

    def test_returns_zero_on_invalid_json(self, tmp_path):
        from src.daemon import mission_control
        journal = tmp_path / "missions.json"
        journal.write_text("bad json")
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control._calculate_success_rate() == 0.0


# ---------------------------------------------------------------------------
# _get_queue_depth
# ---------------------------------------------------------------------------

class TestGetQueueDepth:
    def test_returns_zero_when_journal_missing(self, tmp_path):
        from src.daemon import mission_control
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control._get_queue_depth() == 0

    def test_counts_pending_and_active(self, tmp_path):
        from src.daemon import mission_control
        missions = [
            {"status": "pending"},
            {"status": "active"},
            {"status": "success"},
            {"status": "pending"},
        ]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control._get_queue_depth() == 3

    def test_returns_zero_when_all_complete(self, tmp_path):
        from src.daemon import mission_control
        missions = [{"status": "success"}, {"status": "failure"}]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control._get_queue_depth() == 0


# ---------------------------------------------------------------------------
# _calculate_avg_response_time
# ---------------------------------------------------------------------------

class TestCalculateAvgResponseTime:
    def test_returns_zero_when_journal_missing(self, tmp_path):
        from src.daemon import mission_control
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control._calculate_avg_response_time() == 0.0

    def test_returns_zero_when_no_duration_data(self, tmp_path):
        from src.daemon import mission_control
        missions = [{"status": "success"}]  # no duration_ms
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control._calculate_avg_response_time() == 0.0

    def test_calculates_average_correctly(self, tmp_path):
        from src.daemon import mission_control
        missions = [
            {"duration_ms": 100},
            {"duration_ms": 200},
            {"duration_ms": 300},
        ]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            result = mission_control._calculate_avg_response_time()
            assert abs(result - 200.0) < 0.01

    def test_considers_only_last_50(self, tmp_path):
        from src.daemon import mission_control
        # 50 old missions with 1000ms + 50 recent with 100ms
        old = [{"duration_ms": 1000}] * 50
        recent = [{"duration_ms": 100}] * 50
        missions = old + recent
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            result = mission_control._calculate_avg_response_time()
            assert abs(result - 100.0) < 0.01


# ---------------------------------------------------------------------------
# get_dispatch_queue
# ---------------------------------------------------------------------------

class TestGetDispatchQueue:
    def test_returns_empty_when_journal_missing(self, tmp_path):
        from src.daemon import mission_control
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control.get_dispatch_queue() == []

    def test_includes_only_pending_and_active(self, tmp_path):
        from src.daemon import mission_control
        missions = [
            {"task_id": "t1", "status": "pending", "description": "task 1", "priority": "HIGH"},
            {"task_id": "t2", "status": "active", "description": "task 2", "priority": "MEDIUM"},
            {"task_id": "t3", "status": "success", "description": "task 3", "priority": "LOW"},
        ]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            queue = mission_control.get_dispatch_queue()
            assert len(queue) == 2
            ids = {q.task_id for q in queue}
            assert "t1" in ids
            assert "t2" in ids

    def test_sorts_by_priority(self, tmp_path):
        from src.daemon import mission_control
        missions = [
            {"task_id": "t-low", "status": "pending", "description": "low", "priority": "LOW"},
            {"task_id": "t-critical", "status": "pending", "description": "crit", "priority": "CRITICAL"},
            {"task_id": "t-high", "status": "pending", "description": "high", "priority": "HIGH"},
            {"task_id": "t-medium", "status": "pending", "description": "med", "priority": "MEDIUM"},
        ]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            queue = mission_control.get_dispatch_queue()
            assert queue[0].task_id == "t-critical"
            assert queue[1].task_id == "t-high"
            assert queue[2].task_id == "t-medium"
            assert queue[3].task_id == "t-low"

    def test_truncates_description_to_100_chars(self, tmp_path):
        from src.daemon import mission_control
        long_desc = "x" * 200
        missions = [{"task_id": "t1", "status": "pending", "description": long_desc, "priority": "LOW"}]
        journal = tmp_path / "missions.json"
        journal.write_text(json.dumps({"missions": missions}))
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            queue = mission_control.get_dispatch_queue()
            assert len(queue[0].description) <= 100

    def test_returns_empty_on_invalid_json(self, tmp_path):
        from src.daemon import mission_control
        journal = tmp_path / "missions.json"
        journal.write_text("bad json")
        with patch.object(mission_control, "JOURNAL_DIR", tmp_path):
            assert mission_control.get_dispatch_queue() == []


# ---------------------------------------------------------------------------
# get_recent_alerts
# ---------------------------------------------------------------------------

class TestGetRecentAlerts:
    def test_returns_empty_when_file_missing(self, tmp_path):
        from src.daemon import mission_control
        with patch.object(mission_control, "JIDOKA_FILE", tmp_path / "nonexistent.log"):
            assert mission_control.get_recent_alerts() == []

    def test_returns_last_n_lines(self, tmp_path):
        from src.daemon import mission_control
        alert_file = tmp_path / "jidoka-alerts.log"
        lines = [f"alert-{i}" for i in range(20)]
        alert_file.write_text("\n".join(lines))
        with patch.object(mission_control, "JIDOKA_FILE", alert_file):
            result = mission_control.get_recent_alerts(limit=5)
            assert len(result) == 5
            assert result[-1] == "alert-19"

    def test_default_limit_is_10(self, tmp_path):
        from src.daemon import mission_control
        alert_file = tmp_path / "jidoka-alerts.log"
        lines = [f"a-{i}" for i in range(20)]
        alert_file.write_text("\n".join(lines))
        with patch.object(mission_control, "JIDOKA_FILE", alert_file):
            result = mission_control.get_recent_alerts()
            assert len(result) == 10

    def test_returns_all_when_fewer_than_limit(self, tmp_path):
        from src.daemon import mission_control
        alert_file = tmp_path / "jidoka-alerts.log"
        alert_file.write_text("alert-1\nalert-2")
        with patch.object(mission_control, "JIDOKA_FILE", alert_file):
            result = mission_control.get_recent_alerts(limit=10)
            assert len(result) == 2


# ---------------------------------------------------------------------------
# get_metrics
# ---------------------------------------------------------------------------

class TestGetMetrics:
    def test_aggregates_worker_counts(self):
        from src.daemon.mission_control import get_metrics, WorkerStatus
        workers = [
            WorkerStatus("w1", "online", 1.0, 50.0, 60000, 0, 1),
            WorkerStatus("w2", "offline", 0.0, 0.0, 0, 1, None),
            WorkerStatus("w3", "online", 2.0, 100.0, 90000, 0, 2),
        ]
        with patch("src.daemon.mission_control.get_worker_status", return_value=workers):
            with patch("src.daemon.mission_control._calculate_throughput", return_value=5.0):
                with patch("src.daemon.mission_control._calculate_success_rate", return_value=90.0):
                    with patch("src.daemon.mission_control._get_queue_depth", return_value=3):
                        with patch("src.daemon.mission_control._calculate_avg_response_time", return_value=200.0):
                            metrics = get_metrics()
                            assert metrics.total_workers == 3
                            assert metrics.online_workers == 2
                            assert metrics.throughput_per_minute == 5.0
                            assert metrics.success_rate == 90.0
                            assert metrics.queue_depth == 3
                            assert metrics.avg_response_time_ms == 200.0

    def test_last_updated_is_iso_format(self):
        from src.daemon.mission_control import get_metrics
        with patch("src.daemon.mission_control.get_worker_status", return_value=[]):
            with patch("src.daemon.mission_control._calculate_throughput", return_value=0.0):
                with patch("src.daemon.mission_control._calculate_success_rate", return_value=100.0):
                    with patch("src.daemon.mission_control._get_queue_depth", return_value=0):
                        with patch("src.daemon.mission_control._calculate_avg_response_time", return_value=0.0):
                            metrics = get_metrics()
                            # Should parse as ISO datetime without exception
                            datetime.fromisoformat(metrics.last_updated)


# ---------------------------------------------------------------------------
# get_status_summary
# ---------------------------------------------------------------------------

class TestGetStatusSummary:
    def test_returns_complete_structure(self, tmp_path):
        from src.daemon import mission_control
        from src.daemon.mission_control import WorkerStatus, DaemonMetrics

        workers = [WorkerStatus("w1", "online", 0.5, 50.0, 10000, 0, 123)]
        metrics = DaemonMetrics(
            total_workers=1, online_workers=1, throughput_per_minute=1.0,
            success_rate=100.0, queue_depth=0, avg_response_time_ms=50.0,
            last_updated=datetime.now().isoformat()
        )
        queue = []
        alerts = ["alert-1"]

        with patch("src.daemon.mission_control.get_worker_status", return_value=workers):
            with patch("src.daemon.mission_control.get_metrics", return_value=metrics):
                with patch("src.daemon.mission_control.get_dispatch_queue", return_value=queue):
                    with patch("src.daemon.mission_control.get_recent_alerts", return_value=alerts):
                        summary = mission_control.get_status_summary()

        assert "timestamp" in summary
        assert "workers" in summary
        assert "metrics" in summary
        assert "queue" in summary
        assert "recent_alerts" in summary
        assert summary["recent_alerts"] == ["alert-1"]
        assert len(summary["workers"]) == 1
        assert summary["workers"][0]["name"] == "w1"


# ---------------------------------------------------------------------------
# Dataclass fields
# ---------------------------------------------------------------------------

class TestDataclasses:
    def test_worker_status_fields(self):
        from src.daemon.mission_control import WorkerStatus
        w = WorkerStatus("name", "online", 1.0, 50.0, 60000, 2, 999)
        assert w.name == "name"
        assert w.pid == 999

    def test_daemon_metrics_defaults(self):
        from src.daemon.mission_control import DaemonMetrics
        m = DaemonMetrics()
        assert m.total_workers == 0
        assert m.success_rate == 0.0

    def test_queue_item_fields(self):
        from src.daemon.mission_control import QueueItem
        item = QueueItem("task-1", "do something", "HIGH", "pending")
        assert item.task_id == "task-1"
        assert item.assigned_to is None

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mission Control — Daemon army status, metrics, and dispatch queue.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.file_lock import locked_read

from .mission_control_metrics import (
    DaemonMetrics, QueueItem, WorkerStatus, _calculate_avg_response_time,
    _calculate_success_rate, _calculate_throughput, _get_queue_depth,
)

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
MEKONG_DIR = MEKONG_ROOT / ".mekong"
JOURNAL_DIR = MEKONG_DIR / "journal"
JIDOKA_FILE = MEKONG_DIR / "jidoka-alerts.log"

JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

_DAEMON_KEYWORDS = ("worker", "daemon", "dispatcher", "scheduler", "heartbeat", "jidoka", "learning")


def _run_pm2(args: list[str]) -> subprocess.CompletedProcess:
    """Run PM2 command and return result."""
    env = {**os.environ, "MEKONG_ROOT": str(MEKONG_ROOT)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(
            subprocess.run, ["pm2"] + args, capture_output=True, text=True, env=env, check=False
        ).result()


def get_worker_status() -> list[WorkerStatus]:
    """Query PM2 for all worker statuses."""
    result = _run_pm2(["jlist"])
    if result.returncode != 0 or not result.stdout.strip():
        logger.warning("PM2 not running or no processes found")
        return []
    try:
        processes = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.exception("PM2 returned invalid JSON")
        return []

    workers = []
    for p in processes:
        pm2_env = p.get("pm2_env", {})
        monit = p.get("monit", {})
        name = pm2_env.get("name", "?")
        if not any(kw in name.lower() for kw in _DAEMON_KEYWORDS):
            continue
        workers.append(
            WorkerStatus(
                name=name,
                status=pm2_env.get("status", "unknown"),
                cpu=monit.get("cpu", 0.0),
                memory_mb=monit.get("memory", 0) / 1024 / 1024,
                uptime_ms=pm2_env.get("pm_uptime", 0),
                restarts=pm2_env.get("restart_time", 0),
                pid=p.get("pid"),
            )
        )
    return workers


def get_metrics(
    workers: list[WorkerStatus] | None = None, missions: list[dict] | None = None
) -> DaemonMetrics:
    """Get aggregate metrics for the daemon army."""
    if workers is None:
        workers = get_worker_status()
    return DaemonMetrics(
        total_workers=len(workers),
        online_workers=sum(1 for w in workers if w.status == "online"),
        throughput_per_minute=_calculate_throughput(missions),
        success_rate=_calculate_success_rate(missions),
        queue_depth=_get_queue_depth(missions),
        avg_response_time_ms=_calculate_avg_response_time(missions),
        last_updated=datetime.now().isoformat(),
    )


def get_dispatch_queue(missions: list[dict] | None = None) -> list[QueueItem]:
    """Get current dispatch queue sorted by priority."""
    if missions is None:
        journal_file = JOURNAL_DIR / "missions.json"
        if not journal_file.exists():
            return []
        try:
            with locked_read(journal_file) as f:
                content = f.read()
                data = json.loads(content) if content else {}
            missions = data.get("missions", [])
        except (json.JSONDecodeError, KeyError):
            logger.exception("Failed to get dispatch queue")
            return []

    queue_items = [
        QueueItem(
            task_id=m.get("task_id", "?"), description=m.get("description", "Unknown task")[:100],
            priority=m.get("priority", "MEDIUM"), status=m.get("status", "pending"),
            assigned_to=m.get("assigned_to"), created_at=m.get("created_at", ""),
            started_at=m.get("started_at"), completed_at=m.get("completed_at"),
        )
        for m in missions
        if m.get("status") in ["pending", "active"]
    ]
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    queue_items.sort(key=lambda x: priority_order.get(x.priority, 2))
    return queue_items


def get_recent_alerts(limit: int = 10) -> list[str]:
    """Get recent Jidoka alerts."""
    if not JIDOKA_FILE.exists():
        return []
    try:
        return JIDOKA_FILE.read_text().strip().split("\n")[-limit:]
    except Exception:
        logger.exception("Failed to read Jidoka alerts")
        return []


def get_status_summary() -> dict[str, Any]:
    """Get complete status summary for API response."""
    workers = get_worker_status()
    journal_file = JOURNAL_DIR / "missions.json"
    missions = []
    if journal_file.exists():
        try:
            with locked_read(journal_file) as f:
                content = f.read()
                if content:
                    missions = json.loads(content).get("missions", [])
        except Exception:
            pass

    metrics = get_metrics(workers, missions)
    queue = get_dispatch_queue(missions)
    return {
        "timestamp": datetime.now().isoformat(),
        "workers": [
            {
                "name": w.name, "status": w.status, "cpu": w.cpu, "memory_mb": w.memory_mb,
                "uptime_ms": w.uptime_ms, "restarts": w.restarts, "pid": w.pid,
            }
            for w in workers
        ],
        "metrics": {
            "total_workers": metrics.total_workers, "online_workers": metrics.online_workers,
            "throughput_per_minute": metrics.throughput_per_minute, "success_rate": metrics.success_rate,
            "queue_depth": metrics.queue_depth, "avg_response_time_ms": metrics.avg_response_time_ms,
            "last_updated": metrics.last_updated,
        },
        "queue": [
            {
                "task_id": q.task_id, "description": q.description, "priority": q.priority,
                "status": q.status, "assigned_to": q.assigned_to, "created_at": q.created_at,
            }
            for q in queue[:20]
        ],
        "recent_alerts": get_recent_alerts(5),
    }

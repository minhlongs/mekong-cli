# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Worker Pool — Manage multiple daemon workers with spawn/monitor/retire.

Features:
- Dynamic worker spawning via PM2
- Health checks every 30 seconds
- Auto-restart on failure
- Load tracking for load balancer
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .worker_pool_models import (
    WorkerInfo,
    WorkerPoolStats,
    WorkerState,
    apply_pm2_status_to_workers,
    classify_worker_health,
    compute_worker_pool_stats,
)

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
MEKONG_DIR = MEKONG_ROOT / ".mekong"


class WorkerPool:
    """
    Manages a pool of daemon workers.
    """

    def __init__(self) -> None:
        self.workers: dict[str, WorkerInfo] = {}
        self._health_check_interval = 30
        self._last_health_check = 0.0
        self.refresh_cache_ttl = 5.0
        self._last_refresh = 0.0

    def _pm2_available(self) -> bool:
        """Check if PM2 is installed and available in PATH."""
        return shutil.which("pm2") is not None

    def _run_pm2(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run PM2 command. Returns failed result if PM2 not installed."""
        if not self._pm2_available():
            logger.debug("[WorkerPool] PM2 not installed — skipping pm2 command")
            return subprocess.CompletedProcess(
                args=["pm2"] + args,
                returncode=1,
                stdout="",
                stderr="PM2 not installed",
            )
        env = {**__import__("os").environ, "MEKONG_ROOT": str(MEKONG_ROOT)}
        return subprocess.run(
            ["pm2"] + args,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def spawn(
        self,
        name: str,
        capability: str,
        script: str,
        args: str = "",
        max_memory: str = "200M",
    ) -> bool:
        """Spawn a new worker via PM2."""
        cmd = ["pm2", "start", script]
        if args:
            cmd.extend(["--", args])
        cmd.extend(["--name", name])

        result = self._run_pm2(cmd)
        if result.returncode == 0:
            self.workers[name] = WorkerInfo(
                id=name,
                name=name,
                capability=capability,
                state=WorkerState.IDLE,
                started_at=datetime.now().isoformat(),
            )
            logger.info(f"[WorkerPool] Spawned {name} (capability={capability})")
            return True

        logger.error(f"[WorkerPool] Failed to spawn {name}: {result.stderr}")
        return False

    def retire(self, name: str) -> bool:
        """Retire a worker (stop and remove from pool)."""
        result = self._run_pm2(["stop", name])
        if result.returncode == 0:
            self._run_pm2(["delete", name])
            if name in self.workers:
                del self.workers[name]
            logger.info(f"[WorkerPool] Retired {name}")
            return True

        logger.error(f"[WorkerPool] Failed to retire {name}: {result.stderr}")
        return False

    def get_available_worker(self, capability: str | None = None) -> WorkerInfo | None:
        """Get an available (idle) worker, optionally filtered by capability."""
        self.refresh_status()
        for worker in self.workers.values():
            if worker.state != WorkerState.IDLE:
                continue
            if capability and worker.capability != capability:
                continue
            return worker
        return None

    def mark_busy(self, name: str) -> None:
        """Mark a worker as busy."""
        if name in self.workers:
            self.workers[name].state = WorkerState.BUSY
            logger.debug(f"[WorkerPool] Marked {name} as busy")

    def mark_idle(self, name: str) -> None:
        """Mark a worker as idle after completing a task."""
        if name in self.workers:
            self.workers[name].state = WorkerState.IDLE
            self.workers[name].tasks_completed += 1
            self.workers[name].last_heartbeat = datetime.now().isoformat()
            logger.debug(f"[WorkerPool] Marked {name} as idle")

    def mark_failed(self, name: str) -> None:
        """Mark a worker as failed."""
        if name in self.workers:
            self.workers[name].state = WorkerState.ERRORED
            self.workers[name].tasks_failed += 1
            logger.warning(f"[WorkerPool] Marked {name} as failed")

    def refresh_status(self, force: bool = False) -> None:
        """Refresh worker status from PM2."""
        now = time.time()
        if not force and (now - self._last_refresh) < self.refresh_cache_ttl:
            return
        self._last_refresh = now

        result = self._run_pm2(["jlist"])
        if result.returncode != 0 or not result.stdout.strip():
            for worker in self.workers.values():
                worker.state = WorkerState.OFFLINE
            return

        apply_pm2_status_to_workers(self.workers, result.stdout)

    def get_stats(self) -> WorkerPoolStats:
        """Get aggregate statistics for the worker pool."""
        self.refresh_status()
        return compute_worker_pool_stats(self.workers)

    def health_check(self) -> dict[str, Any]:
        """Perform health check on all workers."""
        self.refresh_status()
        self._last_health_check = time.time()
        return classify_worker_health(self.workers)

    def list_workers(self) -> list[WorkerInfo]:
        """Get list of all workers."""
        self.refresh_status()
        return list(self.workers.values())

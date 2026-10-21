# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Autonomous Scheduler."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from pathlib import Path
import time
from typing import Any
import uuid

from src.core.event_bus import EventType, get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class ScheduledJob:
    """A single scheduled job."""
    id: str
    name: str
    goal: str
    job_type: str  # "interval" or "daily"
    interval_seconds: int = 0
    daily_time: str = ""
    enabled: bool = True
    last_run: float = 0.0
    next_run: float = 0.0
    run_count: int = 0


class Scheduler:
    """Autonomous scheduler for recurring Mekong missions."""

    def __init__(self, config_path: str | None = None) -> None:
        self._jobs: dict[str, ScheduledJob] = {}
        self._config_path = config_path or str(Path(".mekong") / "schedule.yaml")
        self._running = False
        self._run_callback: Callable[[str], dict[str, Any]] | None = None
        self._load()

    def add_job(
        self, name: str, goal: str, job_type: str = "interval",
        interval_seconds: int = 300, daily_time: str = "09:00",
    ) -> ScheduledJob:
        job_id = uuid.uuid4().hex[:8]
        now = time.time()
        next_run = self._next_daily_run(daily_time) if job_type == "daily" else (now + interval_seconds)
        job = ScheduledJob(
            id=job_id, name=name, goal=goal, job_type=job_type,
            interval_seconds=interval_seconds, daily_time=daily_time, next_run=next_run,
        )
        self._jobs[job_id] = job
        self._save()
        return job

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._save()
            return True
        return False

    def list_jobs(self) -> list[ScheduledJob]:
        return list(self._jobs.values())

    def get_job(self, job_id: str) -> ScheduledJob | None:
        return self._jobs.get(job_id)

    def get_due_jobs(self) -> list[ScheduledJob]:
        now = time.time()
        return [j for j in self._jobs.values() if j.enabled and j.next_run <= now]

    def mark_completed(self, job: ScheduledJob) -> None:
        now = time.time()
        job.last_run = now
        job.run_count += 1
        job.next_run = self._next_daily_run(job.daily_time) if job.job_type == "daily" else (now + job.interval_seconds)
        self._save()

    def set_run_callback(self, callback: Callable[[str], dict[str, Any]]) -> None:
        self._run_callback = callback

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def job_count(self) -> int:
        return len(self._jobs)

    async def tick(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        bus = get_event_bus()
        for job in self.get_due_jobs():
            bus.emit(EventType.JOB_STARTED, {
                "job_id": job.id, "job_name": job.name, "goal": job.goal, "source": "scheduler",
            })
            result: dict[str, Any] = {"job_id": job.id, "status": "skipped"}
            if self._run_callback:
                try:
                    result = self._run_callback(job.goal)
                    result["job_id"] = job.id
                except Exception as e:
                    result = {"job_id": job.id, "status": "error", "error": str(e)}
            bus.emit(EventType.JOB_COMPLETED, {"job_id": job.id, "job_name": job.name, "result": result})
            self.mark_completed(job)
            results.append(result)
        return results

    async def run_loop(self, check_interval: float = 60.0) -> None:
        self._running = True
        try:
            while self._running:
                await self.tick()
                await asyncio.sleep(check_interval)
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False

    @staticmethod
    def _next_daily_run(time_str: str) -> float:
        try:
            hour, minute = map(int, time_str.split(":"))
        except (ValueError, AttributeError):
            hour, minute = 9, 0
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target.timestamp()

    def _save(self) -> None:
        path = Path(self._config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Mekong Schedule\njobs:\n"]
        for job in self._jobs.values():
            lines.append(
                f"  - id: {job.id}\n    name: {job.name}\n    goal: {job.goal}\n"
                f"    job_type: {job.job_type}\n    interval_seconds: {job.interval_seconds}\n"
                f'    daily_time: "{job.daily_time}"\n    enabled: {str(job.enabled).lower()}\n'
                f"    last_run: {job.last_run}\n    next_run: {job.next_run}\n    run_count: {job.run_count}\n"
            )
        path.write_text("".join(lines), encoding="utf-8")

    def _load(self) -> None:
        path = Path(self._config_path)
        if not path.exists():
            return
        try:
            import yaml  # type: ignore[import-untyped]
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logger.debug("Failed to parse schedule YAML: %s", e)
            return
        for entry in raw.get("jobs") or []:
            job = ScheduledJob(
                id=str(entry.get("id", "")), name=str(entry.get("name", "")), goal=str(entry.get("goal", "")),
                job_type=str(entry.get("job_type", "interval")), interval_seconds=int(entry.get("interval_seconds", 300)),
                daily_time=str(entry.get("daily_time", "09:00")), enabled=bool(entry.get("enabled", True)),
                last_run=float(entry.get("last_run", 0.0)), next_run=float(entry.get("next_run", 0.0)),
                run_count=int(entry.get("run_count", 0)),
            )
            if job.id:
                self._jobs[job.id] = job


__all__ = ["ScheduledJob", "Scheduler"]

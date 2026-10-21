# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
HEARTBEAT Scheduler Models & Parsers — ScheduledTask, HeartbeatConfig, and cron/markdown parsers.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("heartbeat")


@dataclass
class ScheduledTask:
    description: str
    command: Optional[str] = None
    interval_minutes: int = 60
    cron_hour: Optional[int] = None
    cron_weekday: Optional[int] = None  # 0=Monday
    last_run: Optional[datetime] = None
    workspace: str = "default"
    tier: int = 1  # 1=script, 2=LLM


@dataclass
class HeartbeatConfig:
    enabled: bool = True
    check_interval: int = 60  # seconds between scheduler checks
    max_concurrent: int = 3
    alert_on_failure: bool = True
    workspaces: list[str] = field(default_factory=lambda: ["lam"])


def parse_cron_expr(cron: str) -> tuple[int, Optional[int], Optional[int]]:
    """Parse simple cron expression into (interval_minutes, hour, weekday)."""
    parts = cron.strip().split()
    if len(parts) < 5:
        return (60, None, None)

    minute, hour, _dom, _month, dow = parts[:5]

    if minute.startswith("*/"):
        return (int(minute[2:]), None, None)

    interval = 1440
    parsed_hour = None
    parsed_weekday = None

    if hour != "*":
        parsed_hour = int(hour)

    if dow != "*":
        first_day = dow.split(",")[0]
        parsed_weekday = int(first_day) if first_day.isdigit() else None
        if "," in dow:
            interval = 1440

    return (interval, parsed_hour, parsed_weekday)


def parse_heartbeat_markdown(workspace: str, hb_path: Path) -> list[ScheduledTask]:
    """Parse HEARTBEAT.md into ScheduledTask list."""
    content = hb_path.read_text()
    tasks = []
    current_interval = 60
    current_hour = None
    current_weekday = None

    for line in content.split("\n"):
        line = line.strip()

        if line.startswith("## Every 30"):
            current_interval = 30
            current_hour = None
            current_weekday = None
        elif line.startswith("## Every 1") or line.startswith("## Hourly"):
            current_interval = 60
            current_hour = None
            current_weekday = None
        elif line.startswith("## Daily") or line.startswith("## Every Day"):
            current_interval = 1440
            time_match = re.search(r"(\d{1,2}):(\d{2})", line)
            if time_match:
                current_hour = int(time_match.group(1))
            current_weekday = None
        elif line.startswith("## Weekly"):
            current_interval = 10080
            current_weekday = 0
            day_match = re.search(r"(Monday|Tuesday|Wednesday|Thursday|Friday)", line, re.I)
            if day_match:
                days = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4}
                current_weekday = days.get(day_match.group(1).lower(), 0)
        elif line.startswith("## Monthly"):
            current_interval = 43200

        task_match = re.match(r"- \[[ x]\] \*?\*?(.+?)(?:\*\*)?(?:\s+`(.+?)`)?$", line)
        if task_match:
            desc = task_match.group(1).strip().rstrip("*").strip()
            cmd = task_match.group(2)

            tasks.append(
                ScheduledTask(
                    description=desc,
                    command=cmd,
                    interval_minutes=current_interval,
                    cron_hour=current_hour,
                    cron_weekday=current_weekday,
                    workspace=workspace,
                    tier=1 if cmd else 2,
                )
            )

    return tasks


def load_loop_tasks(loops_dir: Path, cron_parser) -> list[ScheduledTask]:
    """Load autonomous ops loops from .mekong/loops/*.json."""
    if not loops_dir.exists():
        return []

    tasks = []
    for loop_file in sorted(loops_dir.glob("*.json")):
        try:
            data = json.loads(loop_file.read_text())
            if not data.get("enabled", True):
                logger.info(f"Loop disabled: {data.get('name', loop_file.stem)}")
                continue

            cron = data.get("schedule", {}).get("cron", "0 * * * *")
            interval, hour, weekday = cron_parser(cron)

            tier1 = data.get("tier1_check", {})
            command = tier1.get("command")

            task = ScheduledTask(
                description=f"[{data.get('name', loop_file.stem)}] {data.get('description', '')}",
                command=command,
                interval_minutes=interval,
                cron_hour=hour,
                cron_weekday=weekday,
                workspace="solo-ops",
                tier=1 if command else 2,
            )
            task._model_tier = data.get("model_tier", "fast")  # type: ignore[attr-defined]
            tasks.append(task)

            dry = " (DRY RUN)" if data.get("dry_run", False) else ""
            logger.info(f"Loaded loop: {data['name']} [{cron}]{dry}")

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse loop {loop_file}: {e}")

    return tasks

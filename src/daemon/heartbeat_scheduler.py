# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
HEARTBEAT Scheduler — reads HEARTBEAT.md + .mekong/loops/*.json configs.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .heartbeat_models import (
    HeartbeatConfig,
    ScheduledTask,
    load_loop_tasks,
    parse_cron_expr,
    parse_heartbeat_markdown,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [HEARTBEAT] %(message)s")
logger = logging.getLogger("heartbeat")


class HeartbeatScheduler:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.mekong_dir = self.root / ".mekong"
        self.tasks: list[ScheduledTask] = []
        self.running: dict[str, asyncio.Task] = {}
        self.config = HeartbeatConfig()
        self._load_config()

    def _load_config(self):
        config_path = self.mekong_dir / "heartbeat-config.json"
        if config_path.exists():
            data = json.loads(config_path.read_text())
            self.config.enabled = data.get("enabled", True)
            self.config.check_interval = data.get("check_interval", 60)
            self.config.max_concurrent = data.get("max_concurrent", 3)
            self.config.workspaces = data.get("workspaces", ["lam"])

    def discover_heartbeats(self) -> list[tuple[str, Path]]:
        """Find all HEARTBEAT.md files — root + per-tenant."""
        results = []
        root_hb = self.root / "HEARTBEAT.md"
        if root_hb.exists():
            results.append(("root", root_hb))
        studio_dir = self.mekong_dir / "studio"
        if studio_dir.exists():
            for ws in studio_dir.iterdir():
                if ws.is_dir() and (ws / "HEARTBEAT.md").exists():
                    results.append((ws.name, ws / "HEARTBEAT.md"))
        return results

    def discover_loops(self) -> list[ScheduledTask]:
        """Load autonomous ops loops from .mekong/loops/*.json."""
        return load_loop_tasks(self.mekong_dir / "loops", self._parse_cron)

    @staticmethod
    def _parse_cron(cron: str) -> tuple[int, Optional[int], Optional[int]]:
        return parse_cron_expr(cron)

    def parse_heartbeat(self, workspace: str, hb_path: Path) -> list[ScheduledTask]:
        return parse_heartbeat_markdown(workspace, hb_path)

    def is_due(self, task: ScheduledTask, now: datetime) -> bool:
        """Check if task should run now."""
        if task.last_run is not None:
            if (now - task.last_run).total_seconds() / 60 < task.interval_minutes:
                return False
        if task.cron_hour is not None and now.hour != task.cron_hour:
            return False
        if task.cron_weekday is not None and now.weekday() != task.cron_weekday:
            return False
        return True

    async def execute_task(self, task: ScheduledTask) -> bool:
        """Execute task — two-tier processing."""
        logger.info(f"[{task.workspace}] Executing: {task.description}")
        task.last_run = datetime.now()

        if task.tier == 1 and task.command:
            try:
                result = subprocess.run(
                    task.command, shell=True, capture_output=True, text=True,
                    timeout=300, cwd=str(self.root),
                    env={**os.environ, "PYTHONPATH": str(self.root)},
                )
                if result.returncode == 0:
                    logger.info(f"[{task.workspace}] ✅ {task.description}")
                    return True
                logger.warning(f"[{task.workspace}] ⚠️ {task.description}: exit {result.returncode}")
                if self.config.alert_on_failure:
                    self._alert(task, result.stderr[:200])
                return False
            except subprocess.TimeoutExpired:
                logger.error(f"[{task.workspace}] ❌ {task.description}: timeout 300s")
                return False

        from .agent_loop import run_agent_sync

        model_tier = getattr(task, "_model_tier", "fast")
        logger.info(f"[{task.workspace}] Tier 2 → agent_loop (tier={model_tier})")
        try:
            result = run_agent_sync(task=task.description, model_tier=model_tier, max_steps=5)
            success = not result.startswith("Error:")
            logger.info(f"[{task.workspace}] {'✅' if success else '⚠️'} Tier 2: {result[:100]}")
            return success
        except Exception as e:
            logger.error(f"[{task.workspace}] ❌ Tier 2 failed: {e}")
            return False

    def _alert(self, task: ScheduledTask, error: str):
        alert_file = self.mekong_dir / "jidoka-alerts.log"
        msg = f"[{datetime.now().isoformat()}] HEARTBEAT FAIL: {task.workspace}/{task.description}: {error}\n"
        with open(alert_file, "a") as f:
            f.write(msg)

    async def run_forever(self):
        """Main scheduler loop."""
        logger.info("HEARTBEAT Scheduler starting...")
        for ws_name, hb_path in self.discover_heartbeats():
            ws_tasks = self.parse_heartbeat(ws_name, hb_path)
            self.tasks.extend(ws_tasks)
            logger.info(f"Loaded {len(ws_tasks)} tasks from {ws_name}/HEARTBEAT.md")

        loop_tasks = self.discover_loops()
        self.tasks.extend(loop_tasks)
        if loop_tasks:
            logger.info(f"Loaded {len(loop_tasks)} autonomous ops loops")

        while True:
            now = datetime.now()
            due_tasks = [t for t in self.tasks if self.is_due(t, now)]
            if due_tasks:
                semaphore = asyncio.Semaphore(self.config.max_concurrent)

                async def run_with_limit(task):
                    async with semaphore:
                        await self.execute_task(task)

                await asyncio.gather(*[run_with_limit(t) for t in due_tasks])
            await asyncio.sleep(self.config.check_interval)


async def main():
    dry_run = "--dry-run" in sys.argv
    scheduler = HeartbeatScheduler()
    if dry_run:
        logger.info("=== DRY RUN MODE ===")
        for ws_name, hb_path in scheduler.discover_heartbeats():
            for t in scheduler.parse_heartbeat(ws_name, hb_path):
                logger.info(f"  [{ws_name}] {t.description} (every {t.interval_minutes}m, tier {t.tier})")
        loop_tasks = scheduler.discover_loops()
        for t in loop_tasks:
            logger.info(f"  [loop] {t.description} (every {t.interval_minutes}m, tier {t.tier})")
        return
    await scheduler.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

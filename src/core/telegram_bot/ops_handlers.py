"""Telegram bot ops handlers — heartbeat, alerts, health, schedule, swarm, memory."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class OpsHandlers:
    """Mixin providing operational command handlers."""

    async def schedule_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /schedule — list scheduled jobs."""
        from src.core.scheduler import Scheduler

        scheduler = Scheduler()
        jobs = scheduler.list_jobs()
        if not jobs:
            await update.message.reply_text("No scheduled jobs.")
            return

        lines = ["📅 *Scheduled Jobs*"]
        for j in jobs[:10]:
            lines.append(f"• {j.name}: {j.goal[:30]} ({j.job_type})")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def swarm_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /swarm — swarm node status."""
        from src.core.swarm import SwarmRegistry

        registry = SwarmRegistry()
        nodes = registry.list_nodes()
        if not nodes:
            await update.message.reply_text("No swarm nodes registered.")
            return

        lines = ["🐝 *Swarm Nodes*"]
        for n in nodes:
            lines.append(f"• {n.name} ({n.host}:{n.port}) — {n.status}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def memory_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /memory — recent 5 executions."""
        from src.core.memory import MemoryStore

        store = MemoryStore()
        entries = store.recent(5)
        if not entries:
            await update.message.reply_text("No memory entries yet.")
            return

        lines = ["🧠 *Recent Executions*"]
        for e in reversed(entries):
            icon = "✅" if e.status == "success" else "❌"
            lines.append(f"{icon} {e.goal[:30]} — {e.status}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def heartbeat_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /heartbeat — show next scheduled tasks."""
        from src.daemon.heartbeat_scheduler import HeartbeatScheduler

        scheduler = HeartbeatScheduler()
        lines = ["📋 *HEARTBEAT Schedule*\n"]
        for ws_name, hb_path in scheduler.discover_heartbeats():
            tasks = scheduler.parse_heartbeat(ws_name, hb_path)
            lines.append(f"*{ws_name}*: {len(tasks)} tasks")
            for t in tasks[:5]:
                interval = (
                    f"{t.interval_minutes}m"
                    if t.interval_minutes < 1440
                    else f"{t.interval_minutes // 1440}d"
                )
                lines.append(f"  [{interval}] {t.description}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def alerts_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /alerts — show recent Jidoka alerts."""
        alert_file = Path(".mekong/jidoka-alerts.log")
        if not alert_file.exists():
            await update.message.reply_text("✅ No alerts")
            return
        lines = alert_file.read_text().strip().split("\n")
        recent = lines[-10:] if len(lines) > 10 else lines
        await update.message.reply_text(
            "🚨 *Recent Alerts*\n\n" + "\n".join(recent),
            parse_mode="Markdown",
        )

    async def health_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /health — show platform health via PM2."""
        import subprocess

        result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
        if result.returncode != 0:
            await update.message.reply_text("⚠️ PM2 not running")
            return
        try:
            procs = json.loads(result.stdout)
            lines = ["🏥 *Platform Health*\n"]
            for p in procs:
                name = p.get("name", "?")
                status = p.get("pm2_env", {}).get("status", "?")
                emoji = "✅" if status == "online" else "❌" if status == "errored" else "⏸"
                mem_mb = p.get("monit", {}).get("memory", 0) / 1024 / 1024
                lines.append(f"{emoji} {name}: {status} ({mem_mb:.0f}MB)")
            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        except Exception:
            await update.message.reply_text("⚠️ Cannot parse PM2 status")

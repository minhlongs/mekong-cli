# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI - Telegram Bot Command Handlers."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Callable
from telegram import Update
from telegram.ext import ContextTypes
from .telegram_inbox import _load_inbox, add_task, get_pending_tasks

if TYPE_CHECKING:
    from src.core.orchestrator.models import OrchestrationResult

logger = logging.getLogger(__name__)


async def cook_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE, config: dict[str, object], save_config: Callable[..., None],
) -> None:
    goal = " ".join(context.args) if context.args else ""
    if not goal:
        await update.message.reply_text(
            "🦞 Usage: /cook <goal>\n\nExample:\n`/cook Build auth module for AgencyOS`\n`/cook Fix the landing page hero section`",
            parse_mode="Markdown",
        )
        return
    chat_id = update.effective_chat.id
    task = add_task(goal=goal, chat_id=chat_id)
    if chat_id not in config.chat_ids:
        config.chat_ids.append(chat_id)
        save_config()
    await update.message.reply_text(
        f"📨 *Task Queued for Mekong CLI!*\n\n🆔 `{task['id']}`\n🎯 Goal: _{goal}_\n"
        f"⏰ {task['created_at_iso']}\n\nMekong CLI will process and coordinate CC CLI.\nUse /tasks to check status.",
        parse_mode="Markdown",
    )


async def spawn_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE, config: dict[str, object], save_config: Callable[..., None],
) -> None:
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "🦞 Usage: /spawn <project> <goal>\n\nExample:\n`/spawn agencyos-web Add a dashboard sidebar`\n`/spawn openclaw-worker Fix Redis connection`",
            parse_mode="Markdown",
        )
        return
    project, goal, chat_id = args[0], " ".join(args[1:]), update.effective_chat.id
    task = add_task(goal=goal, project=project, chat_id=chat_id)
    if chat_id not in config.chat_ids:
        config.chat_ids.append(chat_id)
        save_config()
    await update.message.reply_text(
        f"📨 *Task Queued for `{project}`!*\n\n🆔 `{task['id']}`\n🎯 Goal: _{goal}_\n"
        f"📂 Project: `apps/{project}`\n\nMekong CLI will process and coordinate CC CLI.",
        parse_mode="Markdown",
    )


async def tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    inbox = _load_inbox()
    if not inbox:
        await update.message.reply_text("📭 Inbox empty.\nUse /cook <goal> to queue a task.")
        return
    icons = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌"}
    lines = ["📬 *Tôm Hùm Inbox*\n"]
    for t in inbox[-10:]:
        proj = t.get("project")
        lines.append(f"{icons.get(t.get('status', 'pending'), '❓')} `{t['id']}`{f' → `{proj}`' if proj else ''}\n   {t['goal'][:50]}\n   {t.get('created_at_iso', '')}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def sessions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        from src.core.cc_spawner import get_spawner
        sessions = get_spawner().all_sessions
        if not sessions:
            await update.message.reply_text("No CC CLI sessions.\nUse /cook <goal> to queue a task.")
            return
        icons = {"running": "🔄", "completed": "✅", "failed": "❌", "timeout": "⏰", "pending": "⏳"}
        lines = ["🦞 *Active CC CLI Sessions*\n"] + [
            f"{icons.get(s.status.value, '❓')} `{s.id}` — {s.status.value}\n   Goal: {s.goal[:40]}\n   Duration: {s.duration:.0f}s | Lines: {len(s.output_buffer)}"
            for s in sessions
        ]
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.warning("Failed to send Telegram session list reply: %s", e)
        await update.message.reply_text("No CC CLI sessions active.")


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from src.core.memory_canonical import MemoryStore
    stats = MemoryStore().stats()
    inbox_info = f"\n📬 Inbox: {len(get_pending_tasks())} pending"
    cc_info = ""
    try:
        from src.core.cc_spawner import get_spawner
        spawner = get_spawner()
        cc_info = f"\n🤖 CC CLI: {len(spawner.active_sessions)} active / {len(spawner.all_sessions)} total"
    except Exception as e:
        logger.warning("Operation failed: %s", e)
    text = f"🟢 *Tôm Hùm Status*\nExecutions: {stats['total']}\nSuccess Rate: {stats['success_rate']:.1f}%\nRecent Failures: {stats['recent_failures']}{inbox_info}{cc_info}"
    await update.message.reply_text(text, parse_mode="Markdown")


async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from src.core.scheduler import Scheduler
    jobs = Scheduler().list_jobs()
    if not jobs:
        await update.message.reply_text("No scheduled jobs.")
        return
    lines = ["📅 *Scheduled Jobs*"] + [f"• {j.name}: {j.goal[:30]} ({j.job_type})" for j in jobs[:10]]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def swarm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from src.core.swarm import SwarmRegistry
    nodes = SwarmRegistry().list_nodes()
    if not nodes:
        await update.message.reply_text("No swarm nodes registered.")
        return
    lines = ["🐝 *Swarm Nodes*"] + [f"• {n.name} ({n.host}:{n.port}) — {n.status}" for n in nodes]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def memory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from src.core.memory_canonical import MemoryStore
    entries = MemoryStore().recent(5)
    if not entries:
        await update.message.reply_text("No memory entries yet.")
        return
    lines = ["🧠 *Recent Executions*"] + [f"{'✅' if e.status == 'success' else '❌'} {e.goal[:30]} — {e.status}" for e in reversed(entries)]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from src.core.orchestrator import RecipeOrchestrator
    from src.providers.llm.client import get_client
    goal = " ".join(context.args) if context.args else ""
    if not goal:
        await update.message.reply_text("Usage: /cmd <goal>")
        return
    await update.message.reply_text(f"⏳ Executing: {goal}...")
    llm_client = get_client()
    orchestrator = RecipeOrchestrator(llm_client=llm_client if llm_client.is_available else None)
    await update.message.reply_text(_format_result(orchestrator.run_from_goal(goal)), parse_mode="Markdown")


def _format_result(result: "OrchestrationResult | None") -> str:
    if result is None:
        return "❌ Execution failed — no result"
    status = getattr(result, "status", None)
    if status is None:
        return f"Result: {result}"
    lines = [f"{'✅' if status.value == 'success' else '❌'} *Result: {status.value.upper()}*", f"Steps: {result.completed_steps}/{result.total_steps}", f"Success Rate: {result.success_rate:.0f}%"]
    if result.errors:
        lines.append(f"Errors: {'; '.join(result.errors[:3])}")
    return "\n".join(lines)


__all__ = ["_format_result", "cmd_handler", "cook_handler", "memory_handler", "schedule_handler", "sessions_handler", "spawn_handler", "status_handler", "swarm_handler", "tasks_handler"]

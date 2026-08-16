# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Telegram bot task relay handlers — /cook, /spawn, /tasks, /sessions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .inbox import _load_inbox, add_task

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class TaskHandlers:
    """Mixin providing task-relay command handlers."""

    async def cook_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cook <goal> — queue task for Mekong CLI."""
        goal = " ".join(context.args) if context.args else ""
        if not goal:
            await update.message.reply_text(
                "🦞 Usage: /cook <goal>\n\n"
                "Example:\n"
                "`/cook Build auth module for AgencyOS`\n"
                "`/cook Fix the landing page hero section`",
                parse_mode="Markdown",
            )
            return

        chat_id = update.effective_chat.id
        task = add_task(goal=goal, chat_id=chat_id)

        if chat_id not in self.config.chat_ids:
            self.config.chat_ids.append(chat_id)
            self._save_config()

        await update.message.reply_text(
            f"📨 *Task Queued for Mekong CLI!*\n\n"
            f"🆔 `{task['id']}`\n"
            f"🎯 Goal: _{goal}_\n"
            f"⏰ {task['created_at_iso']}\n\n"
            f"Mekong CLI will process and coordinate CC CLI.\n"
            f"Use /tasks to check status.",
            parse_mode="Markdown",
        )

    async def spawn_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /spawn <project> <goal> — queue task for specific project."""
        args = context.args or []
        if len(args) < 2:
            await update.message.reply_text(
                "🦞 Usage: /spawn <project> <goal>\n\n"
                "Example:\n"
                "`/spawn agencyos-web Add a dashboard sidebar`\n"
                "`/spawn openclaw-worker Fix Redis connection`",
                parse_mode="Markdown",
            )
            return

        project = args[0]
        goal = " ".join(args[1:])
        chat_id = update.effective_chat.id
        task = add_task(goal=goal, project=project, chat_id=chat_id)

        if chat_id not in self.config.chat_ids:
            self.config.chat_ids.append(chat_id)
            self._save_config()

        await update.message.reply_text(
            f"📨 *Task Queued for `{project}`!*\n\n"
            f"🆔 `{task['id']}`\n"
            f"🎯 Goal: _{goal}_\n"
            f"📂 Project: `apps/{project}`\n\n"
            f"Mekong CLI will process and coordinate CC CLI.",
            parse_mode="Markdown",
        )

    async def tasks_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /tasks — view pending tasks in inbox."""
        inbox = _load_inbox()

        if not inbox:
            await update.message.reply_text(
                "📭 Inbox empty.\nUse /cook <goal> to queue a task.",
            )
            return

        lines = ["📬 *Tôm Hùm Inbox*\n"]
        for t in inbox[-10:]:
            icon = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
            }.get(t.get("status", "pending"), "❓")

            project_str = f" → `{t['project']}`" if t.get("project") else ""
            lines.append(
                f"{icon} `{t['id']}`{project_str}\n"
                f"   {t['goal'][:50]}\n"
                f"   {t.get('created_at_iso', '')}",
            )

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def sessions_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /sessions — list active CC CLI terminals."""
        try:
            from src.core.cc_spawner import get_spawner

            spawner = get_spawner()
            sessions = spawner.all_sessions

            if not sessions:
                await update.message.reply_text(
                    "No CC CLI sessions.\nUse /cook <goal> to queue a task.",
                )
                return

            lines = ["🦞 *Active CC CLI Sessions*\n"]
            for s in sessions:
                icon = {
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "timeout": "⏰",
                    "pending": "⏳",
                }.get(s.status.value, "❓")

                lines.append(
                    f"{icon} `{s.id}` — {s.status.value}\n"
                    f"   Goal: {s.goal[:40]}\n"
                    f"   Duration: {s.duration:.0f}s | Lines: {len(s.output_buffer)}",
                )

            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        except Exception as e:
            logger.error("Sessions handler error: %s", e)
            await update.message.reply_text("No CC CLI sessions active.")

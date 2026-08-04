"""Telegram bot handlers — composes all handler mixins for MekongBot.

Provides NLP free-text dispatch, /cmd, /status, /help, and inline callback.
Task relay (/cook, /spawn, /tasks, /sessions) → TaskHandlers
Operations (/schedule, /swarm, /memory, /heartbeat, /alerts, /health) → OpsHandlers
AGI loop (/agi) → AgiHandlers
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from .agi_handlers import AgiHandlers
from .formatters import HELP_TEXT, build_keyboard, format_result
from .inbox import _load_inbox, _save_inbox, add_task, get_pending_tasks
from .ops_handlers import OpsHandlers
from .task_handlers import TaskHandlers

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class BotHandlers(TaskHandlers, AgiHandlers, OpsHandlers):
    """Mixin composing all Telegram command/message handlers."""

    # ----------------------------------------------------------------
    # NLP: Free-form message → Structured Command
    # ----------------------------------------------------------------

    async def nlp_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle ANY non-command text message via NLP parsing."""
        message = update.message.text
        if not message or len(message.strip()) < 3:
            return

        chat_id = update.effective_chat.id
        if chat_id not in self.config.chat_ids:
            self.config.chat_ids.append(chat_id)
            self._save_config()

        thinking_msg = await update.message.reply_text("🧠 Analyzing...")

        try:
            from src.core.nlp_commander import get_commander

            commander = get_commander()
            task = commander.parse(message)

            if task.parse_error:
                await thinking_msg.edit_text(
                    f"⚠️ Could not parse: {task.parse_error}\n\n"
                    f"Try using /cook <goal> directly.",
                )
                return

            if task.intent == "status":
                await thinking_msg.delete()
                await self.status_handler(update, context)
                return

            confirmation = commander.format_confirmation(task)
            inbox_task = add_task(
                goal=task.cc_cli_prompt,
                project=task.project,
                chat_id=chat_id,
            )
            # Enrich inbox with NLP metadata
            inbox = _load_inbox()
            for t in inbox:
                if t["id"] == inbox_task["id"]:
                    t["raw_message"] = task.raw_message
                    t["intent"] = task.intent
                    t["summary"] = task.summary
                    t["claudekit_commands"] = task.claudekit_commands
                    t["priority"] = task.priority
                    break
            _save_inbox(inbox)

            await thinking_msg.edit_text(
                f"{confirmation}\n\n"
                f"📨 Task `{inbox_task['id']}` queued!\n"
                f"Mekong CLI will process shortly.",
                parse_mode="Markdown",
            )

        except Exception as e:
            await thinking_msg.edit_text(
                f"❌ NLP error: {str(e)[:100]}\nTry /cook <goal> directly.",
            )

    # ----------------------------------------------------------------
    # Core handlers
    # ----------------------------------------------------------------

    async def cmd_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cmd <goal> — execute via orchestrator."""
        goal = " ".join(context.args) if context.args else ""
        if not goal:
            await update.message.reply_text("Usage: /cmd <goal>")
            return

        await update.message.reply_text(f"⏳ Executing: {goal}...")
        result = await asyncio.to_thread(self._execute_goal, goal)
        await update.message.reply_text(format_result(result), parse_mode="Markdown")

    async def status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status — system health."""
        from src.core.memory import MemoryStore

        store = MemoryStore()
        stats = store.stats()

        pending = len(get_pending_tasks())
        inbox_info = f"\n📬 Inbox: {pending} pending"

        cc_info = ""
        try:
            from src.core.cc_spawner import get_spawner

            spawner = get_spawner()
            active = len(spawner.active_sessions)
            total = len(spawner.all_sessions)
            cc_info = f"\n🤖 CC CLI: {active} active / {total} total"
        except Exception as e:
            logger.debug("CC spawner not available: %s", e)

        total_exec = stats["total"] if isinstance(stats, dict) else 0
        success_rate = stats["success_rate"] if isinstance(stats, dict) else 0.0
        recent_fail = stats["recent_failures"] if isinstance(stats, dict) else 0
        text = (
            f"🟢 *Tôm Hùm Status*\n"
            f"Executions: {total_exec}\n"
            f"Success Rate: {success_rate:.1f}%\n"
            f"Recent Failures: {recent_fail}"
            f"{inbox_info}"
            f"{cc_info}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help — show available commands."""
        kb = build_keyboard()
        await update.message.reply_text(
            HELP_TEXT,
            parse_mode="Markdown",
            reply_markup=kb,
        )

    async def _callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard button presses."""
        query = update.callback_query
        await query.answer()
        data = query.data or ""
        if data.startswith("cmd:"):
            action = data.split(":", 1)[1]
            mapping = {
                "cook": "/cook",
                "status": "/status",
                "memory": "/memory",
                "schedule": "/schedule",
                "tasks": "/tasks",
                "sessions": "/sessions",
            }
            await query.edit_message_text(f"Use: {mapping.get(action, data)}")

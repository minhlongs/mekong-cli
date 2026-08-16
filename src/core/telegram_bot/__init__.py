# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Telegram Commander Bot (Tôm Hùm Edition).

Remote command center via Telegram → LLM provider relay.
Commands received on Telegram are saved to inbox for Mekong CLI to process
and coordinate CC CLI execution.

Commands:
  /cook <goal>          — Queue task for Mekong CLI to execute
  /spawn <project> <g>  — Queue task targeting apps/<project>
  /tasks                — View pending tasks in inbox
  /sessions             — List active CC CLI terminals
  /status               — System health
  /schedule             — View scheduled jobs
  /help                 — This help message
"""

from .bot import BotConfig, MekongBot
from .formatters import HELP_TEXT, build_keyboard, format_result
from .inbox import (
    INBOX_PATH,
    _load_inbox,
    _save_inbox,
    add_task,
    get_pending_tasks,
    mark_task,
)

__all__ = [
    "HELP_TEXT",
    "INBOX_PATH",
    "BotConfig",
    "MekongBot",
    "_load_inbox",
    "_save_inbox",
    "add_task",
    "build_keyboard",
    "format_result",
    "get_pending_tasks",
    "mark_task",
]

"""Telegram bot formatters — message templates and keyboard builders."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import InlineKeyboardMarkup

    from src.core.orchestrator import OrchestrationResult

HELP_TEXT = """🦞 *Tôm Hùm — Telegram Commander*

*Autonomous Coding (via Mekong CLI):*
/cook <goal> — Queue task → Mekong CLI executes
/spawn <project> <goal> — Task for specific app
/tasks — View pending inbox
/sessions — Active CC CLI terminals

*Operations:*
/status — System health
/schedule — View scheduled jobs
/heartbeat — HEARTBEAT scheduler tasks
/alerts — Recent Jidoka alerts
/health — Platform health (PM2)
/memory — Recent 5 executions
/help — This help message

*AGI Self-Improvement:*
/agi start — Start AGI loop
/agi stop — Stop AGI loop
/agi status — Detailed AGI metrics
/agi history — Last 5 improvements
/agi config — Show AGI configuration

*Memory:*
/remember <content> — Store memory
"""


def format_result(result: OrchestrationResult | None) -> str:
    """Format OrchestrationResult for Telegram message."""
    if result is None:
        return "❌ Execution failed — no result"

    status = getattr(result, "status", None)
    if status is None:
        return f"Result: {result}"

    icon = "✅" if status.value == "success" else "❌"
    lines = [
        f"{icon} *Result: {status.value.upper()}*",
        f"Steps: {result.completed_steps}/{result.total_steps}",
        f"Success Rate: {result.success_rate:.0f}%",
    ]
    if result.errors:
        lines.append(f"Errors: {'; '.join(result.errors[:3])}")
    return "\n".join(lines)


def build_keyboard() -> InlineKeyboardMarkup | None:
    """Build inline keyboard for quick actions."""
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [
            [
                InlineKeyboardButton("🦞 Cook", callback_data="cmd:cook"),
                InlineKeyboardButton("📊 Status", callback_data="cmd:status"),
            ],
            [
                InlineKeyboardButton("📬 Tasks", callback_data="cmd:tasks"),
                InlineKeyboardButton("🧠 Memory", callback_data="cmd:memory"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    except ImportError:
        return None


__all__ = [
    "HELP_TEXT",
    "build_keyboard",
    "format_result",
]

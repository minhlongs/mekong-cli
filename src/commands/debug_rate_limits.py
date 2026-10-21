# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Debug Rate Limits CLI — ROIaaS Phase 4 Observability

Diagnostic CLI commands for debugging rate limit issues.
"""

from rich.console import Console
import typer

from src.commands.debug_rate_limits_history import (
    list_overrides,
    view_history,
)
from src.commands.debug_rate_limits_status import (
    _format_tier_display,
    _format_timestamp,
    check_status,
)
from src.commands.debug_rate_limits_violations import list_violations

console = Console()

app = typer.Typer(name="debug-rate-limits", help="Debug rate limit issues")

app.command("status")(check_status)
app.command("history")(view_history)
app.command("violations")(list_violations)
app.command("list-overrides")(list_overrides)

__all__ = [
    "_format_tier_display",
    "_format_timestamp",
    "app",
    "check_status",
    "console",
    "list_overrides",
    "list_violations",
    "view_history",
]

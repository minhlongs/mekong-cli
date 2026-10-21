# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth Middleware — CLI Command Authorization Middleware for Typer CLI."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Optional

from rich.console import Console

from src.core.command_authorizer import (
    AuthorizationReason,
    AuthorizationResult,
    CommandAuthorizer,
    get_authorizer,
)

if TYPE_CHECKING:
    import typer

logger = logging.getLogger(__name__)
console = Console()


class AuthMiddleware:
    """Middleware for CLI command authorization and post-command usage recording."""

    def __init__(self, authorizer: Optional[CommandAuthorizer] = None) -> None:
        self.authorizer = authorizer or get_authorizer()
        self._last_result: Optional[AuthorizationResult] = None

    def get_invoked_command(self, ctx: "typer.Context") -> str:
        """Extract invoked command from Typer context."""
        return ctx.invoked_subcommand or ""

    def pre_command_check(self, ctx: "typer.Context") -> None:
        """Pre-command authorization check before command execution."""
        command = self.get_invoked_command(ctx)
        if not command or "--help" in sys.argv or "-h" in sys.argv:
            return

        result = self.authorizer.authorize_command(command)
        self._last_result = result
        if not result.allowed:
            self._handle_authorization_failure(command, result)

    def post_command_check(self, command: str) -> None:
        """Post-command usage recording for metering."""
        if self._last_result and self._last_result.allowed:
            self.authorizer.record_usage(command, self._last_result)

    def _handle_authorization_failure(
        self, command: str, result: AuthorizationResult
    ) -> None:
        """Display authorization error details and exit with code 1 (unless in grace period)."""
        console.print("\n[bold red]🚫 Command Blocked[/bold red]")
        console.print(f"Command: [cyan]{command}[/cyan]\n")

        if result.reason == AuthorizationReason.INVALID_LICENSE:
            console.print("[red]Invalid or missing license.[/red]")
            console.print("\n[yellow]To activate your license:[/yellow]")
            console.print("  [cyan]mekong license-activation mk_your_key[/cyan]\n")
            console.print("[dim]Or set environment variable:[/dim]")
            console.print("  [cyan]export RAAS_LICENSE_KEY=mk_your_key[/cyan]\n")
        elif result.reason == AuthorizationReason.EXPIRED_LICENSE:
            console.print("[red]License has expired.[/red]")
            console.print("\n[yellow]To renew your license:[/yellow]")
            console.print("  [cyan]mekong renewal[/cyan]\n")
            console.print("[dim]Or visit: https://www.mekongmind.com[/dim]\n")
        elif result.reason == AuthorizationReason.QUOTA_EXCEEDED:
            console.print("[red]Rate limit exceeded.[/red]")
            if result.rate_limit_reset_in:
                console.print(
                    f"[dim]Please wait {result.rate_limit_reset_in} seconds before retrying.[/dim]\n"
                )
            console.print("\n[yellow]Upgrade your tier for higher limits:[/yellow]")
            console.print("  [cyan]https://www.mekongmind.com/pricing[/cyan]\n")
        elif result.reason == AuthorizationReason.INSUFFICIENT_TIER:
            console.print(f"[red]{result.message}[/red]")
            console.print("\n[yellow]Upgrade to access this command:[/yellow]")
            console.print("  [cyan]https://www.mekongmind.com/pricing[/cyan]\n")
        elif result.reason == AuthorizationReason.GRACE_PERIOD:
            console.print("[yellow]⚠️  Gateway Unavailable[/yellow]")
            console.print(f"{result.message}")
            console.print(
                "[dim]Command allowed under grace period. Gateway connection required soon.[/dim]\n"
            )
            return
        else:
            console.print(f"[red]{result.message or 'Authorization failed'}[/red]")

        sys.exit(1)

    def get_status(self) -> dict:
        """Get middleware status."""
        return self.authorizer.get_status()


_middleware: Optional[AuthMiddleware] = None


def get_middleware() -> AuthMiddleware:
    """Get global middleware instance."""
    global _middleware
    if _middleware is None:
        _middleware = AuthMiddleware()
    return _middleware


def reset_middleware() -> None:
    """Reset global middleware (for testing)."""
    global _middleware
    _middleware = None

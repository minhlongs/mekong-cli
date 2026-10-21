# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Graceful Shutdown Handler — ROIaaS Final Phase."""

import atexit
import glob
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)


class ShutdownReason(str, Enum):
    ALL_PHASES_OPERATIONAL = "all_phases_operational"
    USER_REQUESTED = "user_requested"
    ERROR = "error"
    SIGNAL_RECEIVED = "signal_received"
    MAINTENANCE = "maintenance"


@dataclass
class ShutdownContext:
    reason: ShutdownReason
    timestamp: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    cleanup_steps_completed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class GracefulShutdownHandler:
    def __init__(self) -> None:
        self.console = Console()
        self._shutdown_in_progress = False
        self._shutdown_context: Optional[ShutdownContext] = None
        self._cleanup_handlers: List[Callable[[], Awaitable[bool]]] = []
        self._final_callbacks: List[Callable[[], Awaitable[None]]] = []
        self._exit_code = 0
        atexit.register(self._on_exit)

    def register_cleanup_handler(self, handler: Callable[[], Awaitable[bool]], name: str = "") -> None:
        self._cleanup_handlers.append(handler)

    def register_final_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._final_callbacks.append(callback)

    async def initiate_shutdown(
        self, reason: ShutdownReason = ShutdownReason.ALL_PHASES_OPERATIONAL, details: Optional[Dict[str, Any]] = None,
    ) -> int:
        if self._shutdown_in_progress:
            self.console.print("[yellow]⚠ Shutdown already in progress...[/yellow]")
            return self._exit_code
        self._shutdown_in_progress = True
        self._shutdown_context = ShutdownContext(
            reason=reason, timestamp=datetime.now(timezone.utc).isoformat(), details=details or {},
        )
        self.console.print("\n" + "=" * 60)
        self.console.print(
            Panel(
                f"[bold yellow]Initiating Graceful Shutdown[/bold yellow]\n\n"
                f"[dim]Reason:[/dim] [cyan]{reason.value}[/cyan]\n[dim]Time:[/dim] {self._shutdown_context.timestamp}",
                title="🛑 SHUTDOWN SEQUENCE", border_style="yellow",
            )
        )
        for idx, handler in enumerate(self._cleanup_handlers):
            step_name = f"Cleanup handler {idx + 1}"
            try:
                self.console.print(f"[dim]⟳ {step_name}...[/dim]")
                if await handler():
                    self.console.print(f"[green]✓ {step_name} completed[/green]")
                    self._shutdown_context.cleanup_steps_completed.append(step_name)
                else:
                    self.console.print(f"[yellow]⚠ {step_name} returned failure[/yellow]")
                    self._shutdown_context.errors.append(f"{step_name} returned failure")
            except Exception as e:
                error_msg = f"{step_name} failed: {e}"
                self.console.print(f"[red]✗ {error_msg}[/red]")
                self._shutdown_context.errors.append(error_msg)

        for callback in self._final_callbacks:
            try:
                await callback()
            except Exception as e:
                self.console.print(f"[yellow]⚠ Final callback error: {e}[/yellow]")

        self._log_goodbye()
        self._exit_code = 0 if not self._shutdown_context.errors else 1
        return self._exit_code

    def _log_goodbye(self) -> None:
        ctx = self._shutdown_context
        if not ctx:
            return
        summary_lines = [
            f"[dim]Reason:[/dim] {ctx.reason.value}",
            f"[dim]Timestamp:[/dim] {ctx.timestamp}",
            f"[dim]Cleanup steps:[/dim] {len(ctx.cleanup_steps_completed)} completed",
            f"[dim]Errors:[/dim] {len(ctx.errors)}" if ctx.errors else "[green]✓ Clean shutdown[/green]",
        ]
        if "phases_status" in ctx.details:
            phases = ctx.details["phases_status"]
            op_count = sum(1 for p in phases.values() if p == "operational")
            summary_lines.append(f"[dim]Phases operational:[/dim] {op_count}/{len(phases)}")
        self.console.print("\n" + "=" * 60)
        self.console.print(
            Panel("\n".join(["[bold green]Goodbye![/bold green]", ""] + summary_lines), title="👋 SHUTDOWN COMPLETE", border_style="green")
        )
        self.console.print("=" * 60 + "\n")

    def _on_exit(self) -> None:
        if not self._shutdown_in_progress:
            self.console.print("\n[yellow]⚠ Process exiting without graceful shutdown...[/yellow]")

    def perform_sync_cleanup(self) -> None:
        self.console.print("[dim]Performing synchronous cleanup...[/dim]")
        sys.stdout.flush()
        sys.stderr.flush()


_shutdown_handler: Optional[GracefulShutdownHandler] = None


def get_shutdown_handler() -> GracefulShutdownHandler:
    global _shutdown_handler
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdownHandler()
    return _shutdown_handler


def reset_shutdown_handler() -> None:
    global _shutdown_handler
    _shutdown_handler = None


async def shutdown_on_all_phases_operational() -> None:
    from src.raas.phase_completion_detector import get_detector
    handler, detector = get_shutdown_handler(), get_detector()

    async def cleanup_temp_files() -> bool:
        for pattern in ("/tmp/tom_hum_*.txt", "/tmp/tom_hum_*", "/tmp/mekong_*.txt"):
            for filepath in glob.glob(pattern):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning("Shutdown cleanup failed: %s", e)
        return True

    handler.register_cleanup_handler(cleanup_temp_files, "cleanup_temp_files")
    await handler.initiate_shutdown(
        reason=ShutdownReason.ALL_PHASES_OPERATIONAL,
        details={"phases_status": {pid: info.status.value for pid, info in detector.get_all_phases_status().items()}},
    )
    sys.exit(handler._exit_code)


def register_shutdown_cleanup(name: str, cleanup_fn: Callable[[], Awaitable[bool]]) -> None:
    get_shutdown_handler().register_cleanup_handler(cleanup_fn, name)


__all__ = [
    "GracefulShutdownHandler", "ShutdownContext", "ShutdownReason", "get_shutdown_handler",
    "register_shutdown_cleanup", "reset_shutdown_handler", "shutdown_on_all_phases_operational",
]

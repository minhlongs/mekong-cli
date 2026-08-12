"""Mekong CLI 7 — `omni` command: 24/7 daemon + config + status."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from ..core.omni import omni_config_cmd, omni_loop, omni_status

console = Console()


def omni_run_cmd(
    once: bool = typer.Option(False, "--once", help="Run one loop then exit"),
) -> None:
    """Run the 24/7 Omni daemon (SOP scheduler + healthcheck)."""
    omni_loop(once=once)


def omni_status_cmd() -> None:
    """Show daemon state, last runs, config."""
    omni_status()


def omni_config(
    sop: Optional[str] = typer.Option(None, "--sop", help="SOP name to schedule"),
    interval: int = typer.Option(0, "--interval", help="Interval minutes (>=5)"),
    dry_run: Optional[bool] = typer.Option(None, "--dry-run/--no-dry-run", help="Toggle dry_run"),
    loop_dry_run: Optional[bool] = typer.Option(None, "--loop-dry-run/--no-loop-dry-run",
                                                help="OPC cycle: DRY hay LIVE"),
    auto_build: Optional[bool] = typer.Option(None, "--auto-build/--no-auto-build",
                                              help="BUILD phase gọi orchestrate thật"),
    live_sop: Optional[list[str]] = typer.Option(None, "--live-sop",
                                                 help="SOP name chạy không dry-run (canary, lặp được)"),
    loop_interval: Optional[float] = typer.Option(None, "--loop-interval",
                                                  help="OPC cycle cadence (giờ)"),
    reset: bool = typer.Option(False, "--reset", help="Reset to defaults"),
) -> None:
    """Configure the Omni daemon schedule."""
    if interval and interval < 5:
        console.print("[red]interval must be >= 5[/]")
        raise typer.Exit(1)
    omni_config_cmd(sop_name=sop or "", interval=interval, dry_run=dry_run,
                    loop_dry_run=loop_dry_run, auto_build=auto_build,
                    live_sop=live_sop or [], loop_interval=loop_interval, reset=reset)

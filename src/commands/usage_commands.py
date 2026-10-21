# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Usage Tracking CLI Commands — ROIaaS Phase 4

Commands for tracking and reporting CLI command usage per license key.
"""

import os
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.commands.usage_commands_helpers import (
    render_usage_report,
    write_usage_export,
)

console = Console()

app = typer.Typer(
    name="usage",
    help="📊 Usage tracking and reporting",
    rich_markup_mode="rich",
)


@app.command(name="report")
def usage_report(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to report"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Export as JSON"),
    license_key: Optional[str] = typer.Option(
        None,
        "--license",
        "-l",
        help="License key (defaults to RAAS_LICENSE_KEY env var)",
    ),
) -> None:
    """
    📊 Show CLI usage report with command counts and free tier status.
    """
    current_license = license_key or os.getenv("RAAS_LICENSE_KEY")
    if not current_license:
        console.print(
            Panel(
                "[bold red]✗ No license key found[/bold red]\n\n"
                "Set [green]RAAS_LICENSE_KEY[/green] environment variable or use [green]--license[/green] flag.",
                title="License Required",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    try:
        from src.raas.credit_metering_middleware import CreditMeter

        meter = CreditMeter()
        summary = meter.get_usage_summary(current_license, period="daily")
        render_usage_report(current_license, summary, days, json_output)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print(
            "[dim]Note: Usage tracking requires RaaS billing to be initialized.[/dim]"
        )
        raise typer.Exit(code=1)


@app.command(name="check")
def usage_check(
    license_key: Optional[str] = typer.Option(
        None,
        "--license",
        "-l",
        help="License key (defaults to RAAS_LICENSE_KEY env var)",
    ),
) -> None:
    """
    ⚡ Quick check if license has remaining free tier quota.

    Returns exit code 0 if quota available, 1 if exceeded.
    """
    current_license = license_key or os.getenv("RAAS_LICENSE_KEY")
    if not current_license:
        console.print("[bold red]✗ No license key[/bold red]")
        raise typer.Exit(code=1)

    try:
        from src.raas.credit_metering_middleware import CreditMeter

        meter = CreditMeter()
        balance = meter._credit_store.get_balance(current_license)

        if balance > 0:
            console.print("[bold green]✓ Quota Available[/bold green]")
            console.print(f"Remaining Credits: [green]{balance} MCU[/green]")
            raise typer.Exit(code=0)
        else:
            console.print("[bold red]✗ Quota Exceeded[/bold red]")
            console.print("Remaining Credits: [red]0 MCU[/red]")
            console.print("[dim]Upgrade tier or wait for monthly reset.[/dim]")
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="export")
def usage_export(
    output: str = typer.Option(
        "~/.mekong/raas/usage-export.json",
        "--output",
        "-o",
        help="Output file path",
    ),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to export"),
    license_key: Optional[str] = typer.Option(
        None,
        "--license",
        "-l",
        help="License key (defaults to RAAS_LICENSE_KEY env var)",
    ),
) -> None:
    """
    📤 Export usage data to JSON file.

    Exports detailed usage events for external analysis or reporting.
    """
    current_license = license_key or os.getenv("RAAS_LICENSE_KEY")
    if not current_license:
        console.print("[bold red]✗ No license key[/bold red]")
        raise typer.Exit(code=1)

    try:
        from src.raas.credit_metering_middleware import CreditMeter

        meter = CreditMeter()
        events = meter.list_events(current_license, limit=1000)
        write_usage_export(current_license, events, output, days)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


__all__ = [
    "Console",
    "Panel",
    "Table",
    "app",
    "console",
    "datetime",
    "usage_check",
    "usage_export",
    "usage_report",
]

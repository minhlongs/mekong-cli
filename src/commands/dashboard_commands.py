# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong Dashboard CLI Commands

Analytics dashboard visualization and export.
"""

from datetime import datetime, timedelta
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.commands.dashboard_summary_helper import (
    run_export_data,
    run_status_check,
    run_summary_display,
)

console = Console()

app = typer.Typer(
    name="dashboard",
    help="📊 Analytics Dashboard",
    rich_markup_mode="rich",
)


@app.command("launch")
def launch_dashboard(
    port: int = typer.Option(8080, "--port", "-p", help="Server port"),
    no_browser: bool = typer.Option(
        False, "--no-browser", "-n", help="Don't open browser automatically"
    ),
    host: str = typer.Option(
        "127.0.0.1", "--host", "-h", help="Bind host (default: 127.0.0.1)"
    ),
) -> None:
    """
    🚀 Launch analytics dashboard server.

    Opens a web dashboard at http://localhost:<port> with real-time
    analytics for API usage, license health, and revenue tracking.
    """
    console.print(f"""
[bold cyan]📊 Mekong Analytics Dashboard[/bold cyan]

Starting server on [green]http://{host}:{port}[/green]

[dim]• API docs: http://{host}:{port}/api/docs[/dim]
[dim]• Dashboard: http://{host}:{port}[/dim]
[dim]• Press Ctrl+C to stop the server[/dim]
""")

    try:
        from src.api.dashboard.app import run_dashboard as _start_dashboard

        _start_dashboard(port=port, open_browser=not no_browser, host=host)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("status")
def dashboard_status() -> None:
    """
    ❤️ Check dashboard health and data availability.

    Verifies database connection, cache status, and data freshness.
    """
    run_status_check()


@app.command("export")
def export_dashboard_data(
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv or json"),
    output: str = typer.Option(..., "--output", "-o", help="Output file path"),
    start_date: Optional[str] = typer.Option(
        None, "--start", "-s", help="Start date (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = typer.Option(
        None, "--end", "-e", help="End date (YYYY-MM-DD)"
    ),
    license_key: Optional[str] = typer.Option(
        None, "--key", "-k", help="Filter by license key"
    ),
    days: int = typer.Option(
        30, "--days", "-d", help="Number of days (if start/end not specified)"
    ),
) -> None:
    """
    💾 Export analytics data to CSV or JSON.

    Export API usage, license data, and revenue metrics.
    """
    run_export_data(
        format=format,
        output=output,
        start_date=start_date,
        end_date=end_date,
        license_key=license_key,
        days=days,
    )


@app.command("summary")
def dashboard_summary() -> None:
    """
    📋 Show quick analytics summary in terminal.

    Display key metrics without launching the web dashboard.
    """
    run_summary_display()


def run_dashboard(
    port: int = 8080,
    no_browser: bool = False,
    host: str = "127.0.0.1",
) -> None:
    """Helper function to run dashboard (for backwards compatibility)."""
    launch_dashboard(port=port, no_browser=no_browser, host=host)


__all__ = [
    "Console",
    "Table",
    "app",
    "console",
    "dashboard_status",
    "dashboard_summary",
    "datetime",
    "export_dashboard_data",
    "launch_dashboard",
    "run_dashboard",
    "timedelta",
]

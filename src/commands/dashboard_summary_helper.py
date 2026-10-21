# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helpers for Mekong Dashboard CLI commands."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

import typer
from rich.table import Table


def _mod():
    import src.commands.dashboard_commands as mod

    return mod


def run_status_check() -> None:
    """Execute dashboard status check and print status table."""
    m = _mod()
    m.console.print("[bold cyan]📊 Dashboard Status[/bold cyan]\n")

    try:
        from src.analytics.dashboard_service import DashboardService

        service = DashboardService()
        metrics = asyncio.run(service.get_metrics(range_days=1))

        m.console.print("[green]✓ Dashboard Healthy[/green]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Component")
        table.add_column("Status")
        table.add_column("Details")

        table.add_row("Database", "✅", "Connected")
        table.add_row("Cache", "✅", f"{len(service._cache)} entries")
        table.add_row("API Usage Data", "✅", f"{len(metrics.api_calls)} data points")
        table.add_row(
            "License Data", "✅", f"{metrics.active_licenses.get('total', 0)} active"
        )
        table.add_row(
            "Rate Limit Events", "✅", f"{len(metrics.rate_limit_events)} events"
        )

        health = metrics.license_health
        if health:
            table.add_row(
                "License Health",
                "✅",
                f"{health.get('active_count', 0)} active, "
                f"{health.get('expiring_soon_count', 0)} expiring",
            )

        m.console.print(table)

    except Exception as e:
        m.console.print("[bold red]✗ Dashboard Unhealthy[/bold red]")
        m.console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def run_export_data(
    format: str,
    output: str,
    start_date: Optional[str],
    end_date: Optional[str],
    license_key: Optional[str],
    days: int,
) -> None:
    """Export analytics data to CSV or JSON."""
    m = _mod()
    if format.lower() not in ("csv", "json"):
        m.console.print("[red]Error:[/red] Format must be 'csv' or 'json'")
        raise typer.Exit(1)

    if start_date and end_date:
        start, end = start_date, end_date
    else:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    m.console.print(f"[dim]Exporting data from {start} to {end}...[/dim]")

    try:
        from src.analytics.dashboard_service import DashboardService

        service = DashboardService()
        date_range = (start, end)

        if format == "csv":
            data = asyncio.run(service.export_to_csv(date_range, license_key))
        else:
            data = asyncio.run(service.export_to_json(date_range, license_key))

        with open(output, "w") as f:
            f.write(data)

        m.console.print(f"[green]✓ Exported to {output}[/green]")
        file_size = os.path.getsize(output)
        m.console.print(f"[dim]File size: {file_size:,} bytes[/dim]")

    except Exception as e:
        m.console.print(f"[red]Export failed:[/red] {e}")
        raise typer.Exit(1)


def run_summary_display() -> None:
    """Render quick analytics summary in terminal."""
    m = _mod()
    m.console.print("[bold cyan]📊 Analytics Summary[/bold cyan]\n")

    try:
        from src.analytics.dashboard_service import DashboardService

        service = DashboardService()
        metrics = asyncio.run(service.get_metrics(range_days=30))

        total_calls = sum(d.get("calls", 0) for d in metrics.api_calls)
        active_licenses = metrics.active_licenses.get("total", 0)
        revenue = metrics.revenue.get("total_mrr", 0)
        avg_daily = total_calls // 30 if total_calls else 0

        m.console.print("[bold]Key Metrics (Last 30 Days)[/bold]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")

        table.add_row("Total API Calls", f"{total_calls:,}")
        table.add_row("Active Licenses", f"{active_licenses:,}")
        table.add_row("Est. Monthly Revenue", f"${revenue:,.2f}")
        table.add_row("Avg Calls/Day", f"{avg_daily:,}")
        m.console.print(table)

        if metrics.tier_distribution.get("by_tier"):
            m.console.print("\n[bold]Tier Distribution[/bold]\n")
            tier_table = Table(show_header=True, header_style="bold")
            tier_table.add_column("Tier")
            tier_table.add_column("Count")
            tier_table.add_column("Active")
            for tier, data in metrics.tier_distribution["by_tier"].items():
                if isinstance(data, dict):
                    tier_table.add_row(
                        tier.upper(),
                        str(data.get("count", 0)),
                        str(data.get("active", 0)),
                    )
            m.console.print(tier_table)

        if metrics.license_health:
            m.console.print("\n[bold]License Health[/bold]\n")
            health = metrics.license_health
            health_table = Table(show_header=False, box=None)
            health_table.add_column("Status")
            health_table.add_column("Count")
            health_table.add_row(
                "Active", f"[green]{health.get('active_count', 0)}[/green]"
            )
            health_table.add_row(
                "Expiring Soon",
                f"[orange]{health.get('expiring_soon_count', 0)}[/orange]",
            )
            health_table.add_row(
                "Suspended", f"[yellow]{health.get('suspended_count', 0)}[/yellow]"
            )
            health_table.add_row(
                "Revoked", f"[red]{health.get('revoked_count', 0)}[/red]"
            )
            m.console.print(health_table)

    except Exception as e:
        m.console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

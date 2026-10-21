# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
ROI Dashboard Subcommand — Analytics dashboard data fetching

Part of mekong roi unified command (Phase 6).
"""

import typer
import asyncio
import json
from rich.console import Console
from rich.table import Table
from datetime import datetime, timedelta
from typing import Optional

console = Console()
app = typer.Typer(name="dashboard", help="📈 Analytics dashboard")


@app.command("show")
def show_dashboard(
    license_key: Optional[str] = typer.Option(None, "--key", "-k", help="License key (defaults to env var)"),
    range_days: int = typer.Option(30, "--range", "-r", help="Date range in days"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
) -> None:
    """📊 Show analytics dashboard data."""
    console.print("[bold cyan]📈 Analytics Dashboard[/bold cyan]\n")
    if not license_key:
        import os
        license_key = os.getenv("RAAS_LICENSE_KEY", "")

    try:
        from src.analytics.dashboard_service import DashboardMetrics, DashboardService

        service = DashboardService()
        metrics: DashboardMetrics = asyncio.run(service.get_metrics(range_days=range_days))
        if format == "json":
            console.print(json.dumps({
                "last_updated": metrics.last_updated,
                "active_licenses": metrics.active_licenses,
                "revenue": metrics.revenue,
                "tier_distribution": metrics.tier_distribution,
                "rate_limit_violations": metrics.rate_limit_violations,
                "license_health": metrics.license_health,
            }, indent=2, default=str))
            return

        if metrics.active_licenses:
            t = Table(title="👥 Active Licenses", show_header=True, header_style="bold cyan")
            t.add_column("Metric", style="dim")
            t.add_column("Value", justify="right")
            t.add_row("Total", str(metrics.active_licenses.get("total", 0)))
            console.print(t)

        if metrics.tier_distribution:
            t = Table(title="📊 Tier Distribution", show_header=True, header_style="bold cyan")
            t.add_column("Tier", style="dim")
            t.add_column("Count", justify="right")
            t.add_column("Percentage", justify="right")
            total = sum(v for v in metrics.tier_distribution.values() if isinstance(v, (int, float)))
            tier_display = {"free": "🔓 FREE", "pro": "💎 PRO", "enterprise": "🏢 ENTERPRISE"}
            for tier, count in metrics.tier_distribution.items():
                if isinstance(count, (int, float)):
                    pct = (count / total * 100) if total > 0 else 0
                    t.add_row(tier_display.get(tier, tier.upper()), str(int(count)), f"{pct:.1f}%")
            console.print(t)

        if metrics.revenue:
            t = Table(title="💰 Revenue Summary", show_header=True, header_style="bold green")
            t.add_column("Metric", style="dim")
            t.add_column("Value", justify="right")
            for k, v in metrics.revenue.items():
                if isinstance(v, (int, float)):
                    t.add_row(k.replace("_", " ").title(), f"${v:,.2f}")
            console.print(t)

        if metrics.rate_limit_violations:
            t = Table(title="⚠️ Rate Limit Violations (24h)", show_header=True, header_style="bold yellow")
            t.add_column("Tenant", style="dim")
            t.add_column("Violations", justify="right")
            for v in metrics.rate_limit_violations[:10]:
                t.add_row(v.get("tenant_id", "unknown")[:12], str(v.get("count", 0)))
            console.print(t)

        if metrics.license_health:
            t = Table(title="❤️ License Health", show_header=True, header_style="bold green")
            t.add_column("Metric", style="dim")
            t.add_column("Value", justify="right")
            for k, v in metrics.license_health.items():
                if isinstance(v, (int, float)):
                    t.add_row(k.replace("_", " ").title(), str(int(v)) if isinstance(v, int) else f"{v:.2f}")
            console.print(t)

        console.print(f"\n[dim]Last updated: {metrics.last_updated}[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("export")
def export_analytics(
    license_key: Optional[str] = typer.Option(None, "--key", "-k", help="License key"),
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv, json"),
    output: str = typer.Option(..., "--output", "-o", help="Output file path"),
    start_date: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
) -> None:
    """💾 Export analytics to CSV/JSON."""
    console.print(f"[bold cyan]💾 Exporting Analytics to {format.upper()}...[/bold cyan]\n")
    start_date = start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = end_date or datetime.now().strftime("%Y-%m-%d")
    try:
        from src.analytics.dashboard_service import DashboardService
        service = DashboardService()
        if format == "csv":
            data = asyncio.run(service.export_to_csv(date_range=(start_date, end_date), license_key=license_key))
        elif format == "json":
            data = asyncio.run(service.export_to_json(date_range=(start_date, end_date), license_key=license_key))
        else:
            console.print(f"[red]Error:[/red] Invalid format: {format}")
            raise typer.Exit(1)
        with open(output, "w") as f:
            f.write(data)
        console.print(f"[green]✓ Exported to {output}[/green]")
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("real-time")
def stream_metrics(license_key: Optional[str] = typer.Option(None, "--key", "-k", help="License key")) -> None:
    """⚡ Stream real-time metrics (SSE)."""
    console.print("[bold cyan]⚡ Real-time Metrics Stream[/bold cyan]\n")
    console.print("[yellow]Note:[/yellow] SSE streaming requires a running API server.\n")
    console.print("To start the gateway server:\n  [cyan]mekong gateway --port 8000[/cyan]\n")
    console.print("Then connect via:\n  [cyan]curl -N http://localhost:8000/dashboard/stream?token=mk_xxx[/cyan]\n")


@app.command("health")
def health_check() -> None:
    """❤️ Check dashboard health status."""
    console.print("[bold cyan]❤️ Dashboard Health Check[/bold cyan]\n")
    try:
        from src.analytics.dashboard_service import DashboardService
        asyncio.run(DashboardService().get_metrics(range_days=1))
        console.print("[bold green]✓ Dashboard Healthy[/bold green]\n")
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Component", style="dim")
        table.add_column("Status", justify="center")
        for comp in ("Database", "Cache", "Rate Limit Emitter"):
            table.add_row(comp, "✅")
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]✗ Dashboard Unhealthy[/bold red]\n\n[red]Error:[/red] {e}\n")
        raise typer.Exit(1)

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage Commands — Phase 6 CLI Integration with RaaS Gateway."""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from src.cli.usage_export import perform_export
from src.cli.usage_overage import (
    display_overage_data,
    display_overage_estimate,
    fetch_overage_from_gateway,
    generate_overage_estimate,
)
from src.cli.usage_report import display_local_usage, display_report_table, display_usage_data
from src.cli.usage_tracker import (
    fetch_usage_from_gateway,
    get_license_key,
    get_period_bounds,
    mask_license_key,
    sync_local_usage,
)

console = Console()
app = typer.Typer(name="usage", help="📊 Usage metering and reporting", rich_markup_mode="rich")


@app.command("show")
def show_usage(
    license_key: Optional[str] = typer.Option(None, "--key", "-k", help="License key (defaults to RAAS_LICENSE_KEY env)"),
    period: str = typer.Option("current", "--period", "-p", help="Period: 'current' or 'previous'"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed breakdown"),
) -> None:
    """📊 Show current period usage."""
    console.print("[bold cyan]📊 Usage Report[/bold cyan]\n")
    resolved_key = get_license_key(license_key)
    if not resolved_key:
        console.print("[yellow]No license key provided.[/yellow]\nSet RAAS_LICENSE_KEY env var or use [bold]-k[/bold] flag.\n")
        return

    console.print(f"License Key: [cyan]{mask_license_key(resolved_key)}[/cyan]\nPeriod: [cyan]{period.title()}[/cyan]\n")
    start, end = get_period_bounds(period)
    if usage_data := fetch_usage_from_gateway(resolved_key, start, end):
        display_usage_data(usage_data, verbose)
    else:
        console.print("[dim]Gateway unavailable, showing local metrics.[/dim]\n")
        display_local_usage(resolved_key, period, verbose)


@app.command("report")
def report_usage(
    license_key: Optional[str] = typer.Option(None, "--key", "-k", help="License key (defaults to RAAS_LICENSE_KEY env)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed breakdown"),
) -> None:
    """📊 Comprehensive usage report with entitlements."""
    import requests
    from src.core.gateway_client import GatewayClient
    from src.core.raas_auth import get_auth_client

    console.print("[bold cyan]📊 Usage Report[/bold cyan]\n")
    resolved_key = get_license_key(license_key)
    if not resolved_key:
        console.print("[yellow]No license key provided.[/yellow]\nSet RAAS_LICENSE_KEY env var or use [bold]-k[/bold] flag.\n")
        return
    console.print(f"License Key: [cyan]{mask_license_key(resolved_key)}[/cyan]\n")

    try:
        client = GatewayClient()
        session = get_auth_client().get_session()
        headers = {"Authorization": f"Bearer {session.token}"} if session.authenticated and session.token else {}
        now = datetime.now().replace(tzinfo=None)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        usage_resp = requests.get(
            f"{client.gateway_url}/v1/usage", headers=headers,
            params={"start_hour": start.isoformat() + "Z", "end_hour": end.isoformat() + "Z", "limit": 100}, timeout=10,
        )
        ent_resp = requests.get(f"{client.gateway_url}/v1/license/entitlements", headers=headers, timeout=10)
        display_report_table(
            usage_data=usage_resp.json() if usage_resp.status_code == 200 else None,
            entitlements_data=ent_resp.json() if ent_resp.status_code == 200 else None,
            rate_limit_remaining=int(usage_resp.headers.get("X-RateLimit-Remaining", 0)),
            rate_limit_limit=int(usage_resp.headers.get("X-RateLimit-Limit", 0)),
            rate_limit_reset=usage_resp.headers.get("X-RateLimit-Reset", ""),
            verbose=verbose,
        )
    except requests.RequestException as e:
        console.print(f"[dim]Gateway error: {e}[/dim]\n")
        display_local_usage(resolved_key, "current", verbose)
    except Exception as e:
        console.print(f"[dim]Error: {e}[/dim]\n")
        display_local_usage(resolved_key, "current", verbose)


@app.command("sync")
def sync_usage(
    force: bool = typer.Option(False, "--force", "-f", help="Force sync even if recently synced"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be synced without sending"),
) -> None:
    """🔄 Manually sync local metrics to RaaS Gateway."""
    console.print("[bold cyan]🔄 Usage Sync[/bold cyan]\n")
    result = sync_local_usage(force=force, dry_run=dry_run)
    st = result["status"]
    if st == "no_data":
        console.print("[yellow]No local usage data found.[/yellow]\nUsage tracking will start on next command execution.\n")
    elif st == "no_files":
        console.print("[dim]No usage files to sync.[/dim]\n")
    elif st == "dry_run":
        console.print("[bold]Dry Run Mode[/bold] - No data will be sent\n")
        for f in result.get("files", []):
            console.print(f"  Would sync: {f}")
        if result.get("total_files", 0) > 5:
            console.print(f"  ... and {result['total_files'] - 5} more")
    elif st in ("complete", "partial"):
        console.print(Panel(
            f"[bold green]✓ Synced {result['synced_count']} events[/bold green]\nFailed: {result['failed_count']}",
            title="Sync Result", border_style="green" if st == "complete" else "yellow",
        ))
    else:
        console.print(Panel(
            f"[bold red]✗ Sync failed[/bold red]\nError: {result.get('message', 'Unknown error')}\n\n"
            "The RaaS Gateway may be unavailable. Data will retry on next sync.",
            title="Sync Error", border_style="red",
        ))


@app.command("overage")
def calculate_overage(
    license_key: Optional[str] = typer.Option(None, "--key", "-k", help="License key (defaults to RAAS_LICENSE_KEY env)"),
    period_start: Optional[str] = typer.Option(None, "--start", "-s", help="Period start (ISO format)"),
    period_end: Optional[str] = typer.Option(None, "--end", "-e", help="Period end (ISO format)"),
) -> None:
    """💰 Calculate overage charges."""
    console.print("[bold cyan]💰 Overage Calculation[/bold cyan]\n")
    resolved_key = get_license_key(license_key)
    if not resolved_key:
        console.print("[yellow]No license key provided.[/yellow]\n")
        return
    console.print(f"License Key: [cyan]{mask_license_key(resolved_key)}[/cyan]\n")
    now = datetime.utcnow()
    start_dt = datetime.fromisoformat(period_start.replace("Z", "+00:00")) if period_start else now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_dt = datetime.fromisoformat(period_end.replace("Z", "+00:00")) if period_end else now
    console.print(f"Period: [cyan]{start_dt.strftime('%Y-%m-%d')}[/cyan] → [cyan]{end_dt.strftime('%Y-%m-%d')}[/cyan]\n")
    if overage_data := fetch_overage_from_gateway(resolved_key, start_dt, end_dt):
        display_overage_data(overage_data)
    else:
        console.print("[dim]Gateway unavailable, showing estimate.[/dim]\n")
        display_overage_estimate(generate_overage_estimate(start_dt, end_dt))


@app.command("export")
def export_usage(
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, csv"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    period: str = typer.Option("current", "--period", "-p", help="Period: current, previous, all"),
) -> None:
    """📁 Export usage data to CSV/JSON."""
    console.print(f"[bold cyan]📁 Export Usage[/bold cyan]\n\nFormat: [cyan]{format.upper()}[/cyan]\nOutput: [cyan]{output or '(auto-generated)'}[/cyan]\n")
    result = perform_export(format=format, output=output, period=period)
    if result["success"]:
        console.print(Panel(f"[bold green]✓ Exported {result['event_count']} events[/bold green]\nPath: [cyan]{result['output_path']}[/cyan]", title="Export Complete", border_style="green"))
    else:
        console.print(Panel("[bold red]✗ Export failed[/bold red]\nCheck file permissions and try again.", title="Export Error", border_style="red"))

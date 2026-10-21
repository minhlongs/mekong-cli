# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong Sync CLI Command — RaaS Usage Metrics Synchronization."""

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.sync_commands_helpers import (
    _display_rate_limit_state, _display_summary, show_entitlement, sync_encrypted,
)

console = Console()
app = typer.Typer(help="🔄 RaaS usage metrics synchronization")


@app.command()
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Calculate metrics but don't upload"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed metrics"),
) -> None:
    """Synchronize local usage metrics with RaaS Gateway."""
    from src.raas.sync_client import get_sync_client

    console.print("[bold cyan]🔄 Mekong Sync - RaaS Gateway[/bold cyan]\n[dim]Step 1/3: Validating license...[/dim]")
    client = get_sync_client()
    is_valid, error = client.validate_license()
    if not is_valid:
        console.print(f"[bold red]✗ License validation failed[/bold red]\n[red]{error}[/red]\n")
        console.print("[yellow]Get a license key:[/yellow]\n  [cyan]https://api.cashclaw.cc[/cyan]\n")
        console.print("[dim]Or set environment variable:[/dim]\n  [cyan]export RAAS_LICENSE_KEY=mk_your_key[/cyan]\n")
        raise SystemExit(1)

    console.print("[green]✓ License valid[/green]\n[dim]Step 2/3: Collecting local metrics...[/dim]")
    summary = client.get_usage_summary()
    if summary.total_requests == 0:
        console.print("[yellow]⚠ No local metrics found[/yellow]\n[dim]Usage metrics are collected automatically during CLI usage.[/dim]\n")
        console.print("[dim]Dry run complete.[/dim]\n" if dry_run else "[dim]Run some commands first, then sync again.[/dim]\n")
        return

    console.print(f"[green]✓ Found {summary.total_requests} requests[/green]\n")
    if dry_run:
        console.print("[dim]Step 3/3: Dry run (skipping upload)...[/dim]")
        result = client.sync_metrics(dry_run=True)
        console.print("[green]✓ Dry run complete[/green]\n")
    else:
        console.print("[dim]Step 3/3: Syncing to RaaS Gateway...[/dim]")
        result = client.sync_metrics()
        if not result.success:
            console.print(f"[bold red]✗ Sync failed[/bold red]\n[red]{result.error}[/red]\n")
            if result.rate_limit_reset_in:
                console.print(f"[dim]Rate limit resets in {result.rate_limit_reset_in}s[/dim]\n")
            raise SystemExit(1)
        console.print(f"[green]✓ Synced {result.synced_count} requests[/green]\n")

    _display_summary(summary, result, verbose)


@app.command("status")
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status"),
) -> None:
    """Show sync status without uploading."""
    from src.raas.sync_client import get_sync_client

    console.print("[bold cyan]📊 Sync Status[/bold cyan]\n")
    client = get_sync_client()
    status_info = client.get_sync_status()

    if status_info["license_valid"]:
        console.print("[green]✓ License valid[/green]\n")
    else:
        console.print(f"[bold red]✗ License invalid[/bold red]\n[red]{status_info['license_error']}[/red]\n")

    table = Table(title="📊 Local Metrics", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Total Requests", str(status_info["metrics_count"]))
    table.add_row("Total Payload", f"{status_info['total_payload_size']:,} bytes")
    table.add_row("Hours Active", str(status_info["hours_active"]))
    if status_info["peak_hour"]:
        table.add_row("Peak Hour", f"{status_info['peak_hour']} ({status_info['peak_requests']} requests)")
    console.print(table)
    console.print()

    if status_info["circuit_breakers"]:
        circuit_table = Table(title="🔌 Circuit Breakers")
        for col, st in [("Gateway", "cyan"), ("State", "green"), ("Failures", "white")]:
            circuit_table.add_column(col, style=st)
        for gateway, info in status_info["circuit_breakers"].items():
            sc = {"closed": "green", "half-open": "yellow", "open": "red"}.get(info["state"], "white")
            circuit_table.add_row(gateway, f"[{sc}]{info['state']}[/{sc}]", str(info["failure_count"]))
        console.print(circuit_table)
        console.print()

    if verbose:
        for key, title, col_name in [("endpoints", "📍 Endpoints", "Endpoint"), ("methods", "🔧 Methods", "Method")]:
            if status_info[key]:
                t = Table(title=title)
                t.add_column(col_name, style="cyan")
                t.add_column("Count", style="white")
                for k, count in sorted(status_info[key].items(), key=lambda x: x[1], reverse=True):
                    t.add_row(k, str(count))
                console.print(t)
                console.print()


@app.command("reset")
def reset(
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Skip confirmation prompt"),
) -> None:
    """Reset local usage metrics (admin only)."""
    from src.core.telemetry_reporter import TelemetryReporter

    if not confirm:
        console.print("[bold yellow]⚠️  Warning: This will delete all local usage metrics![/bold yellow]\n")
        console.print("[dim]This action:\n  • Clears local telemetry cache\n  • Does NOT affect server-side metrics\n  • Cannot be undone[/dim]\n")
        if not typer.confirm("Are you sure you want to continue?"):
            console.print("[yellow]Cancelled.[/yellow]\n")
            raise SystemExit(0)

    console.print("[dim]Resetting local metrics...[/dim]")
    try:
        reporter = TelemetryReporter()
        reporter._metrics = []
        _reset_sync_client()
        console.print("[green]✓ Local metrics reset complete[/green]\n[dim]Note: Server-side metrics at RaaS Gateway are not affected.[/dim]\n")
    except Exception as e:
        console.print(f"[bold red]✗ Reset failed: {str(e)}[/bold red]\n")
        raise SystemExit(1)


def _reset_sync_client() -> None:
    """Helper to reset sync client (for CLI)."""
    from src.raas.sync_client import reset_sync_client as _reset
    _reset()


@app.command("kv-sync")
def kv_sync(
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh from KV"),
) -> None:
    """Sync rate limit state with KV store."""
    from src.core.kv_store_client import get_kv_client

    console.print("[bold cyan]🔄 KV Store Sync[/bold cyan]\n")
    client = get_kv_client()
    success, message = client.sync_state()

    if success:
        console.print(f"[green]✓ {message}[/green]\n")
        _display_rate_limit_state(client.get_rate_limit_state(force_refresh=force))
    else:
        console.print(f"[bold red]✗ {message}[/bold red]\n")
        raise typer.Exit(code=1)


@app.command("kv-status")
def kv_status() -> None:
    """Show KV store health and rate limit state."""
    from src.core.kv_store_client import show_kv_status
    show_kv_status()


app.command("encrypted")(sync_encrypted)
app.command("entitlement")(show_entitlement)

__all__ = [
    "Any", "Panel", "_display_rate_limit_state", "_display_summary",
    "_reset_sync_client", "app", "console", "json", "kv_status", "kv_sync",
    "reset", "show_entitlement", "status", "sync", "sync_encrypted",
]

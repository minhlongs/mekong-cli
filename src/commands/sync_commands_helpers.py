# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""KV store, encrypted sync, and entitlement helpers for Mekong Sync CLI."""

import json
import sys
from typing import Any

from rich.panel import Panel
from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.sync_commands"]


def _display_summary(summary: Any, result: Any, verbose: bool = False) -> None:
    """Display sync summary in formatted table."""
    f = _facade()
    table = Table(title="📊 Sync Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Requests", str(summary.total_requests))
    table.add_row("Total Payload", f"{summary.total_payload_size:,} bytes")
    table.add_row("Hours Active", str(summary.hours_active))

    if summary.peak_hour:
        table.add_row("Peak Hour", f"{summary.peak_hour} ({summary.peak_requests} requests)")
    if result.rate_limit_remaining is not None:
        table.add_row("Rate Limit Remaining", str(result.rate_limit_remaining))
    table.add_row("Sync Time", f"{result.elapsed_ms:.0f}ms")

    f.console.print(table)
    f.console.print()

    if verbose and summary.endpoints:
        endpoint_table = Table(title="📍 Endpoint Breakdown")
        endpoint_table.add_column("Endpoint", style="cyan")
        endpoint_table.add_column("Requests", style="green")
        for endpoint, count in sorted(summary.endpoints.items(), key=lambda x: x[1], reverse=True):
            endpoint_table.add_row(endpoint, str(count))
        f.console.print(endpoint_table)
        f.console.print()

    if verbose and summary.methods:
        method_table = Table(title="🔧 Method Breakdown")
        method_table.add_column("Method", style="cyan")
        method_table.add_column("Requests", style="green")
        for method, count in sorted(summary.methods.items(), key=lambda x: x[1], reverse=True):
            method_table.add_row(method, str(count))
        f.console.print(method_table)
        f.console.print()

    if result.success:
        f.console.print(
            Panel(
                f"[green]✓ Sync completed successfully![/green]\n\n"
                f"Synced [bold]{result.synced_count}[/bold] requests ([bold]{result.total_payload_size:,}[/bold] bytes)\n"
                f"Gateway response: [dim]{result.gateway_response}[/dim]",
                title="✅ Sync Status",
                border_style="green",
            )
        )


def _display_rate_limit_state(state: Any) -> None:
    """Display rate limit state in table."""
    f = _facade()
    table = Table(title="Rate Limit State")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Remaining", str(state.remaining))
    table.add_row("Limit", str(state.limit))
    table.add_row("Reset In", f"{state.seconds_until_reset}s")
    table.add_row("Synced At", state.synced_at.strftime("%H:%M:%S"))
    f.console.print(table)


def sync_encrypted(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Calculate but don't upload"),
    no_billing: bool = typer.Option(False, "--no-billing", help="Don't push to Stripe/Polar"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed metrics"),
) -> None:
    """Synchronize with encrypted payload (Phase 5)."""
    from src.raas.sync_client import get_sync_client

    f = _facade()
    f.console.print("[bold cyan]🔐 Mekong Sync Encrypted - Phase 5[/bold cyan]\n")
    client = get_sync_client()

    f.console.print("[dim]Step 1/4: Validating license...[/dim]")
    is_valid, error = client.validate_license()
    if not is_valid:
        f.console.print(f"[bold red]✗ License validation failed[/bold red]\n[red]{error}[/red]\n")
        f.console.print("[yellow]Get a license key:[/yellow]\n  [cyan]https://api.cashclaw.cc[/cyan]\n")
        raise SystemExit(1)

    f.console.print("[green]✓ License valid[/green]\n[dim]Step 2/4: Fetching entitlements...[/dim]")
    entitlements = client.fetch_entitlements()

    if "error" not in entitlements:
        f.console.print(f"[green]✓ Tier:[/green] {entitlements.get('tier', 'unknown')} | Rate limit: {entitlements.get('rate_limit', 60)}/min\n")
    else:
        f.console.print(f"[yellow]⚠ Entitlements: {entitlements.get('error')}[/yellow]\n")

    if dry_run:
        f.console.print("[dim]Step 3/4: Dry run (skipping upload)...[/dim]")
        result = client.sync_metrics_encrypted(dry_run=True, push_to_billing=not no_billing)
        f.console.print("[green]✓ Dry run complete[/green]\n")
    else:
        f.console.print("[dim]Step 3/4: Syncing encrypted payload...[/dim]")
        result = client.sync_metrics_encrypted(push_to_billing=not no_billing)
        if not result.success:
            f.console.print(f"[bold red]✗ Sync failed[/bold red]\n[red]{result.error}[/red]\n")
            raise SystemExit(1)
        f.console.print(f"[green]✓ Synced {result.synced_count} events[/green]\n")

    f.console.print(
        Panel(
            f"[green]✓ Sync completed![/green]\n\nEvents: [bold]{result.synced_count}[/bold]\n"
            f"Payload: [bold]{result.total_payload_size:,}[/bold] bytes\nTime: [bold]{result.elapsed_ms:.0f}[/bold]ms",
            title="🔐 Encrypted Sync Status",
            border_style="green",
        )
    )


def show_entitlement(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full entitlement details"),
) -> None:
    """Show license entitlements from RaaS Gateway."""
    from src.raas.sync_client import get_sync_client

    f = _facade()
    f.console.print("[bold cyan]📋 License Entitlements[/bold cyan]\n")
    client = get_sync_client()

    f.console.print("[dim]Validating license...[/dim]")
    is_valid, error = client.validate_license()
    if not is_valid:
        f.console.print(f"[bold red]✗ License invalid[/bold red]\n[red]{error}[/red]\n")
        return

    f.console.print("[green]✓ License valid[/green]\n[dim]Fetching entitlements from RaaS Gateway...[/dim]")
    entitlements = client.fetch_entitlements()

    if "error" in entitlements:
        f.console.print(f"[bold red]✗ Failed: {entitlements['error']}[/bold red]\n")
        raise SystemExit(1)

    table = Table(title="License Entitlements", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Tenant ID", str(entitlements.get("tenant_id", "N/A")))
    table.add_row("Tier", entitlements.get("tier", "unknown").upper())
    table.add_row("Features", ", ".join(entitlements.get("features", [])) or "None")
    table.add_row("Rate Limit", f"{entitlements.get('rate_limit', 60)} requests/min")
    table.add_row("Max Payload", f"{entitlements.get('max_payload_size', 1048576):,} bytes")
    table.add_row("Retention", f"{entitlements.get('retention_days', 30)} days")
    if entitlements.get("expires_at"):
        table.add_row("Expires At", str(entitlements["expires_at"]))

    f.console.print(table)
    f.console.print()
    if verbose:
        f.console.print("[dim]Raw response:[/dim]")
        f.console.print(json.dumps(entitlements, indent=2))
        f.console.print()

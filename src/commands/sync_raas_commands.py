# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sync RaaS CLI Command — Phase 6 Usage Reporting Integration."""

from datetime import datetime, timezone
import os
from typing import Optional

from rich.console import Console
from rich.table import Table
import typer

from src.commands.sync_raas_subcommands import show_entitlement, show_events, sync_status

console = Console()
app = typer.Typer(
    name="sync-raas", help="🔄 Sync with RaaS Gateway - usage metering & billing integration", rich_markup_mode="rich"
)


@app.command()
def sync_raas(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed sync information"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be synced without sending"),
    no_billing: bool = typer.Option(False, "--no-billing", help="Don't push to Stripe/Polar billing"),
) -> None:
    """🔄 Full sync with RaaS Gateway."""
    from src.raas.sync_client import get_sync_client

    console.print("[bold cyan]🔄 Mekong Sync RaaS - Phase 6[/bold cyan]\n\n[dim]Step 1/5: Authenticating with RaaS Gateway...[/dim]")
    if not _authenticate():
        return
    console.print("[green]✓ Authenticated[/green]\n\n[dim]Step 2/5: Fetching license entitlements...[/dim]")

    client = get_sync_client()
    entitlements = client.fetch_entitlements()
    if "error" in entitlements:
        console.print(f"[bold red]✗ Failed: {entitlements['error']}[/bold red]\n")
        return

    _display_entitlements(entitlements)
    console.print("\n[dim]Step 3/5: Registering with billing system...[/dim]")
    if dry_run:
        console.print("[yellow]⊘ Skipped (dry run)[/yellow]\n")
    else:
        webhook_result = client.register_webhook(push_to_billing=not no_billing)
        if webhook_result.get("success"):
            console.print(f"[green]✓ Registered with {webhook_result.get('provider', 'billing')}[/green]\n")
        else:
            console.print(f"[yellow]⚠ Webhook registration: {webhook_result.get('error', 'skipped')}[/yellow]\n")

    console.print("[dim]Step 4/5: Syncing usage metrics...[/dim]")
    if dry_run:
        console.print("[yellow]⊘ Skipped (dry run)[/yellow]\n")
    else:
        sync_result = client.sync_metrics()
        if sync_result.success:
            console.print(f"[green]✓ Synced {sync_result.synced_count} events[/green]\n")
        else:
            console.print(f"[yellow]⚠ Sync: {sync_result.error}[/yellow]\n")

    console.print("[dim]Step 5/5: Pushing analytics to MekongMind...[/dim]")
    if dry_run:
        console.print("[yellow]⊘ Skipped (dry run)[/yellow]\n\n[bold]Dry Run Complete[/bold]\n")
    else:
        analytics_result = client.push_analytics()
        if analytics_result.get("success"):
            console.print("[green]✓ Analytics pushed[/green]\n")
        else:
            console.print(f"[dim]Analytics: {analytics_result.get('error', 'skipped')}[/dim]\n")

    _display_sync_summary(entitlements, verbose)


def _authenticate() -> bool:
    """Authenticate with RaaS Gateway. Returns True if successful."""
    from src.core.raas_auth import RaaSAuthClient

    auth_client = RaaSAuthClient()
    session = auth_client.get_session()
    if session.authenticated:
        return True

    api_key = os.getenv("RAAS_LICENSE_KEY")
    if not api_key:
        console.print("[bold red]✗ No license key found[/bold red]\n")
        console.print(
            "[yellow]Set your license key:[/yellow]\n"
            "  [cyan]export RAAS_LICENSE_KEY=mk_your_key[/cyan]\n\n"
            "Or get a key from:\n"
            "  [cyan]https://www.mekongmind.com[/cyan]\n"
        )
        return False

    result = auth_client.validate_credentials(api_key)
    if not result.valid:
        console.print(f"[bold red]✗ Authentication failed: {result.error}[/bold red]\n")
        return False

    return True


def _display_entitlements(entitlements: dict) -> None:
    """Display license entitlements in table."""
    table = Table(title="License Entitlements", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim")
    table.add_column("Value", style="green")

    table.add_row("Tenant ID", str(entitlements.get("tenant_id", "N/A")))
    table.add_row("Tier", entitlements.get("tier", "unknown").upper())
    table.add_row("Features", ", ".join(entitlements.get("features", [])) or "None")
    table.add_row("Rate Limit", f"{entitlements.get('rate_limit', 60)} requests/min")
    table.add_row("Max Payload", f"{entitlements.get('max_payload_size', 1048576):,} bytes")
    table.add_row("Retention", f"{entitlements.get('retention_days', 30)} days")

    if entitlements.get("expires_at"):
        table.add_row("Expires At", str(entitlements["expires_at"]))

    console.print(table)


def _display_sync_summary(entitlements: dict, verbose: bool = False) -> None:
    """Display sync summary."""
    summary_table = Table(title="Sync Summary", show_header=False, box=None)
    summary_table.add_column("Label", style="dim")
    summary_table.add_column("Value", style="cyan")

    summary_table.add_row("Sync Time", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    summary_table.add_row("Gateway", "https://www.mekongmind.com")
    summary_table.add_row("Version", "v2.0.0 (CF Worker)")

    console.print(summary_table)

    if verbose:
        console.print("\n[dim]Anonymized analytics pushed to MekongMind dashboard[/dim]")
        console.print("[dim]Dashboard: https://www.mekongmind.com[/dim]\n")


app.command("status")(sync_status)
app.command("entitlement")(show_entitlement)
app.command("events")(show_events)

__all__ = [
    "Optional", "_authenticate", "_display_entitlements", "_display_sync_summary",
    "app", "console", "os", "show_entitlement", "show_events", "sync_raas",
    "sync_status",
]

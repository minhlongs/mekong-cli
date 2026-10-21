# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Status, entitlement, and events subcommands for Sync RaaS CLI."""

from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Optional

from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.sync_raas_commands"]


def sync_status() -> None:
    """
    📊 Show sync status without uploading.

    Displays connection status, local metrics cache,
    and last sync timestamp.
    """
    from src.raas.sync_client import get_sync_client

    f = _facade()
    f.console.print("[bold cyan]📊 Sync Status[/bold cyan]\n")

    client = get_sync_client()
    status = client.get_sync_status()

    connection_table = Table(title="Connection Status", show_header=False, box=None)
    connection_table.add_column("Property", style="dim")
    connection_table.add_column("Value", style="green" if status.get("connected") else "red")

    connection_table.add_row("Gateway", "✓ Connected" if status.get("connected") else "✗ Disconnected")
    connection_table.add_row("License", "✓ Valid" if status.get("license_valid") else "✗ Invalid")
    connection_table.add_row("Last Sync", status.get("last_sync", "Never"))

    f.console.print(connection_table)
    f.console.print()

    metrics = status.get("local_metrics", {})
    if metrics.get("count", 0) > 0:
        metrics_table = Table(title="Local Metrics", show_header=True)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="white")

        metrics_table.add_row("Events", str(metrics.get("count", 0)))
        metrics_table.add_row("Size", f"{metrics.get('total_size', 0):,} bytes")
        metrics_table.add_row("Oldest", metrics.get("oldest", "N/A"))
        metrics_table.add_row("Newest", metrics.get("newest", "N/A"))

        f.console.print(metrics_table)
    else:
        f.console.print("[dim]No local metrics cached.[/dim]\n")

    circuit_breakers = status.get("circuit_breakers", {})
    if circuit_breakers:
        f.console.print("\n[bold]Circuit Breakers:[/bold]")
        for gateway, info in circuit_breakers.items():
            state_color = {
                "closed": "green",
                "half-open": "yellow",
                "open": "red",
            }.get(info.get("state"), "white")
            f.console.print(
                f"  {gateway}: [{state_color}]{info.get('state')}[/{state_color}] ({info.get('failure_count', 0)} failures)"
            )


def show_entitlement(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show raw entitlement response"
    ),
) -> None:
    """
    📋 Show license entitlements from RaaS Gateway.

    Fetches current license tier, features, rate limits,
    and entitlements from the central billing system.
    """
    from src.raas.sync_client import get_sync_client

    f = _facade()
    f.console.print("[bold cyan]📋 License Entitlements[/bold cyan]\n")

    if not f._authenticate():
        return

    f.console.print("[green]✓ Authenticated[/green]\n")

    client = get_sync_client()
    entitlements = client.fetch_entitlements()

    if "error" in entitlements:
        f.console.print(f"[bold red]✗ Failed: {entitlements['error']}[/bold red]\n")
        return

    f._display_entitlements(entitlements)

    if verbose:
        f.console.print("\n[dim]Raw response:[/dim]")
        f.console.print(f"[dim]{json.dumps(entitlements, indent=2)}[/dim]\n")


def show_events(
    limit: int = typer.Option(
        20, "--limit", "-l", help="Number of events to show"
    ),
    event_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by event type (cli:command, llm:call, etc.)"
    ),
) -> None:
    """
    📊 Show recent usage events.

    Displays locally cached usage events before sync.
    """
    f = _facade()
    f.console.print("[bold cyan]📊 Recent Usage Events[/bold cyan]\n")

    usage_dir = Path.home() / ".mekong" / "usage"
    if not usage_dir.exists():
        f.console.print("[yellow]No usage data found.[/yellow]")
        f.console.print("[dim]Usage tracking starts on next command execution.[/dim]\n")
        return

    usage_files = sorted(usage_dir.glob("*.json"), reverse=True)[:limit]
    if not usage_files:
        f.console.print("[dim]No usage events cached.[/dim]\n")
        return

    f.console.print(f"Found [cyan]{len(usage_files)}[/cyan] event file(s)\n")

    events_table = Table(title=f"Last {len(usage_files)} Events", show_header=True)
    events_table.add_column("File", style="dim")
    events_table.add_column("Events", style="white")
    events_table.add_column("Size", style="green")
    events_table.add_column("Created", style="cyan")

    for usage_file in usage_files[:10]:
        try:
            with open(usage_file, "r") as fh:
                data = json.load(fh)
            events = data.get("events", [])
            size = usage_file.stat().st_size
            created = datetime.fromtimestamp(usage_file.stat().st_mtime)

            events_table.add_row(
                usage_file.name,
                str(len(events)),
                f"{size:,} bytes",
                created.strftime("%Y-%m-%d %H:%M"),
            )
        except Exception:
            events_table.add_row(usage_file.name, "Error", "-", "-")

    f.console.print(events_table)

    if len(usage_files) > 10:
        f.console.print(f"\n[dim]... and {len(usage_files) - 10} more files[/dim]\n")

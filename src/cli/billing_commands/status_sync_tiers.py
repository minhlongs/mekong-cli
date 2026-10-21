# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Billing status, sync, sync-status, and tiers commands."""

from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.table import Table

from src.cli.billing_commands.helpers import _mod, app, console, print_error, print_success


def _render_fallback_status(license_key: str) -> None:
    from src.core.billing_engine import get_billing_engine

    st = get_billing_engine().get_billing_status(license_key=license_key)
    table = Table("Metric", "Value", show_header=True, header_style="bold green")
    for k, v in [
        ("Tier", "pro"), ("Status", st["status"]),
        ("MCU Quota", f"{st['quota_consumed_mcu']:.1f} / {st['quota_allocated_mcu']:.1f} MCU"),
        ("Current Charge", f"${st['total_unbilled_usd']:.2f}"),
        ("Events Recorded", str(st["total_events_recorded"])),
    ]:
        table.add_row(k, v)
    console.print(table)


@app.command("status")
def billing_status(
    license_key: str = typer.Option("mekong_lic_default", "--license", "-l", help="License key"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """📊 Get billing status for a license."""
    if json_output:
        from src.core.billing_engine import get_billing_engine

        print(json.dumps(get_billing_engine().get_billing_status(license_key=license_key), indent=2))
        return

    import asyncio
    from datetime import datetime

    console.print(f"[bold cyan]📊 Billing Status[/bold cyan]\n\nLicense: [cyan]{license_key}[/cyan]\n")
    try:
        from src.db.repository import get_repository

        license_info = asyncio.run(get_repository().get_license_by_key(license_key))
        if not license_info:
            _render_fallback_status(license_key)
            return

        result = asyncio.run(_mod().get_engine().calculate_period_charges(
            license_key=license_key, period_start=datetime.now().replace(day=1), period_end=datetime.now(),
        ))
        table = Table("Metric", "Value", show_header=True, header_style="bold green")
        for k, v in [
            ("Tier", license_info.get("tier", "unknown")), ("Status", license_info.get("status", "unknown")),
            ("Period Start", result.period_start.date().isoformat()),
            ("Current Charge", f"${result.total}"), ("Line Items", str(len(result.line_items))),
        ]:
            table.add_row(k, v)
        console.print(table)
    except Exception:
        _render_fallback_status(license_key)


@app.command("sync")
def billing_sync(
    license_key: Optional[str] = typer.Option(None, "--license", "-l", help="License key (defaults to MEKONG_API_KEY)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Simulate without submitting"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed sync information"),
    force: bool = typer.Option(False, "--force", "-f", help="Force resync already synced records"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit number of records to sync"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """🔄 Sync usage records from local SQLite to RaaS Gateway."""
    if json_output:
        from src.core.billing_engine import get_billing_engine

        print(json.dumps(get_billing_engine().sync_usage_records(), indent=2))
        return

    console.print("[bold cyan]🔄 Billing Sync - RaaS Gateway[/bold cyan]\n")
    m = _mod()
    service = m.BillingSyncService(m.SyncConfig(api_key=license_key)) if license_key else m.get_service()
    api_key = license_key or os.getenv("MEKONG_API_KEY") or os.getenv("RAAS_LICENSE_KEY", "")
    if not api_key:
        print_error("API key not configured", "Set MEKONG_API_KEY or RAAS_LICENSE_KEY environment variable")
        raise SystemExit(1)

    console.print(f"Gateway: [cyan]https://api.cashclaw.cc/v2/usage[/cyan]\nAPI Key: [cyan]mk_***{api_key[-4:] if len(api_key) > 4 else api_key}[/cyan]\n")
    if dry_run:
        console.print("[yellow]🛑 Dry run mode - will not submit[/yellow]\n")
        records = service.fetch_unsynced_records(limit)
        if not records:
            console.print("[dim]No unsynced records found.[/dim]")
        else:
            console.print(f"Would sync [cyan]{len(records)}[/cyan] record(s):")
            for r in records[:5]:
                console.print(f"  • {r.event_type} - {r.endpoint or 'N/A'} - {r.timestamp}")
            if len(records) > 5:
                console.print(f"  ... and {len(records) - 5} more")
        console.print(f"\nPayload size: [cyan]{len(json.dumps(service.build_payload(records) if records else {}))}[/cyan] bytes")
        return

    if force:
        console.print("[yellow]⚠ Force resync mode - re-syncing already synced records[/yellow]\n")
    result = service.force_resync(limit) if force else service.sync_to_gateway(limit)

    if result.success:
        print_success(f"Synced {result.records_synced} record(s)")
        console.print(f"Payload size: [cyan]{result.total_payload_size}[/cyan] bytes\nElapsed: [cyan]{result.elapsed_ms:.0f}[/cyan]ms\nIdempotency key: [dim]{result.idempotency_key}[/dim]")
        if result.gateway_response:
            console.print(f"\nGateway response: [green]{result.gateway_response.get('status', 'OK')}[/green]")
    else:
        print_error("Sync failed", result.error)
        console.print(f"Records failed: [red]{result.records_failed}[/red]\nRetry count: [yellow]{result.retry_count}[/yellow]")
        raise SystemExit(1)


@app.command("sync-status")
def billing_sync_status() -> None:
    """📊 Show billing sync status."""
    console.print("[bold cyan]📊 Billing Sync Status[/bold cyan]\n")
    status = _mod().get_service().get_sync_status()
    table = Table(title="Sync Status", show_header=False, box=None)
    table.add_column("Property", style="dim")
    table.add_column("Value", style="green" if status.get("api_key_configured") else "red")
    for k, v in [
        ("API Key", "✓ Configured" if status["api_key_configured"] else "✗ Not configured"),
        ("Gateway", status["gateway_url"]), ("Unsynced Records", str(status["unsynced_records"])),
        ("Synced Records", str(status["synced_records"])), ("Last Sync", status["last_sync"] or "Never"),
    ]:
        table.add_row(k, v)
    console.print(table)

    if status["recent_history"]:
        console.print("\n[bold]Recent Sync History:[/bold]")
        history_table = Table(show_header=True, header_style="bold cyan")
        for col, st in [("Time", "dim"), ("Records", "white"), ("Status", "white"), ("Key", "dim")]:
            history_table.add_column(col, style=st)
        for entry in status["recent_history"][:5]:
            st_col = "green" if entry["status"] == "success" else "red"
            history_table.add_row(
                entry["created_at"][:19] if entry["created_at"] else "N/A",
                str(entry["records_count"]), f"[{st_col}]{entry['status']}[/{st_col}]",
                entry["idempotency_key"][:20] + "...",
            )
        console.print(history_table)


@app.command("tiers")
def billing_tiers(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON tiers"),
) -> None:
    """🏷️ Display monetization tiers and consumption rate matrices."""
    from src.core.billing_engine import get_billing_engine

    tiers = get_billing_engine().get_pricing_tiers()
    if json_output:
        print(json.dumps(tiers, indent=2))
        return
    table = Table(title="🏷️ Mekong Monitored Pricing Tiers & Unit Costs", header_style="bold yellow")
    table.add_column("Tier", style="bold")
    for col in ("Monthly Base", "Included MCU", "LLM Tokens (1k)", "Agent Min", "API Call"):
        table.add_column(col, justify="right")
    for k, v in tiers.items():
        table.add_row(
            k.upper(), f"${v['base_monthly_usd']:.2f}", f"{v['included_mcu']:,}",
            f"${v['rates']['llm_tokens']:.4f}", f"${v['rates']['agent_minutes']:.3f}", f"${v['rates']['api_calls']:.4f}",
        )
    console.print(table)

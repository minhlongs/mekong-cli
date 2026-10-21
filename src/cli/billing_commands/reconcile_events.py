# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Billing reconciliation and event emission commands."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

import typer
from rich.table import Table

from src.cli.billing_commands.helpers import (
    _mod, app, console, logger, print_error, print_success,
)
from src.core.event_bus import EventType


@app.command("reconcile")
def trigger_reconciliation(
    license_key: Optional[str] = typer.Option(None, "--license", "-l", help="Specific license to reconcile"),
    audit_date: Optional[str] = typer.Option(None, "--date", "-d", help="Audit date (YYYY-MM-DD, default: yesterday)"),
    all_licenses: bool = typer.Option(False, "--all", help="Reconcile all licenses"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """🔍 Trigger reconciliation audit for variance detection."""
    if json_output:
        from src.core.billing_engine import get_billing_engine

        print(json.dumps(get_billing_engine().reconcile_usage(license_key=license_key or "all"), indent=2))
        return

    import asyncio
    from datetime import timedelta

    console.print("[bold cyan]🔍 Running Reconciliation Audit[/bold cyan]\n")
    if audit_date:
        try:
            audit_dt = date.fromisoformat(audit_date)
        except ValueError:
            print_error("Invalid date format", "Use YYYY-MM-DD")
            raise SystemExit(1)
    else:
        audit_dt = date.today() - timedelta(days=1)

    console.print(f"Audit Date: [cyan]{audit_dt}[/cyan]\nLicense: [cyan]{license_key or 'all'}[/cyan]\n")
    try:
        results = asyncio.run(_mod().get_reconciliation_service().run_daily_reconciliation(audit_date=audit_dt))
        table = Table(show_header=True, header_style="bold cyan")
        for col in ("License Key", "Status", "Expected", "Actual", "Variance", "Variance %"):
            table.add_column(col)

        matched = variance = investigating = 0
        for result in results:
            if license_key and result.license_key != license_key:
                continue
            status_style = {"matched": "green", "variance": "yellow"}.get(result.status, "red")
            if result.status == "matched":
                matched += 1
            elif result.status == "variance":
                variance += 1
            else:
                investigating += 1

            table.add_row(
                result.license_key, f"[{status_style}]{result.status}[/{status_style}]",
                f"${result.expected_amount}", f"${result.actual_amount}",
                f"${result.variance}", f"{result.variance_percent:.2f}%",
            )

        console.print(table)
        console.print(f"\n[bold]Summary:[/bold]\n  Matched: [green]{matched}[/green]\n  Variance: [yellow]{variance}[/yellow]\n  Investigating: [red]{investigating}[/red]")
        if variance > 0 or investigating > 0:
            console.print("\n[yellow]⚠ Variances detected — review reconciliation_audits table[/yellow]")
    except Exception as e:
        print_error("Reconciliation failed", str(e))
        logger.exception("Reconciliation error")
        raise SystemExit(1)


@app.command("emit-event")
def emit_billing_event(
    event_type: str = typer.Argument(..., help="Event type (billing:recorded, billing:overage, etc.)"),
    payload: Optional[str] = typer.Option(None, "--payload", "-p", help="JSON payload"),
    payload_file: Optional[str] = typer.Option(None, "--payload-file", "-f", help="JSON file with payload"),
    webhook_url: Optional[str] = typer.Option(None, "--webhook", "-w", help="Webhook URL to emit to"),
) -> None:
    """📡 Emit billing event to event bus or webhook."""
    import requests

    console.print("[bold cyan]📡 Emitting Billing Event[/bold cyan]\n")

    event_data = {}
    if payload:
        try:
            event_data = json.loads(payload)
        except json.JSONDecodeError as e:
            print_error("Invalid JSON payload", str(e))
            raise SystemExit(1)
    elif payload_file:
        try:
            with open(payload_file, "r") as f:
                event_data = json.load(f)
        except FileNotFoundError:
            print_error("Payload file not found", payload_file)
            raise SystemExit(1)
        except json.JSONDecodeError as e:
            print_error("Invalid JSON in payload file", str(e))
            raise SystemExit(1)

    event_type_map = {
        "billing:recorded": EventType.BILLING_RECORDED,
        "billing:overage": EventType.BILLING_OVERAGE,
        "billing:period_closed": EventType.BILLING_PERIOD_CLOSED,
        "billing:reconciliation": EventType.BILLING_RECONCILIATION,
        "billing:batch_processed": EventType.BILLING_BATCH_PROCESSED,
        "billing:idempotency_conflict": EventType.BILLING_IDEMPOTENCY_CONFLICT,
    }

    if event_type not in event_type_map:
        print_error(
            f"Unknown event type: {event_type}",
            f"Valid types: {', '.join(event_type_map.keys())}",
        )
        raise SystemExit(1)

    event_enum = event_type_map[event_type]
    event = _mod().get_event_bus().emit(event_enum, event_data)

    console.print(f"Event Type: [cyan]{event_type}[/cyan]")
    console.print(f"Timestamp: [cyan]{datetime.fromtimestamp(event.timestamp)}[/cyan]")
    console.print(f"Payload: {json.dumps(event_data, indent=2)}")

    if webhook_url:
        console.print(f"\nSending to webhook: {webhook_url}")
        try:
            response = requests.post(
                webhook_url,
                json={
                    "event_type": event_type,
                    "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
                    "data": event_data,
                },
                timeout=10,
            )
            response.raise_for_status()
            print_success(f"Webhook response: {response.status_code}")
        except requests.RequestException as e:
            print_error("Webhook failed", str(e))
            raise SystemExit(1)
    else:
        console.print("\n[ydim]No webhook URL provided — emitted to local event bus only[/ydim]")

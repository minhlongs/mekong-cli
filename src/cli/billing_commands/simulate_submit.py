# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Billing simulate and submit-usage commands."""

from __future__ import annotations

import json
from typing import Optional

import typer

from src.cli.billing_commands.helpers import (
    _mod,
    app,
    console,
    print_billing_result,
    print_error,
    print_success,
)


@app.command("simulate")
def simulate_billing(
    license_key: str = typer.Option("mekong_lic_default", "--license", "-l", help="License key"),
    api_calls: int = typer.Option(100, "--api-calls", help="Number of API calls"),
    token_input: int = typer.Option(1000, "--token-input", help="Input tokens (in K)"),
    token_output: int = typer.Option(500, "--token-output", help="Output tokens (in K)"),
    agent_spawns: int = typer.Option(10, "--agent-spawns", help="Number of agent spawns"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
    period_start: Optional[str] = typer.Option(None, "--period-start", help="Period start (YYYY-MM-DD)"),
    period_end: Optional[str] = typer.Option(None, "--period-end", help="Period end (YYYY-MM-DD)"),
    tier: str = typer.Option("pro", "--tier", "-t", help="Pricing tier: free, developer, pro, enterprise"),
    days: int = typer.Option(30, "--days", "-d", help="Period days"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON invoice"),
) -> None:
    """🧪 Simulate billing calculation for usage."""
    if json_output:
        from src.core.billing_engine import get_billing_engine

        print(json.dumps(get_billing_engine().simulate_billing(license_key=license_key, tier=tier, period_days=days), indent=2))
        return

    import asyncio
    from datetime import datetime

    from src.core.anomaly_detector import AnomalyCategory
    from src.core.usage_metering import UsageEvent, UsageEventType

    console.print("[bold cyan]🧪 Simulating Billing Calculation[/bold cyan]\n")
    now_ts = datetime.now().timestamp()
    events = [
        UsageEvent(event_type=UsageEventType.API_CALL, category=AnomalyCategory.API_CALLS, metric="requests", value=api_calls, timestamp=now_ts, metadata={"source": "cli_simulate"}),
        UsageEvent(event_type=UsageEventType.TOKEN_USAGE, category=AnomalyCategory.TOKEN_USAGE, metric="input_tokens", value=token_input, timestamp=now_ts, metadata={"source": "cli_simulate"}),
        UsageEvent(event_type=UsageEventType.TOKEN_USAGE, category=AnomalyCategory.TOKEN_USAGE, metric="output_tokens", value=token_output, timestamp=now_ts, metadata={"source": "cli_simulate"}),
        UsageEvent(event_type=UsageEventType.AGENT_SPAWN, category=AnomalyCategory.AGENT_SPAWNS, metric="spawns", value=agent_spawns, timestamp=now_ts, metadata={"source": "cli_simulate", "model": model}),
    ]
    period_start_dt = datetime.strptime(period_start, "%Y-%m-%d") if period_start else datetime.now()
    period_end_dt = datetime.strptime(period_end, "%Y-%m-%d") if period_end else datetime.now()

    try:
        result = asyncio.run(_mod().get_engine().calculate_charges(license_key=license_key, usage_events=events, period_start=period_start_dt, period_end=period_end_dt))
        print_billing_result(result)
        console.print("\n[ydim]Simulation only — no charges applied[/ydim]")
    except Exception as e:
        print_error("Billing simulation failed", str(e))
        raise SystemExit(1)


@app.command("submit-usage")
def submit_usage(
    license_key: str = typer.Option("mekong_lic_default", "--license", "-l", help="License key"),
    events_file: Optional[str] = typer.Option(None, "--events-file", "-f", help="JSON file with usage events"),
    event_type: Optional[str] = typer.Option(None, "--event-type", "-t", help="Event type (if not using file)"),
    metric: Optional[str] = typer.Option("requests", "--metric", "-m", help="Metric name"),
    value: Optional[float] = typer.Option(None, "--value", "-v", help="Usage value"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name"),
    batch_id: Optional[str] = typer.Option(None, "--batch-id", help="Batch ID for idempotency"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Simulate without submitting"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """📤 Submit usage events for billing (with idempotency)."""
    if json_output:
        from src.core.billing_engine import get_billing_engine

        rec = get_billing_engine().record_usage(
            license_key=license_key, event_type=event_type or "api_calls",
            quantity=value if value is not None else 1.0, idempotency_key=batch_id or "",
        )
        print(json.dumps(rec, indent=2))
        return

    import asyncio
    from datetime import datetime, timezone

    console.print("[bold cyan]📤 Submitting Usage for Billing[/bold cyan]\n")
    events = []
    if events_file:
        try:
            with open(events_file, "r") as f:
                events_data = json.load(f)
                events = events_data.get("events", events_data)
        except FileNotFoundError:
            print_error("Events file not found", events_file)
            raise SystemExit(1)
        except json.JSONDecodeError as e:
            print_error("Invalid JSON in events file", str(e))
            raise SystemExit(1)
    elif event_type and value is not None:
        events = [{"event_type": event_type, "metric": metric, "value": value, "model": model, "timestamp": datetime.now(timezone.utc).isoformat(), "metadata": {"source": "cli"}}]
    else:
        print_error("Missing required arguments", "Provide --events-file OR (--event-type and --value)")
        raise SystemExit(1)

    if not events:
        print_error("No events to process")
        raise SystemExit(1)

    console.print(f"Processing {len(events)} event(s)...")
    idempotency_manager = _mod().get_idempotency_manager()
    if not batch_id:
        batch_id = idempotency_manager.generate_batch_id(license_key=license_key, events=events)

    console.print(f"Batch ID: [cyan]{batch_id}[/cyan]")
    if dry_run:
        console.print("\n[yellow]🛑 Dry run — not submitting[/yellow]")
        return

    async def process_batch(events_list):
        from src.core.anomaly_detector import AnomalyCategory
        from src.core.usage_metering import UsageEvent, UsageEventType

        usage_events = [
            UsageEvent(
                event_type=UsageEventType(e.get("event_type", "usage:api_call")),
                category=AnomalyCategory.API_CALLS, metric=e.get("metric", "requests"),
                value=e.get("value", 0),
                timestamp=datetime.fromisoformat(e["timestamp"]).timestamp() if e.get("timestamp") else datetime.now().timestamp(),
                metadata=e.get("metadata", {}),
            )
            for e in events_list
        ]
        result = await _mod().get_engine().calculate_charges(license_key=license_key, usage_events=usage_events, period_start=datetime.now(), period_end=datetime.now())
        billing_record_id = f"br_{batch_id}_{int(datetime.now().timestamp())}"
        _mod().get_emitter().emit_billing_recorded(result, billing_record_id)
        return billing_record_id

    try:
        result = asyncio.run(idempotency_manager.process_batch(batch_id=batch_id, license_key=license_key, key_id="", events=events, process_fn=process_batch))
        if result.is_duplicate:
            console.print(f"\n[yellow]⚠ Duplicate batch detected (already processed)[/yellow]\nBilling Record: {result.billing_record_id}")
        elif result.status == "completed":
            print_success("Batch processed successfully")
            console.print(f"Billing Record ID: [green]{result.billing_record_id}[/green]\nTotal Charge: [green]${result.total_charge}[/green]")
        elif result.status == "failed":
            print_error("Batch processing failed", result.error_message)
            raise SystemExit(1)
        else:
            console.print(f"Status: {result.status}")
    except Exception as e:
        print_error("Failed to submit usage", str(e))
        raise SystemExit(1)

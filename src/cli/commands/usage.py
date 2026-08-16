# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage CLI commands — ROIaaS Phase 4 + C5 unit-economics extension.

Provides Typer app with subcommand:
  usage report   — table or JSON, optionally augmented with CAC/LTV/MRR
  usage check    — quick remaining-credit check
  usage export   — dump events to JSONL file

JSON contract (existing keys untouched):

  {
    "licenseKeyHash": "...",
    "generatedAt": "...",
    "period": "...",
    "totalCreditsUsed": 42,
    "eventCount": 56,
    "breakdown": {"cook": 14, ...},
    # new under --unit-economics:
    "unitEconomics": {
      "cacVnd": 512000,
      "ltvVnd": 2048000,
      "mrrVnd": 299000,
      "method": "industry_average"
    }
  }
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from typer import Typer, Option
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.services.metering import UNIT_ECON_CAC_VND, UNIT_ECON_LTV_VND, UNIT_ECON_MRR_VND

app = Typer(name="usage", help="Usage tracking and unit economics")
console = Console()


@app.command(name="report")
def usage_report(
    days: int = Option(7, "--days", "-d", help="Number of days to report"),
    json_output: bool = Option(False, "--json", "-j", help="Export as JSON"),
    unit_economics: bool = Option(
        False, "--unit-economics", "-e", help="Append CAC/LTV/MRR to JSON"
    ),
    license_key: Optional[str] = Option(
        None,
        "--license",
        "-l",
        help="License key (defaults to RAAS_LICENSE_KEY env var)",
    ),
) -> None:
    """Usage report for a license key.

    Adds unit-economics (CAC, LTV, MRR) to JSON output when ``-e`` is passed.
    Table output is intentionally unchanged — unit-economics is purposely
    structured data, not a human panel.
    """
    current_license = license_key or os.getenv("RAAS_LICENSE_KEY")
    if not current_license:
        console.print(
            Panel(
                "[bold red]No license key[/bold red]\n\n"
                "Set [green]RAAS_LICENSE_KEY[/green] env var or use [green]--license[/green] flag.",
                title="License required",
                border_style="red",
            )
        )
        raise SystemExit(1)

    try:
        from src.raas.credit_metering_middleware import CreditMeter

        meter = CreditMeter()
        summary = meter.get_usage_summary(current_license, period="daily")
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]Error reading usage:[/bold red] {exc}")
        raise SystemExit(1)

    now = datetime.now(timezone.utc)
    if json_output:
        payload: dict = {
            "licenseKeyHash": current_license[:8] + "..." + current_license[-4:],
            "generatedAt": now.isoformat(),
            "period": f"Last {days} days",
            "totalCreditsUsed": summary.total_credits_used,
            "eventCount": summary.event_count,
            "breakdown": summary.breakdown,
        }
        if unit_economics:
            payload["unitEconomics"] = {
                "cacVnd": UNIT_ECON_CAC_VND,
                "ltvVnd": UNIT_ECON_LTV_VND,
                "mrrVnd": UNIT_ECON_MRR_VND,
                "method": "industry_average",
            }
        console.print(json.dumps(payload, indent=2))
        return

    # Rich table (no unit-economics block — pure human-readable)
    console.print(
        Panel(
            f"[bold cyan]Usage: {current_license[:8]}...{current_license[-4:]}[/bold cyan]\n"
            f"Period: Last {days} days | {now.strftime('%Y-%m-%d %H:%M')} UTC",
            border_style="cyan",
        )
    )
    tbl = Table(show_header=True, header_style="bold cyan")
    tbl.add_column("Metric", style="cyan")
    tbl.add_column("Value", style="green")
    tbl.add_column("Details", style="dim")
    tbl.add_row(
        "Events",
        str(summary.event_count),
        "Commands + agents + pipelines",
    )
    tbl.add_row(
        "Credits used",
        str(summary.total_credits_used),
        "MCU consumed",
    )
    console.print(tbl)

    if summary.breakdown:
        bd = Table(show_header=True, header_style="bold green")
        bd.add_column("Task type", style="green")
        bd.add_column("Credits", style="cyan", justify="right")
        for task_type, credits in sorted(
            summary.breakdown.items(), key=lambda kv: kv[1], reverse=True
        ):
            bd.add_row(task_type, str(credits))
        console.print(bd)


@app.command(name="check")
def usage_check(
    license_key: Optional[str] = Option(
        None,
        "--license",
        "-l",
        help="License key (defaults to RAAS_LICENSE_KEY env var)",
    ),
) -> None:
    """Quick quota check: exit 0 if credits remain, 1 if exhausted."""
    current_license = license_key or os.getenv("RAAS_LICENSE_KEY")
    if not current_license:
        console.print("[bold red]No license key[/bold red]")
        raise SystemExit(1)

    try:
        from src.raas.credit_metering_middleware import CreditMeter

        meter = CreditMeter()
        balance = meter._credit_store.get_balance(current_license)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1)

    if balance > 0:
        console.print(f"[bold green]✓ Quota available[/bold green] — {balance} MCU remaining")
        raise SystemExit(0)
    console.print("[bold red]✗ Quota exhausted[/bold red] — 0 MCU remaining")
    console.print("[dim]Upgrade tier or wait for monthly reset.[/dim]")
    raise SystemExit(1)


@app.command(name="export")
def usage_export(
    output: str = Option(
        str(Path.home() / ".mekong" / "raas" / "usage-export.json"),
        "--output",
        "-o",
        help="Output JSON file path",
    ),
    days: int = Option(30, "--days", "-d", help="Lookback window"),
    license_key: Optional[str] = Option(
        None,
        "--license",
        "-l",
        help="License key",
    ),
) -> None:
    """Export recent usage events to JSON."""
    current_license = license_key or os.getenv("RAAS_LICENSE_KEY")
    if not current_license:
        console.print("[bold red]No license key[/bold red]")
        raise SystemExit(1)

    try:
        from src.raas.credit_metering_middleware import CreditMeter

        meter = CreditMeter()
        events = meter.list_events(current_license, limit=1000)

        out = Path(output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "licenseKeyHash": current_license[:8] + "..." + current_license[-4:],
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "periodDays": days,
            "eventCount": len(events),
            "events": [
                {
                    "id": e.id,
                    "tenantId": e.tenant_id,
                    "missionId": e.mission_id,
                    "taskType": e.task_type,
                    "creditsUsed": e.credits_used,
                    "timestamp": e.timestamp,
                }
                for e in events
            ],
        }
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.print(
            Panel(
                f"[bold green]✓ Exported {len(events)} events[/bold green]\n\n"
                f"Path: [cyan]{out}[/cyan]\nSize: {out.stat().st_size / 1024:.1f} KB",
                title="Usage export complete",
                border_style="green",
            )
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1)

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helpers for Usage Tracking CLI Commands."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from rich.panel import Panel
from rich.table import Table


def _mod():
    import src.commands.usage_commands as mod

    return mod


def render_usage_report(current_license: str, summary, days: int, json_output: bool) -> None:
    """Render usage report in JSON or rich table format."""
    m = _mod()
    if json_output:
        output = {
            "licenseKeyHash": current_license[:8] + "..." + current_license[-4:],
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "period": f"Last {days} days",
            "totalCreditsUsed": summary.total_credits_used,
            "eventCount": summary.event_count,
            "breakdown": summary.breakdown,
        }
        m.console.print(json.dumps(output, indent=2))
        return

    m.console.print(
        Panel(
            f"[bold cyan]Usage Report: {current_license[:8]}...{current_license[-4:]}[/bold cyan]\n"
            f"Period: Last {days} days | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            border_style="cyan",
        )
    )

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Details", style="dim")

    table.add_row(
        "Total Events",
        str(summary.event_count),
        "Commands + Agents + Pipelines",
    )
    table.add_row(
        "Credits Used",
        str(summary.total_credits_used),
        "MCU consumed",
    )
    m.console.print(table)

    if summary.breakdown:
        breakdown_table = Table(show_header=True, header_style="bold green")
        breakdown_table.add_column("Task Type", style="green")
        breakdown_table.add_column("Count", style="cyan", justify="right")
        breakdown_table.add_column("Credits", style="yellow", justify="right")

        for task_type, credits in sorted(
            summary.breakdown.items(), key=lambda x: x[1], reverse=True
        ):
            breakdown_table.add_row(task_type, str(credits), str(credits))

        m.console.print(breakdown_table)

    free_tier_limit = 10
    within_limits = summary.event_count / days < free_tier_limit
    m.console.print(
        Panel(
            f"[bold]Free Tier Status:[/bold]\n"
            f"Daily Limit: {free_tier_limit} commands\n"
            f"Average: {summary.event_count / days:.1f} events/day\n"
            + ("[green]✓ Within limits[/green]" if within_limits else "[red]⚠ Approaching limit[/red]"),
            border_style="green" if within_limits else "yellow",
        )
    )


def write_usage_export(current_license: str, events: list, output: str, days: int) -> None:
    """Write usage export JSON and print confirmation panel."""
    m = _mod()
    output_path = Path(output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export_data = {
        "licenseKeyHash": current_license[:8] + "..." + current_license[-4:],
        "generatedAt": datetime.utcnow().isoformat() + "Z",
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

    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2)

    m.console.print(
        Panel(
            f"[bold green]✓ Exported {len(events)} events[/bold green]\n\n"
            f"Path: [cyan]{output_path}[/cyan]\n"
            f"Size: {output_path.stat().st_size / 1024:.1f} KB",
            title="Usage Export Complete",
            border_style="green",
        )
    )

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Violations command for Debug Rate Limits CLI."""

import asyncio
import json
import sys
from typing import Optional

from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.debug_rate_limits_status import _format_timestamp


def _facade():
    return sys.modules["src.commands.debug_rate_limits"]


def list_violations(
    tenant_id: Optional[str] = typer.Option(None, "--tenant", "-t", help="Filter by tenant ID"),
    hours: int = typer.Option(24, "--hours", "-h", help="Hours of history"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List rate limit violations (429 responses)."""
    from src.db.database import close_database, init_database
    from src.db.tier_config_repository import get_repository

    f = _facade()

    async def _get_violations():
        await init_database()
        repo = get_repository()
        db = repo._db

        where_clause = "WHERE tenant_id = $1" if tenant_id else ""
        tenant_param = (tenant_id,) if tenant_id else ()

        query = f"""
            SELECT
                id, tenant_id, tier, endpoint, preset,
                retry_after, created_at
            FROM rate_limit_events
            {where_clause}
              AND event_type = 'rate_limited'
              AND created_at > NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 100
        """ % hours

        events = await db.fetch_all(query, tenant_param)

        agg_tenant_query = """
            SELECT tenant_id, COUNT(*) as violations
            FROM rate_limit_events
            WHERE event_type = 'rate_limited'
              AND created_at > NOW() - INTERVAL '%s hours'
            GROUP BY tenant_id
            ORDER BY violations DESC
        """ % hours

        by_tenant = await db.fetch_all(agg_tenant_query)

        agg_endpoint_query = f"""
            SELECT endpoint, COUNT(*) as violations
            FROM rate_limit_events
            {where_clause}
              AND event_type = 'rate_limited'
              AND created_at > NOW() - INTERVAL '%s hours'
            GROUP BY endpoint
            ORDER BY violations DESC
            LIMIT 10
        """ % hours

        by_endpoint = await db.fetch_all(agg_endpoint_query, tenant_param)
        total = sum(t["violations"] for t in by_tenant)

        return {
            "events": events,
            "by_tenant": by_tenant,
            "by_endpoint": by_endpoint,
            "total": total,
        }

    try:
        result = asyncio.run(_get_violations())
    except Exception as e:
        f.console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        asyncio.run(close_database())

    if as_json:
        output = {
            "period_hours": hours,
            "total_violations": result["total"],
            "by_tenant": [dict(t) for t in result["by_tenant"]],
            "by_endpoint": [dict(e) for e in result["by_endpoint"]],
            "recent_violations": [
                {
                    "tenant_id": e["tenant_id"],
                    "tier": e["tier"],
                    "endpoint": e["endpoint"],
                    "preset": e["preset"],
                    "retry_after": e["retry_after"],
                    "timestamp": e["created_at"],
                }
                for e in result["events"]
            ],
        }
        f.console.print(json.dumps(output, indent=2))
        return

    f.console.print(Panel(f"[bold red]Rate Limit Violations[/bold red]\n[cyan]Period:[/cyan] Last {hours}h | [cyan]Total:[/cyan] {result['total']} violations", border_style="red"))

    if result["total"] == 0:
        f.console.print("[green]No violations in this period![/green]")
        return

    f.console.print("\n[bold yellow]By Tenant:[/bold yellow]")
    if result["by_tenant"]:
        table = Table(show_header=True)
        table.add_column("Tenant ID", style="cyan")
        table.add_column("Violations", style="red", justify="right")
        for row in result["by_tenant"]:
            table.add_row(row["tenant_id"], str(row["violations"]))
        f.console.print(table)
    else:
        f.console.print("[dim]No tenant data[/dim]")

    f.console.print("\n[bold yellow]Top Violated Endpoints:[/bold yellow]")
    if result["by_endpoint"]:
        table = Table(show_header=True)
        table.add_column("Endpoint", style="white")
        table.add_column("Violations", style="red", justify="right")
        for row in result["by_endpoint"]:
            endpoint = row["endpoint"]
            if len(endpoint) > 40:
                endpoint = endpoint[:37] + "..."
            table.add_row(endpoint, str(row["violations"]))
        f.console.print(table)
    else:
        f.console.print("[dim]No endpoint data[/dim]")

    if result["events"]:
        f.console.print(f"\n[bold yellow]Recent Violations (Last {len(result['events'])})[/bold yellow]:")
        table = Table(show_header=True, show_lines=True)
        table.add_column("Time", style="dim", width=19)
        table.add_column("Tenant", style="cyan", width=20)
        table.add_column("Endpoint", style="white", width=35)
        table.add_column("Preset", style="yellow", width=15)
        table.add_column("Retry After", style="red", width=12)

        for event in result["events"]:
            table.add_row(
                _format_timestamp(event["created_at"]),
                event["tenant_id"],
                event["endpoint"][:35],
                event["preset"],
                f"{event['retry_after']}s" if event["retry_after"] else "-",
            )
        f.console.print(table)

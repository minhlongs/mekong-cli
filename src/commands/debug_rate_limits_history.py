# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""History and overrides commands for Debug Rate Limits CLI."""

import asyncio
import json
import sys
from typing import Optional

from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.debug_rate_limits_status import (
    _format_tier_display,
    _format_timestamp,
)


def _facade():
    return sys.modules["src.commands.debug_rate_limits"]


def view_history(
    tenant_id: str = typer.Argument(..., help="Tenant ID"),
    hours: int = typer.Option(24, "--hours", "-h", help="Hours of history"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max events to show"),
    event_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by event type"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """View rate limit event history for a tenant."""
    from src.db.database import close_database, init_database
    from src.db.tier_config_repository import get_repository

    f = _facade()

    async def _get_history():
        await init_database()
        repo = get_repository()
        db = repo._db

        query = (
            "SELECT id, tenant_id, tier, endpoint, preset, event_type, quota_limit, "
            "quota_remaining, quota_utilization_pct, response_status, retry_after, created_at "
            "FROM rate_limit_events WHERE tenant_id = $1 AND created_at > NOW() - INTERVAL '%s hours'" % hours
        )
        params = [tenant_id]
        if event_type:
            query += " AND event_type = $2"
            params.append(event_type)

        query += " ORDER BY created_at DESC LIMIT %s" % limit
        return await db.fetch_all(query, tuple(params))

    try:
        events = asyncio.run(_get_history())
    except Exception as e:
        f.console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        asyncio.run(close_database())

    if as_json:
        output = {
            "tenant_id": tenant_id, "hours": hours, "count": len(events),
            "events": [
                {
                    "timestamp": e["created_at"], "tier": e["tier"], "endpoint": e["endpoint"],
                    "preset": e["preset"], "event_type": e["event_type"], "quota_limit": e["quota_limit"],
                    "quota_remaining": e["quota_remaining"], "response_status": e["response_status"],
                    "retry_after": e["retry_after"],
                }
                for e in events
            ],
        }
        f.console.print(json.dumps(output, indent=2))
        return

    if not events:
        f.console.print(f"[yellow]No events found for tenant '{tenant_id}' in last {hours}h[/yellow]")
        return

    f.console.print(Panel(f"[bold cyan]Rate Limit History[/bold cyan]\n[cyan]Tenant:[/cyan] {tenant_id} | [cyan]Period:[/cyan] Last {hours}h | [cyan]Events:[/cyan] {len(events)}", border_style="cyan"))

    table = Table(show_header=True, show_lines=True)
    for col, st, w in [("Time", "dim", 19), ("Tier", "cyan", 15), ("Endpoint", "white", 30), ("Preset", "yellow", 15), ("Event", "green", 18), ("Status", "white", 8), ("Retry", "red", 8)]:
        table.add_column(col, style=st, width=w)

    event_style = {"override_applied": "blue", "request_allowed": "green", "rate_limited": "red"}
    for event in events:
        event_color = event_style.get(event["event_type"], "white")
        table.add_row(
            _format_timestamp(event["created_at"]), _format_tier_display(event["tier"]),
            event["endpoint"][:30], event["preset"], f"[{event_color}]{event['event_type']}[/{event_color}]",
            str(event["response_status"]) if event["response_status"] else "-",
            f"{event['retry_after']}s" if event["retry_after"] else "-",
        )

    f.console.print(table)
    f.console.print(f"[dim]Showing {len(events)} events (use --limit to adjust)[/dim]")


def list_overrides(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all tenant rate limit overrides."""
    from src.db.database import close_database, init_database
    from src.db.tier_config_repository import get_repository

    f = _facade()

    async def _get_overrides():
        await init_database()
        return await get_repository().get_all_tenant_overrides()

    try:
        overrides = asyncio.run(_get_overrides())
    except Exception as e:
        f.console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        asyncio.run(close_database())

    if as_json:
        output = {
            "count": len(overrides),
            "overrides": [
                {
                    "tenant_id": o.tenant_id, "tier": o.tier, "preset": o.preset,
                    "custom_limit": o.custom_limit, "custom_window": o.custom_window, "expires_at": o.expires_at,
                }
                for o in overrides
            ],
        }
        f.console.print(json.dumps(output, indent=2))
        return

    if not overrides:
        f.console.print("[yellow]No tenant overrides configured.[/yellow]")
        return

    f.console.print(Panel(f"[bold cyan]Tenant Rate Limit Overrides[/bold cyan]\n[cyan]Total:[/cyan] {len(overrides)}", border_style="cyan"))
    table = Table(show_header=True, show_lines=True)
    for col, st, j in [("Tenant ID", "cyan", "left"), ("Preset", "green", "left"), ("Custom Limit", "yellow", "right"), ("Window (s)", "magenta", "right"), ("Tier Override", "blue", "left"), ("Expires", "red", "left")]:
        table.add_column(col, style=st, justify=j)

    for override in overrides:
        expires = _format_timestamp(override.expires_at) if override.expires_at else "Never"
        if override.is_expired():
            expires = f"[dim]{expires} (expired)[/dim]"
        table.add_row(
            override.tenant_id, override.preset, str(override.custom_limit) if override.custom_limit else "-",
            str(override.custom_window), override.tier or "-", expires,
        )
    f.console.print(table)

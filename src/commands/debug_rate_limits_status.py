# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Status command and format helpers for Debug Rate Limits CLI."""

import asyncio
from datetime import datetime
import json
import sys

from rich.panel import Panel
from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.debug_rate_limits"]


def _format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display."""
    try:
        ts = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return timestamp_str


def _format_tier_display(tier: str) -> str:
    """Format tier name for display."""
    if "custom" in tier.lower():
        return f"{tier.split()[0]} (custom)"
    return tier


def check_status(
    tenant_id: str = typer.Argument(..., help="Tenant ID to check"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check current rate limit status for a tenant."""
    from src.db.database import close_database, init_database
    from src.db.tier_config_repository import get_repository

    f = _facade()

    async def _get_status():
        await init_database()
        repo = get_repository()
        overrides = {}
        for preset in ("auth_login", "auth_callback", "auth_refresh", "api_default"):
            override = await repo.get_tenant_override(tenant_id, preset)
            if override and not override.is_expired():
                overrides[preset] = override

        query = (
            "SELECT preset, event_type, quota_limit, quota_remaining, quota_utilization_pct, created_at "
            "FROM rate_limit_events WHERE tenant_id = $1 AND created_at > NOW() - INTERVAL '5 minutes' "
            "ORDER BY created_at DESC LIMIT 100"
        )
        events = await repo._db.fetch_all(query, (tenant_id,))
        utilization = {}
        for event in events:
            preset = event["preset"]
            if preset not in utilization:
                utilization[preset] = {"requests": 0, "limited": 0, "last_limit": None, "last_remaining": None, "utilization": 0.0}
            utilization[preset]["requests"] += 1
            if event["event_type"] == "rate_limited":
                utilization[preset]["limited"] += 1
            if event["quota_remaining"] is not None:
                utilization[preset]["last_remaining"] = event["quota_remaining"]
                utilization[preset]["last_limit"] = event["quota_limit"]
                utilization[preset]["utilization"] = float(event["quota_utilization_pct"] or 0)

        if overrides:
            tiers = set(o.tier for o in overrides.values() if o.tier)
            effective_tier = list(tiers)[0] if len(tiers) == 1 else "mixed (custom)"
        else:
            effective_tier = events[0].get("tier", "unknown") if events else "unknown"

        return {
            "tenant_id": tenant_id, "effective_tier": effective_tier,
            "has_custom_overrides": len(overrides) > 0, "overrides": overrides,
            "presets": utilization, "recent_events_count": len(events),
        }

    try:
        result = asyncio.run(_get_status())
    except Exception as e:
        f.console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        asyncio.run(close_database())

    if as_json:
        output = {
            "tenant_id": result["tenant_id"],
            "tier": result["effective_tier"],
            "has_custom_overrides": result["has_custom_overrides"],
            "overrides": {
                preset: {"custom_limit": o.custom_limit, "custom_window": o.custom_window, "expires_at": o.expires_at}
                for preset, o in result["overrides"].items()
            },
            "quota_utilization": {
                preset: {
                    "requests_5min": data["requests"], "limited_count": data["limited"],
                    "remaining": data["last_remaining"], "utilization_pct": round(data["utilization"], 2),
                }
                for preset, data in result["presets"].items()
            },
        }
        f.console.print(json.dumps(output, indent=2))
        return

    f.console.print(Panel(f"[bold cyan]Rate Limit Status[/bold cyan]\n[cyan]Tenant:[/cyan] {tenant_id}", border_style="cyan"))
    tier_display = _format_tier_display(result["effective_tier"])
    if result["has_custom_overrides"]:
        tier_display = f"[green]{tier_display}[/green] [dim](custom overrides active)[/dim]"
    f.console.print(f"[bold]Effective Tier:[/bold] {tier_display}\n")

    if result["overrides"]:
        f.console.print("[bold yellow]Custom Overrides:[/bold yellow]")
        table = Table(show_header=True, show_lines=True)
        for col, st in [("Preset", "cyan"), ("Custom Limit", "green"), ("Window (s)", "yellow"), ("Expires", "red")]:
            table.add_column(col, style=st)
        for preset, override in result["overrides"].items():
            expires = _format_timestamp(override.expires_at) if override.expires_at else "Never"
            table.add_row(preset, str(override.custom_limit), str(override.custom_window), expires)
        f.console.print(table)
        f.console.print()

    if result["presets"]:
        f.console.print("[bold blue]Quota Utilization (Last 5 minutes)[/bold blue]")
        table = Table(show_header=True)
        for col, st in [("Preset", "cyan"), ("Requests", "white"), ("Limited", "red"), ("Remaining", "green"), ("Utilization", "yellow")]:
            table.add_column(col, style=st)
        for preset, data in result["presets"].items():
            pct = data["utilization"]
            c = "green" if pct < 50 else "yellow" if pct < 80 else "red"
            table.add_row(preset, str(data["requests"]), str(data["limited"]), str(data["last_remaining"] or "-"), f"[{c}]{pct:.1f}%[/{c}]")
        f.console.print(table)
    else:
        f.console.print("[yellow]No recent activity (last 5 minutes)[/yellow]")

    f.console.print()

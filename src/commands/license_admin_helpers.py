# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Formatting and view helpers for License Admin CLI."""

from __future__ import annotations

import asyncio
from datetime import datetime
from rich.panel import Panel
from rich.table import Table


def _mod():
    import src.commands.license_admin as mod

    return mod


def get_status_badge(status: str) -> str:
    """Get colored status badge."""
    badges = {
        "active": "[green]● Active[/green]",
        "revoked": "[red]● Revoked[/red]",
        "expired": "[yellow]● Expired[/yellow]",
        "cancelled": "[dim]● Cancelled[/dim]",
    }
    return badges.get(status, f"● {status}")


def format_date(dt, short: bool = False) -> str:
    """Format datetime for display."""
    if not dt:
        return "N/A"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M" if not short else "%m-%d %H:%M")
    return str(dt)[:16] if not short else str(dt)[5:16]


def format_details(details: dict) -> str:
    """Format audit details for display."""
    if not details:
        return ""
    parts = []
    if "tier" in details:
        parts.append(f"tier={details['tier']}")
    if "reason" in details:
        parts.append(f"reason={details['reason'][:20]}")
    if "quantity" in details:
        parts.append(f"qty={details['quantity']}")
    return " | ".join(parts)


def run_view_audit_logs(
    action: str | None,
    entity_type: str | None,
    days: int,
    limit: int,
) -> None:
    """Fetch and render audit logs."""
    m = _mod()

    async def _view():
        service = m.get_admin_service()
        return await service.get_audit_logs(
            action=action,
            entity_type=entity_type,
            days=days,
            limit=limit,
        )

    logs = asyncio.run(_view())

    if not logs:
        m.console.print("[yellow]⚠️  No audit logs found[/yellow]")
        return

    table = Table(title="📜 Audit Logs", show_lines=True)
    table.add_column("Time", style="cyan")
    table.add_column("Action")
    table.add_column("Entity")
    table.add_column("Entity ID")
    table.add_column("Actor")
    table.add_column("IP")
    table.add_column("Details")

    for log in logs:
        action_style = "green" if log.get("action") == "CREATE" else "red"
        table.add_row(
            format_date(log.get("created_at")),
            f"[{action_style}]{log.get('action')}[/{action_style}]",
            log.get("entity_type", "N/A"),
            str(log.get("entity_id", "N/A"))[:20],
            log.get("actor_email", "N/A"),
            log.get("actor_ip", "N/A"),
            format_details(log.get("details", {})),
        )

    m.console.print(table)


def run_interactive_dashboard() -> None:
    """Render interactive admin dashboard summary."""
    m = _mod()
    m.console.print(
        Panel.fit(
            "[bold cyan]🔐 RAAS License Admin Dashboard[/bold cyan]\n"
            "[dim]Phase 2 - License Management[/dim]",
            border_style="cyan",
        )
    )
    m.console.print()

    async def get_summary():
        service = m.get_admin_service()
        licenses = await service.list_licenses(page=1, page_size=1000)
        logs = await service.get_audit_logs(days=7, limit=100)
        return licenses, logs

    licenses, logs = asyncio.run(get_summary())

    total_licenses = licenses["total"]
    active_count = sum(
        1 for license in licenses["items"] if license.get("status") == "active"
    )
    revoked_count = sum(
        1 for license in licenses["items"] if license.get("status") == "revoked"
    )
    recent_actions = len(logs)

    m.console.print(
        Panel(
            f"[bold]Total Licenses:[/bold] {total_licenses}\n"
            f"[green]● Active:[/green] {active_count}\n"
            f"[red]● Revoked:[/red] {revoked_count}\n"
            f"[blue]● Actions (7 days):[/blue] {recent_actions}",
            title="📊 Summary",
            border_style="blue",
        )
    )

    m.console.print("\n[bold]Recent Activity:[/bold]")
    for log in logs[:5]:
        m.console.print(
            f"  {format_date(log.get('created_at'), short=True)} | "
            f"{log.get('action')} | {log.get('entity_type')} | "
            f"{log.get('actor_email')}"
        )

    m.console.print(
        "\n[dim]Use commands: mekong license-admin list|create|revoke|audit[/dim]"
    )

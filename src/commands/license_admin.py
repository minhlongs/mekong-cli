# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
License Admin CLI — ROIaaS Phase 2

Terminal-based admin dashboard for license management.
"""

import asyncio
import os
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from src.api.admin_license_service import get_admin_service
from src.commands.license_admin_helpers import (
    format_date,
    format_details,
    get_status_badge,
    run_interactive_dashboard,
    run_view_audit_logs,
)

console = Console()
app = typer.Typer(help="License Admin Dashboard (Phase 2)")


@app.command("list")
def list_licenses(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    page_size: int = typer.Option(20, "--page-size", "-s", help="Items per page"),
    tier: str = typer.Option(None, "--tier", "-t", help="Filter by tier"),
    status: str = typer.Option(None, "--status", help="Filter by status"),
    email: str = typer.Option(None, "--email", "-e", help="Filter by email"),
) -> None:
    """List all licenses with pagination and filters."""

    async def _list():
        service = get_admin_service()
        return await service.list_licenses(
            page=page, page_size=page_size, tier=tier, status=status, email=email
        )

    licenses = asyncio.run(_list())
    table = Table(title="📋 License Keys", show_lines=True)
    for col, style in [("ID", "cyan"), ("Key", "dim"), ("Tier", None), ("Email", None), ("Status", None), ("Created", None), ("By", None)]:
        table.add_column(col, style=style)

    for lic in licenses["items"]:
        table.add_row(
            str(lic.get("id", "N/A")),
            lic.get("license_key", "N/A"),
            lic.get("tier", "unknown").upper(),
            lic.get("email", "N/A"),
            get_status_badge(lic.get("status", "unknown")),
            format_date(lic.get("created_at")),
            lic.get("created_by", "system"),
        )

    console.print(table)
    console.print(
        Panel(
            f"Page {licenses['page']}/{licenses['total_pages']} | "
            f"Total: {licenses['total']} | Showing: {len(licenses['items'])} items",
            border_style="blue",
        )
    )


@app.command("create")
def create_license(
    tier: str = typer.Option("trial", "--tier", "-t", help="License tier"),
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    days: int = typer.Option(None, "--days", "-d", help="Expiry days (trial only)"),
    quantity: int = typer.Option(1, "--quantity", "-q", help="Number of keys"),
    notes: str = typer.Option(None, "--notes", "-n", help="Optional notes"),
) -> None:
    """Create new license key(s)."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@mekong.dev")
    actor_ip = os.getenv("ACTOR_IP", "127.0.0.1")

    async def _create():
        service = get_admin_service()
        return await service.create_license(
            tier=tier, email=email, days=days, quantity=quantity,
            notes=notes, created_by=admin_email, actor_ip=actor_ip,
        )

    console.print(Panel(f"Creating {quantity} license key(s)...", border_style="cyan"))
    result = asyncio.run(_create())

    if result["keys"]:
        keys_text = "\n".join(result["keys"])
        console.print(
            Panel(
                f"[bold green]✅ Created {len(result['keys'])} license key(s)[/bold green]\n\n"
                f"[bold]Tier:[/bold] {tier.upper()}\n[bold]Email:[/bold] {email}\n"
                f"[bold]Keys:[/bold]\n[cyan]{keys_text}[/cyan]",
                title="License Created",
                border_style="green",
            )
        )
    else:
        console.print(Panel("[bold red]❌ Failed to create license keys[/bold red]", border_style="red"))


@app.command("revoke")
def revoke_license(
    key_id: str = typer.Argument(..., help="Key ID to revoke"),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason for revocation"),
    notes: str = typer.Option(None, "--notes", "-n", help="Optional notes"),
) -> None:
    """Revoke a license key."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@mekong.dev")
    actor_ip = os.getenv("ACTOR_IP", "127.0.0.1")

    if not Confirm.ask(f"[yellow]⚠️  Revoke key {key_id}?[/yellow]"):
        console.print("[dim]Cancelled[/dim]")
        return

    async def _revoke():
        service = get_admin_service()
        return await service.revoke_license(
            key_id=key_id, reason=reason, revoked_by=admin_email, actor_ip=actor_ip, notes=notes
        )

    result = asyncio.run(_revoke())
    if result.get("success"):
        console.print(
            Panel(
                f"[bold green]✅ License revoked[/bold green]\n\n"
                f"[bold]Key ID:[/bold] {key_id}\n[bold]Reason:[/bold] {reason}",
                title="License Revoked",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(f"[bold red]❌ {result.get('error', 'Unknown error')}[/bold red]", border_style="red")
        )


@app.command("audit")
def view_audit_logs(
    action: str = typer.Option(None, "--action", "-a", help="Filter by action"),
    entity_type: str = typer.Option(None, "--entity-type", "-e", help="Filter by entity type"),
    days: int = typer.Option(30, "--days", "-d", help="Last N days"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """View audit logs."""
    run_view_audit_logs(action=action, entity_type=entity_type, days=days, limit=limit)


@app.command("dashboard")
def interactive_dashboard() -> None:
    """Launch interactive admin dashboard."""
    run_interactive_dashboard()


__all__ = [
    "app",
    "console",
    "create_license",
    "datetime",
    "format_date",
    "format_details",
    "get_admin_service",
    "get_status_badge",
    "interactive_dashboard",
    "list_licenses",
    "revoke_license",
    "view_audit_logs",
]

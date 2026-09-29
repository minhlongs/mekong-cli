# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vendor marketplace CLI — Sovereign third-party agent and provider governance.

Exposes ``mekong vendor`` sub-app with:
- ``overview``           show marketplace metrics and active vendors
- ``onboard <name>``     register a new vendor or provider
- ``list``               show registered vendors with filtering
- ``delist <name>``      remove or sandbox a vendor
- ``audit <name>``       run automated compliance and boundary audit
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.vendor_engine import get_vendor_engine

logger = logging.getLogger(__name__)
console = Console()

app = typer.Typer(
    name="vendor",
    help="🏛️ Vendor Marketplace & Provider Governance: Onboard, audit, list, and delist ecosystem extensions",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def vendor_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON marketplace overview",
    ),
) -> None:
    """🏛️ Vendor Marketplace Overview: Ecosystem metrics, trust scores, and active providers."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_vendor_engine()
    status = engine.get_status()
    vendors = engine.list_vendors(limit=10)

    if json_output:
        overview = {
            **status,
            "recent_vendors": vendors,
        }
        print(json.dumps(overview, indent=2))
        return

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="left")
    grid.add_row(
        f"🏛️ [bold]Total Providers:[/bold] [bold cyan]{status['total_vendors']}[/bold cyan]",
        f"🟢 [bold]Active Extensions:[/bold] [bold green]{status['active_vendors']}[/bold green]",
    )
    grid.add_row(
        f"🔍 [bold]Audits Performed:[/bold] [bold yellow]{status['total_audits_performed']}[/bold yellow]",
        f"⚡ [bold]Engine Status:[/bold] [bold green]{status['status']}[/bold green]",
    )

    console.print(
        Panel(
            grid,
            title="[bold green]🏛️ Mekong Sovereign Vendor Marketplace[/bold green]",
            subtitle=f"[dim]DB: {status['db_path']}[/dim]",
            border_style="green",
            box=ROUNDED,
        )
    )

    table = Table(
        title="🌟 Featured Ecosystem Extensions & Providers",
        box=ROUNDED,
        header_style="bold yellow",
    )
    table.add_column("Vendor Name", style="bold cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Version", justify="center")
    table.add_column("Trust Score", justify="right", style="bold green")
    table.add_column("SLA", justify="right")
    table.add_column("Description", style="dim")

    for v in vendors:
        table.add_row(
            v["name"],
            v["vendor_type"],
            v["version"],
            f"{v['trust_score']:.1f}",
            f"{v['sla_percent']:.2f}%",
            v["description"][:50],
        )
    console.print(table)


@app.command(name="onboard")
def onboard(
    name: str = typer.Argument(..., help="Vendor name / plugin ID"),
    description: str = typer.Option("", "--description", "-d", help="Short description of the extension"),
    vendor_type: str = typer.Option("agent", "--type", "-t", help="Vendor type: agent | provider | hook | recipe | model_router"),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Semantic version"),
    author: str = typer.Option("Community Builder", "--author", "-a", help="Author or organization"),
    trust_score: float = typer.Option(85.0, "--trust", "-s", help="Initial trust score (0-100)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """Register and onboard a new vendor into the marketplace."""
    engine = get_vendor_engine()
    vendor = engine.onboard_vendor(
        name=name,
        vendor_type=vendor_type,
        version=version,
        description=description,
        author=author,
        trust_score=trust_score,
    )

    if json_output:
        print(json.dumps(vendor, indent=2))
        return

    console.print(
        Panel(
            f"[bold]Vendor Name:[/bold] [cyan]{vendor['name']}[/cyan] ({vendor['vendor_type']})\n"
            f"[bold]Version:[/bold] {vendor['version']} | [bold]Author:[/bold] {vendor['author']}\n"
            f"[bold]Trust Score:[/bold] [green]{vendor['trust_score']:.1f}[/green] | [bold]Status:[/bold] [green]{vendor['status']}[/green]\n"
            f"[bold]Capabilities:[/bold] {', '.join(vendor['capabilities'])}\n"
            f"[bold]Description:[/bold] {vendor['description']}",
            title="✅ Vendor Onboarded Successfully",
            border_style="green",
            box=ROUNDED,
        )
    )


@app.command(name="list")
def list_vendors(
    vendor_type: str = typer.Option("all", "--type", "-t", help="Filter by vendor type"),
    status: str = typer.Option("all", "--status", "-s", help="Filter by status: active | pending_audit | delisted"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results to display"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """List registered vendors with optional type and status filtering."""
    engine = get_vendor_engine()
    vendors = engine.list_vendors(vendor_type=vendor_type, status=status, limit=limit)

    if json_output:
        print(json.dumps(vendors, indent=2))
        return

    if not vendors:
        console.print("[yellow]No vendors found matching criteria.[/yellow]")
        return

    table = Table(
        title="🏛️ Registered Marketplace Vendors",
        box=ROUNDED,
        header_style="bold yellow",
    )
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Version", justify="center")
    table.add_column("Trust Score", justify="right", style="bold green")
    table.add_column("Status", justify="center")
    table.add_column("Author")

    for v in vendors:
        status_style = "green" if v["status"] == "active" else "red"
        table.add_row(
            v["id"],
            v["name"],
            v["vendor_type"],
            v["version"],
            f"{v['trust_score']:.1f}",
            f"[{status_style}]{v['status']}[/{status_style}]",
            v["author"],
        )
    console.print(table)


@app.command(name="delist")
def delist(
    name: str = typer.Argument(..., help="Vendor name or ID to remove"),
    reason: str = typer.Option("", "--reason", "-r", help="Reason for delisting or deprecation"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """Remove or sandbox a vendor from the marketplace."""
    engine = get_vendor_engine()
    res = engine.delist_vendor(name_or_id=name, reason=reason)

    if json_output:
        print(json.dumps(res, indent=2))
        return

    if not res.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {res.get('error')}")
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"[bold]Vendor:[/bold] [cyan]{res['name']}[/cyan] ({res['vendor_id']})\n"
            f"[bold]Status:[/bold] [red]{res['status'].upper()}[/red]\n"
            f"[bold]Reason:[/bold] {res['reason']}",
            title="🛑 Vendor Delisted",
            border_style="red",
            box=ROUNDED,
        )
    )


@app.command(name="audit")
def audit(
    name: str = typer.Argument(..., help="Vendor name or ID to assess"),
    audit_type: str = typer.Option("security", "--type", "-t", help="Audit type: security | compliance | performance | boundary"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """Perform automated compliance, security, and boundary assessment on a vendor."""
    engine = get_vendor_engine()
    res = engine.audit_vendor(name_or_id=name, audit_type=audit_type)

    if json_output:
        print(json.dumps(res, indent=2))
        return

    if "error" in res:
        console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
        raise typer.Exit(code=1)

    status_color = "green" if res["status"] == "PASSED" else "yellow"
    panel = Panel(
        f"[bold]Audit ID:[/bold] {res['audit_id']}\n"
        f"[bold]Vendor:[/bold] [cyan]{res['name']}[/cyan] | [bold]Type:[/bold] {res['audit_type']}\n"
        f"[bold]Audit Score:[/bold] [bold {status_color}]{res['audit_score']:.1f} / 100.0[/bold {status_color}] | "
        f"[bold]Verdict:[/bold] [bold {status_color}]{res['status']}[/bold {status_color}]\n\n"
        f"[bold]Key Findings:[/bold]\n" + "\n".join(f"• {f}" for f in res['findings']),
        title="🔍 Vendor Assessment Report",
        border_style=status_color,
        box=ROUNDED,
    )
    console.print(panel)


# Registration hook
def register(cli: typer.Typer) -> None:
    cli.add_typer(app, name="vendor", help="🏛️ Vendor Marketplace & Provider Governance")

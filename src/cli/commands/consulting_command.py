# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/consulting_command.py — CLI command surface for AI Agent Consulting & Advisory Suite.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.consulting_engine import get_consulting_engine

console = Console()
consulting_app = typer.Typer(
    name="consulting",
    help="💼 Consulting Suite: AI agent building service, pricing, proposals & B2B outreach",
    no_args_is_help=False,
)

engagement_app = typer.Typer(
    name="engagement",
    help="📋 Client consulting contract & engagement lifecycle management",
    no_args_is_help=False,
)
consulting_app.add_typer(engagement_app, name="engagement")


@consulting_app.callback(invoke_without_command=True)
def consulting_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON consulting business summary",
    ),
) -> None:
    """💼 Consulting Overview: Active contracts, pipeline value, realized revenue, and offerings."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_consulting_engine()
    status = engine.get_status()

    if json_output:
        print(json.dumps(status, indent=2))
        return

    pipeline = f"[bold green]${status['pipeline_value_usd']:,.2f} USD[/bold green]"
    realized = f"[bold cyan]${status['realized_revenue_usd']:,.2f} USD[/bold cyan]"

    body = (
        f"[bold cyan]💼 MEKONG ADVISORY & CONSULTING CONTROL PLANE[/bold cyan]\n"
        f"[dim]Active Engagements:[/dim]      [bold]{status['active_engagements']}[/bold] contracts\n"
        f"[dim]Completed Engagements:[/dim]   [dim]{status['completed_engagements']}[/dim] delivered\n"
        f"[dim]Active Pipeline Value:[/dim]   {pipeline}\n"
        f"[dim]Realized Revenue:[/dim]        {realized}\n\n"
        f"[bold]Standard Service Offerings:[/bold]\n"
        f"  • [yellow]audit[/yellow]        — AI Agent Architecture & Automation Audit ($500)\n"
        f"  • [yellow]custom_agent[/yellow] — Custom Domain Subagent Build ($2,000)\n"
        f"  • [yellow]full_stack[/yellow]   — Full Stack Agency OS Deployment ($5,000)\n"
        f"  • [yellow]retainer[/yellow]     — Autonomous Operations Retainer ($2,000/mo)"
    )

    console.print(Panel(body, title="Consulting Operations Dashboard", border_style="cyan", box=ROUNDED))


@consulting_app.command(name="pricing")
def consulting_pricing(
    currency: str = typer.Option(
        "USD",
        "--currency",
        "-c",
        help="Display pricing in USD or VND",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output service catalog and pricing as JSON",
    ),
) -> None:
    """💰 Show standardized AI agent consulting packages, pricing, and deliverables."""
    engine = get_consulting_engine()
    packages = engine.get_service_catalog(currency=currency)

    if json_output:
        print(json.dumps([p.to_dict() for p in packages], indent=2))
        return

    is_vnd = currency.upper() == "VND"
    table = Table(
        title=f"Mekong Consulting Service Offerings ({'VND' if is_vnd else 'USD'})",
        box=ROUNDED,
        border_style="cyan",
    )
    table.add_column("Tier", style="bold yellow", width=14)
    table.add_column("Service Offering", style="bold")
    table.add_column("Price", justify="right", width=16)
    table.add_column("Delivery Timeline", justify="center", width=18)
    table.add_column("Key Deliverables", style="dim")

    for p in packages:
        price_str = f"{p.price_vnd:,.0f} VND" if is_vnd else f"${p.price_usd:,.2f} USD"
        deliv_str = "; ".join(p.deliverables[:2])
        table.add_row(p.tier, p.title, price_str, p.delivery_time, deliv_str)

    console.print(table)


@consulting_app.command(name="proposal")
def consulting_proposal(
    prospect: str = typer.Argument(..., help="Prospect company / client name"),
    service: str = typer.Option(
        "custom_agent",
        "--service",
        "-s",
        help="Service tier (audit, custom_agent, full_stack, retainer)",
    ),
    requirements: str = typer.Option(
        "",
        "--requirements",
        "-r",
        help="Custom requirements / client problem statement",
    ),
    industry: str = typer.Option(
        "Technology",
        "--industry",
        "-i",
        help="Target prospect industry",
    ),
    budget: Optional[float] = typer.Option(
        None,
        "--budget",
        "-b",
        help="Custom contract budget in USD",
    ),
    save: bool = typer.Option(
        False,
        "--save",
        help="Save generated proposal markdown to proposals/",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Custom directory for saved proposal markdown files",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output structured proposal details as JSON",
    ),
) -> None:
    """📑 Synthesize a customized commercial consulting proposal for a prospect."""
    engine = get_consulting_engine()
    prop = engine.generate_proposal(
        prospect_name=prospect,
        service_tier=service,
        requirements=requirements,
        industry=industry,
        budget=budget,
        save_report=save,
        output_dir=output_dir,
    )

    if json_output:
        print(json.dumps(prop.to_dict(), indent=2))
        return

    console.print(prop.markdown_proposal)
    if prop.proposal_file:
        console.print(f"\n[bold green]Saved proposal to:[/bold green] [dim]{prop.proposal_file}[/dim]")


@consulting_app.command(name="outreach")
def consulting_outreach(
    prospect: str = typer.Argument(..., help="Prospect company name"),
    service: str = typer.Option(
        "custom_agent",
        "--service",
        "-s",
        help="Service tier (audit, custom_agent, full_stack, retainer)",
    ),
    role: str = typer.Option(
        "CTO",
        "--role",
        "-r",
        help="Recipient title / role (CTO, Founder, Head of Product)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output multi-channel outreach templates as JSON",
    ),
) -> None:
    """✉️ Generate multi-channel B2B cold/warm outreach templates (Email, LinkedIn, Zalo)."""
    engine = get_consulting_engine()
    out = engine.generate_outreach(prospect_name=prospect, service_tier=service, role=role)

    if json_output:
        print(json.dumps(out.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold]Subject:[/bold] {out.subject}\n\n{out.email_body}",
            title="📧 Email Template",
            border_style="cyan",
            box=ROUNDED,
        )
    )
    console.print(
        Panel(
            out.linkedin_body,
            title="💼 LinkedIn Direct Message",
            border_style="blue",
            box=ROUNDED,
        )
    )
    console.print(
        Panel(
            out.zalo_body,
            title="💬 Zalo OA / Message",
            border_style="green",
            box=ROUNDED,
        )
    )


@engagement_app.command(name="create")
def engagement_create(
    client: str = typer.Argument(..., help="Client company name"),
    service: str = typer.Option(
        "custom_agent",
        "--service",
        "-s",
        help="Service tier (audit, custom_agent, full_stack, retainer)",
    ),
    price: float = typer.Option(
        2000.0,
        "--price",
        "-p",
        help="Engagement price in USD",
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Project kickoff date (YYYY-MM-DD)",
    ),
    notes: str = typer.Option(
        "",
        "--notes",
        "-n",
        help="Notes / specific deliverables agreed upon",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output engagement record as JSON",
    ),
) -> None:
    """📝 Create and track a new client consulting engagement contract."""
    engine = get_consulting_engine()
    eng = engine.create_engagement(
        client_name=client,
        service_tier=service,
        price_usd=price,
        start_date=start_date,
        notes=notes,
    )

    if json_output:
        print(json.dumps(eng.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold green]Engagement {eng.id} Created[/bold green]\n"
            f"[dim]Client:[/dim]        {eng.client_name}\n"
            f"[dim]Offering:[/dim]      {eng.service_tier}\n"
            f"[dim]Contract Value:[/dim] ${eng.price_usd:,.2f} USD\n"
            f"[dim]Status:[/dim]        [bold yellow]{eng.status}[/bold yellow]\n"
            f"[dim]Kickoff Date:[/dim]  {eng.start_date}",
            title="Consulting Engagement Raised",
            border_style="green",
            box=ROUNDED,
        )
    )


@engagement_app.command(name="list")
def engagement_list(
    status: str = typer.Option(
        "ALL",
        "--status",
        "-s",
        help="Filter by status (PROPOSED, ACTIVE, DELIVERED, COMPLETED, ALL)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output engagements as JSON",
    ),
) -> None:
    """📋 List tracked client consulting contracts."""
    engine = get_consulting_engine()
    engagements = engine.list_engagements(status=status)

    if json_output:
        print(json.dumps([e.to_dict() for e in engagements], indent=2))
        return

    if not engagements:
        console.print("[dim]No consulting engagements matching the criteria.[/dim]")
        return

    table = Table(title=f"Client Engagements ({len(engagements)} total)", box=ROUNDED, border_style="cyan")
    table.add_column("ID", style="bold cyan")
    table.add_column("Client", style="bold")
    table.add_column("Tier", style="yellow")
    table.add_column("Contract Value", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Kickoff Date", style="dim")

    for e in engagements:
        stat_color = "green" if e.status in {"DELIVERED", "COMPLETED"} else "yellow"
        table.add_row(
            e.id,
            e.client_name,
            e.service_tier,
            f"${e.price_usd:,.2f}",
            f"[{stat_color}]{e.status}[/{stat_color}]",
            e.start_date,
        )

    console.print(table)


@engagement_app.command(name="update")
def engagement_update(
    engagement_id: str = typer.Argument(..., help="Engagement ID to update"),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="New status (PROPOSED, ACTIVE, DELIVERED, COMPLETED)",
    ),
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        "-n",
        help="Updated notes / progress comments",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output updated engagement as JSON",
    ),
) -> None:
    """🔄 Update status or notes for an existing engagement contract."""
    engine = get_consulting_engine()
    eng = engine.update_engagement(engagement_id=engagement_id, status=status, notes=notes)

    if not eng:
        console.print(f"[bold red]Error:[/bold red] Engagement '{engagement_id}' not found.")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(eng.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold green]Engagement {eng.id} Updated[/bold green]\n"
            f"[dim]Client:[/dim]  {eng.client_name}\n"
            f"[dim]Status:[/dim]  [bold yellow]{eng.status}[/bold yellow]\n"
            f"[dim]Notes:[/dim]   {eng.notes or '(none)'}",
            title="Contract Updated",
            border_style="green",
            box=ROUNDED,
        )
    )


def register_consulting_command(app: typer.Typer) -> None:
    """Register the 'consulting' command group onto the main Typer application."""
    app.add_typer(consulting_app, name="consulting")

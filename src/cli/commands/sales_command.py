# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/sales_command.py — CLI command surface for Sales & Revenue Dealflow Engine.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.sales_engine import DealStage, get_sales_engine

console = Console()
sales_app = typer.Typer(
    name="sales",
    help="💰 Sales & Revenue Command Suite: Pipeline tracking, outreach, deal prep, and close reports",
    no_args_is_help=False,
)


@sales_app.callback(invoke_without_command=True)
def sales_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON pipeline summary",
    ),
) -> None:
    """💰 Sales Executive Overview: Pipeline value, win rate, and deal stages."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_sales_engine()
    metrics = engine.get_pipeline_metrics()

    if json_output:
        print(json.dumps(metrics.to_dict(), indent=2))
        return

    header_text = (
        f"[bold cyan]💰 SALES & REVENUE EXECUTIVE PIPELINE[/bold cyan]\n"
        f"[dim]Total Opportunities:[/dim]  [bold]{metrics.total_deals}[/bold]  |  "
        f"[dim]Win Rate:[/dim]             [green]{metrics.win_rate:.1f}%[/green]\n"
        f"[dim]Total Pipeline Value:[/dim] [yellow]${metrics.total_pipeline_value:,.2f}[/yellow]  |  "
        f"[dim]Weighted Forecast:[/dim]    [bold green]${metrics.weighted_pipeline_value:,.2f}[/bold green]\n"
        f"[dim]Closed Won Revenue:[/dim]   [bold cyan]${metrics.won_value:,.2f}[/bold cyan]"
    )
    console.print(Panel(header_text, title="Revenue Engine", border_style="cyan", box=ROUNDED))

    # Deals by stage table
    stage_table = Table(title="Pipeline by Stage", box=ROUNDED)
    stage_table.add_column("Stage", style="cyan")
    stage_table.add_column("Count", justify="center", style="bold")

    for stage, count in metrics.deals_by_stage.items():
        stage_table.add_row(stage.upper(), str(count))

    console.print(stage_table)

    # Top deals table
    if metrics.top_deals:
        deals_table = Table(title="Top Pipeline Opportunities", box=ROUNDED)
        deals_table.add_column("ID", style="dim", width=12)
        deals_table.add_column("Opportunity", style="bold")
        deals_table.add_column("Company", style="cyan")
        deals_table.add_column("Value", justify="right", style="yellow")
        deals_table.add_column("Stage", justify="center")

        for d in metrics.top_deals:
            stage_style = "bold green" if d.stage == "won" else "cyan"
            deals_table.add_row(
                d.id,
                d.name,
                d.company,
                f"${d.value:,.2f}",
                f"[{stage_style}]{d.stage.upper()}[/{stage_style}]",
            )
        console.print(deals_table)


@sales_app.command(name="add")
def sales_add(
    name: str = typer.Argument(
        ...,
        help="Name of the deal opportunity (e.g. 'Enterprise License')",
    ),
    company: str = typer.Option(
        ...,
        "--company",
        "-c",
        help="Target company or account name",
    ),
    value: float = typer.Option(
        ...,
        "--value",
        "-v",
        help="Estimated deal value in USD",
    ),
    stage: str = typer.Option(
        "lead",
        "--stage",
        "-s",
        help="Pipeline stage: lead, qualified, proposal, negotiation, won, lost",
    ),
    email: str = typer.Option(
        "",
        "--email",
        "-e",
        help="Key contact email address",
    ),
    notes: str = typer.Option(
        "",
        "--notes",
        "-n",
        help="Optional notes or background information",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON deal receipt",
    ),
) -> None:
    """➕ Add a new deal opportunity to the sales pipeline."""
    engine = get_sales_engine()
    deal = engine.add_deal(
        name=name,
        company=company,
        value=value,
        stage=stage,
        contact_email=email,
        notes=notes,
    )

    if json_output:
        print(json.dumps(deal.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold green]✓ Deal Opportunity Added[/bold green]\n"
            f"[dim]ID:[/dim]             {deal.id}\n"
            f"[dim]Opportunity:[/dim]    [bold]{deal.name}[/bold]\n"
            f"[dim]Company:[/dim]        [cyan]{deal.company}[/cyan]\n"
            f"[dim]Value:[/dim]          [yellow]${deal.value:,.2f}[/yellow] (Weighted: ${deal.weighted_value:,.2f})\n"
            f"[dim]Stage:[/dim]          {deal.stage.upper()}\n"
            f"[dim]Contact:[/dim]        {deal.contact_email or 'None'}",
            title="Sales Pipeline Ledger",
            border_style="green",
            box=ROUNDED,
        )
    )


@sales_app.command(name="list")
def sales_list(
    stage: Optional[str] = typer.Option(
        None,
        "--stage",
        "-s",
        help="Filter deals by stage (e.g. lead, qualified, won)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON deals list",
    ),
) -> None:
    """📋 List deals in the sales pipeline."""
    engine = get_sales_engine()
    deals = engine.list_deals(stage=stage)

    if json_output:
        print(json.dumps([d.to_dict() for d in deals], indent=2))
        return

    table = Table(title=f"Sales Opportunities ({len(deals)} deals)", box=ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Name", style="bold")
    table.add_column("Company", style="cyan")
    table.add_column("Value", justify="right", style="yellow")
    table.add_column("Weighted", justify="right", style="dim")
    table.add_column("Stage", justify="center")

    for d in deals:
        table.add_row(
            d.id,
            d.name,
            d.company,
            f"${d.value:,.2f}",
            f"${d.weighted_value:,.2f}",
            d.stage.upper(),
        )
    console.print(table)


@sales_app.command(name="update")
def sales_update(
    deal_id: str = typer.Argument(
        ...,
        help="Deal ID to update",
    ),
    stage: Optional[str] = typer.Option(
        None,
        "--stage",
        "-s",
        help="New stage: lead, qualified, proposal, negotiation, won, lost",
    ),
    value: Optional[float] = typer.Option(
        None,
        "--value",
        "-v",
        help="Updated deal value in USD",
    ),
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        "-n",
        help="Updated notes",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON updated deal",
    ),
) -> None:
    """🔄 Update an existing deal's stage, value, or notes."""
    engine = get_sales_engine()
    deal = engine.update_deal(deal_id=deal_id, stage=stage, value=value, notes=notes)

    if not deal:
        if json_output:
            print(json.dumps({"ok": False, "error": f"Deal not found: {deal_id}"}))
        else:
            console.print(f"[bold red]Error:[/bold red] Deal not found: {deal_id}")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(deal.to_dict(), indent=2))
        return

    console.print(f"[bold green]✓ Deal {deal.id} updated:[/bold green] Stage={deal.stage.upper()} Value=${deal.value:,.2f}")


@sales_app.command(name="outreach")
def sales_outreach(
    company: str = typer.Argument(
        ...,
        help="Target company name for outreach generation",
    ),
    persona: str = typer.Option(
        "CTO",
        "--persona",
        "-p",
        help="Target persona (e.g. CTO, VP of Engineering, Founder)",
    ),
    channel: str = typer.Option(
        "email",
        "--channel",
        "-c",
        help="Outreach channel: 'email', 'linkedin', 'zalo'",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON outreach copy",
    ),
) -> None:
    """✉️ Synthesize tailored multi-channel outreach copy and cadences."""
    engine = get_sales_engine()
    template = engine.generate_outreach(company=company, persona=persona, channel=channel)

    if json_output:
        print(json.dumps(template.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold]Channel:[/bold] [cyan]{template.channel.upper()}[/cyan]  |  "
            f"[bold]Target:[/bold] {template.company} ({template.persona})\n\n"
            f"[bold]Subject / Opening:[/bold]\n{template.subject}\n\n"
            f"[bold]Message Body:[/bold]\n{template.body}\n\n"
            f"[bold]Follow-Up Cadence:[/bold]\n" + "\n".join(f"  • {c}" for c in template.follow_up_sequence),
            title="Tailored Outreach Playbook",
            border_style="cyan",
            box=ROUNDED,
        )
    )


@sales_app.command(name="prep")
def sales_prep(
    company: str = typer.Argument(
        ...,
        help="Prospect company name",
    ),
    value: float = typer.Option(
        15000.0,
        "--value",
        "-v",
        help="Target opportunity value",
    ),
    pain_points: str = typer.Option(
        "",
        "--pain",
        help="Comma-separated list of known customer pain points",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON deal prep report",
    ),
) -> None:
    """📝 Generate deal preparation notes, objection handling, and ROI model."""
    engine = get_sales_engine()
    prep = engine.generate_deal_prep(company=company, value=value, pain_points=pain_points)

    if json_output:
        print(json.dumps(prep.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold cyan]DEAL PREP — {prep.company}[/bold cyan] (Target Value: ${prep.deal_value:,.2f})\n\n"
            f"[bold]Solution Summary:[/bold]\n{prep.solution_summary}\n\n"
            f"[bold]Expected ROI Multiplier:[/bold] [bold green]{prep.roi_multiplier}x[/bold green]\n\n"
            f"[bold]Identified Pain Points:[/bold]\n" + "\n".join(f"  • {p}" for p in prep.pain_points),
            title="Account Executive Deal Preparation",
            border_style="cyan",
            box=ROUNDED,
        )
    )

    table = Table(title="Objection Handling Playbook", box=ROUNDED)
    table.add_column("Anticipated Objection", style="yellow", width=36)
    table.add_column("Strategic Response & Rebuttal")

    for obj in prep.objections_playbook:
        table.add_row(obj["objection"], obj["rebuttal"])
    console.print(table)


@sales_app.command(name="close")
def sales_close(
    deal_id: str = typer.Argument(
        ...,
        help="ID of deal to close as WON",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON close report",
    ),
) -> None:
    """🎉 Finalize deal closing, transition to WON, and create onboarding receipt."""
    engine = get_sales_engine()
    report = engine.generate_close_report(deal_id=deal_id)

    if not report:
        if json_output:
            print(json.dumps({"ok": False, "error": f"Deal not found: {deal_id}"}))
        else:
            console.print(f"[bold red]Error:[/bold red] Deal not found: {deal_id}")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold green]🎉 DEAL CLOSED WON — {report.company}[/bold green]\n\n"
            f"[dim]Deal ID:[/dim]        {report.deal_id}\n"
            f"[dim]Final Value:[/dim]    [bold yellow]${report.final_value:,.2f}[/bold yellow]\n"
            f"[dim]Closed Date:[/dim]    {report.closed_date}\n\n"
            f"[bold]Customer Success Onboarding Checklist:[/bold]\n"
            + "\n".join(f"  [green]✓[/green] {c}" for c in report.onboarding_checklist),
            title="Deal Close Receipt",
            border_style="green",
            box=ROUNDED,
        )
    )


def register_sales_command(app: typer.Typer) -> None:
    """Register the 'sales' command group onto the main Typer application."""
    app.add_typer(sales_app, name="sales")

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Campaign ledger & tracking subcommands for Marketing & Growth Suite."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.marketing_engine import get_marketing_engine

console = Console()

campaign_app = typer.Typer(
    name="campaign",
    help="🎯 Campaign ledger & tracking operations",
    no_args_is_help=False,
)


@campaign_app.command(name="create")
def campaign_create(
    name: str = typer.Argument(..., help="Campaign name (e.g. 'Q4 Developer Inbound')"),
    channel: str = typer.Option("social", "--channel", "-c", help="Marketing channel: social, search, content, email, local, zalo"),
    budget: float = typer.Option(1500.0, "--budget", "-b", help="Allocated budget in USD"),
    audience: str = typer.Option("Tech Founders & Engineers", "--audience", "-a", help="Target audience persona description"),
    status: str = typer.Option("active", "--status", "-s", help="Campaign status: draft, active, paused, completed"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON campaign record"),
) -> None:
    """➕ Create and register a promotional or growth campaign."""
    engine = get_marketing_engine()
    camp = engine.create_campaign(
        name=name, channel=channel, budget=budget, target_audience=audience, status=status,
    )
    if json_output:
        print(json.dumps(camp.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold green]✓ Campaign Created[/bold green]\n"
            f"[dim]ID:[/dim]        {camp.id}\n"
            f"[dim]Name:[/dim]      [bold]{camp.name}[/bold]\n"
            f"[dim]Channel:[/dim]   [cyan]{camp.channel.upper()}[/cyan]\n"
            f"[dim]Budget:[/dim]    [yellow]${camp.budget:,.2f}[/yellow]\n"
            f"[dim]Audience:[/dim]  {camp.target_audience}\n"
            f"[dim]Status:[/dim]    {camp.status.upper()}",
            title="Campaign Ledger",
            border_style="green",
            box=ROUNDED,
        )
    )


@campaign_app.command(name="list")
def campaign_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (draft, active, paused, completed)"),
    channel: Optional[str] = typer.Option(None, "--channel", "-c", help="Filter by channel (social, search, content, email, local, zalo)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON campaigns list"),
) -> None:
    """📋 List marketing campaigns in the ledger."""
    engine = get_marketing_engine()
    campaigns = engine.list_campaigns(status=status, channel=channel)
    if json_output:
        print(json.dumps([c.to_dict() for c in campaigns], indent=2))
        return

    table = Table(title=f"Marketing Campaigns ({len(campaigns)} campaigns)", box=ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Name", style="bold")
    table.add_column("Channel", style="cyan")
    table.add_column("Budget", justify="right", style="yellow")
    table.add_column("Conv", justify="right", style="green")
    table.add_column("CPA", justify="right", style="bold yellow")
    table.add_column("Status", justify="center")

    for c in campaigns:
        status_style = "bold green" if c.status == "active" else "dim"
        table.add_row(
            c.id, c.name, c.channel.upper(), f"${c.budget:,.2f}",
            str(c.conversions), f"${c.cpa:,.2f}", f"[{status_style}]{c.status.upper()}[/{status_style}]",
        )
    console.print(table)


@campaign_app.command(name="update")
def campaign_update(
    campaign_id: str = typer.Argument(..., help="Campaign ID to update"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status: draft, active, paused, completed"),
    budget: Optional[float] = typer.Option(None, "--budget", "-b", help="Updated budget in USD"),
    impressions: Optional[int] = typer.Option(None, "--impressions", "-i", help="Updated total impressions"),
    conversions: Optional[int] = typer.Option(None, "--conversions", "-c", help="Updated total conversions"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON updated campaign"),
) -> None:
    """🔄 Update campaign status, budget, impressions, or conversions."""
    engine = get_marketing_engine()
    camp = engine.update_campaign(
        campaign_id=campaign_id, status=status, budget=budget, impressions=impressions, conversions=conversions,
    )
    if not camp:
        if json_output:
            print(json.dumps({"ok": False, "error": f"Campaign not found: {campaign_id}"}))
        else:
            console.print(f"[bold red]Error:[/bold red] Campaign not found: {campaign_id}")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(camp.to_dict(), indent=2))
        return

    console.print(
        f"[bold green]✓ Campaign {camp.id} updated:[/bold green] "
        f"Status={camp.status.upper()} Budget=${camp.budget:,.2f} Conversions={camp.conversions}"
    )

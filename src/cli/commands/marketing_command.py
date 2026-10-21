# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/marketing_command.py — CLI command surface for Marketing & Growth Suite.
"""

from __future__ import annotations

import json

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.marketing_campaign_commands import (
    campaign_app,
    campaign_create,
    campaign_list,
    campaign_update,
)
from src.cli.commands.marketing_growth_commands import (
    marketing_bootstrap,
    marketing_content,
    marketing_growth,
    marketing_seo,
)
from src.core.marketing_engine import get_marketing_engine

console = Console()
marketing_app = typer.Typer(
    name="marketing",
    help="📢 Marketing & Growth Suite: Campaigns, ready-to-use content, SEO audit, growth lab, bootstrap strategy",
    no_args_is_help=False,
)

marketing_app.add_typer(campaign_app, name="campaign")
marketing_app.command(name="content")(marketing_content)
marketing_app.command(name="seo")(marketing_seo)
marketing_app.command(name="growth")(marketing_growth)
marketing_app.command(name="bootstrap")(marketing_bootstrap)


@marketing_app.callback(invoke_without_command=True)
def marketing_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON marketing summary",
    ),
) -> None:
    """📢 Marketing Executive Overview: Active campaigns, spend, impressions, conversions, and CPA."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_marketing_engine()
    metrics = engine.get_marketing_metrics()

    if json_output:
        print(json.dumps(metrics.to_dict(), indent=2))
        return

    header_text = (
        f"[bold magenta]📢 MARKETING & GROWTH EXECUTIVE DASHBOARD[/bold magenta]\n"
        f"[dim]Total Campaigns:[/dim]   [bold]{metrics.total_campaigns}[/bold] (Active: [green]{metrics.active_campaigns}[/green])  |  "
        f"[dim]Total Spend:[/dim]         [yellow]${metrics.total_budget:,.2f}[/yellow]\n"
        f"[dim]Impressions:[/dim]       [cyan]{metrics.total_impressions:,}[/cyan]  |  "
        f"[dim]Conversions:[/dim]       [bold green]{metrics.total_conversions:,}[/bold green]  |  "
        f"[dim]Blended CPA:[/dim]       [bold yellow]${metrics.blended_cpa:,.2f}[/bold yellow]"
    )
    console.print(Panel(header_text, title="Growth Operations", border_style="magenta", box=ROUNDED))

    chan_table = Table(title="Campaigns by Channel", box=ROUNDED)
    chan_table.add_column("Channel", style="cyan")
    chan_table.add_column("Count", justify="center", style="bold")

    for ch, count in metrics.campaigns_by_channel.items():
        chan_table.add_row(ch.upper(), str(count))
    console.print(chan_table)

    if metrics.top_campaigns:
        camp_table = Table(title="Top Performing Campaigns", box=ROUNDED)
        camp_table.add_column("ID", style="dim", width=12)
        camp_table.add_column("Campaign", style="bold")
        camp_table.add_column("Channel", style="cyan")
        camp_table.add_column("Budget", justify="right", style="yellow")
        camp_table.add_column("Impressions", justify="right")
        camp_table.add_column("Conversions", justify="right", style="green")
        camp_table.add_column("CPA", justify="right", style="bold yellow")
        camp_table.add_column("Status", justify="center")

        for c in metrics.top_campaigns:
            status_style = "bold green" if c.status == "active" else "dim"
            camp_table.add_row(
                c.id,
                c.name,
                c.channel.upper(),
                f"${c.budget:,.2f}",
                f"{c.impressions:,}",
                f"{c.conversions:,}",
                f"${c.cpa:,.2f}",
                f"[{status_style}]{c.status.upper()}[/{status_style}]",
            )
        console.print(camp_table)


def register_marketing_command(app: typer.Typer) -> None:
    """Register the 'marketing' command group onto the main Typer application."""
    app.add_typer(marketing_app, name="marketing")


__all__ = [
    "campaign_app",
    "campaign_create",
    "campaign_list",
    "campaign_update",
    "console",
    "get_marketing_engine",
    "marketing_app",
    "marketing_bootstrap",
    "marketing_content",
    "marketing_growth",
    "marketing_main",
    "marketing_seo",
    "register_marketing_command",
]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/marketing_command.py — CLI command surface for Marketing & Growth Suite.
"""

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
marketing_app = typer.Typer(
    name="marketing",
    help="📢 Marketing & Growth Suite: Campaigns, ready-to-use content, SEO audit, growth lab, bootstrap strategy",
    no_args_is_help=False,
)

campaign_app = typer.Typer(
    name="campaign",
    help="🎯 Campaign ledger & tracking operations",
    no_args_is_help=False,
)
marketing_app.add_typer(campaign_app, name="campaign")


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

    # Channels breakdown
    chan_table = Table(title="Campaigns by Channel", box=ROUNDED)
    chan_table.add_column("Channel", style="cyan")
    chan_table.add_column("Count", justify="center", style="bold")

    for ch, count in metrics.campaigns_by_channel.items():
        chan_table.add_row(ch.upper(), str(count))
    console.print(chan_table)

    # Top campaigns
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


@campaign_app.command(name="create")
def campaign_create(
    name: str = typer.Argument(
        ...,
        help="Campaign name (e.g. 'Q4 Developer Inbound')",
    ),
    channel: str = typer.Option(
        "social",
        "--channel",
        "-c",
        help="Marketing channel: social, search, content, email, local, zalo",
    ),
    budget: float = typer.Option(
        1500.0,
        "--budget",
        "-b",
        help="Allocated budget in USD",
    ),
    audience: str = typer.Option(
        "Tech Founders & Engineers",
        "--audience",
        "-a",
        help="Target audience persona description",
    ),
    status: str = typer.Option(
        "active",
        "--status",
        "-s",
        help="Campaign status: draft, active, paused, completed",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON campaign record",
    ),
) -> None:
    """➕ Create and register a promotional or growth campaign."""
    engine = get_marketing_engine()
    camp = engine.create_campaign(
        name=name,
        channel=channel,
        budget=budget,
        target_audience=audience,
        status=status,
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
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (draft, active, paused, completed)",
    ),
    channel: Optional[str] = typer.Option(
        None,
        "--channel",
        "-c",
        help="Filter by channel (social, search, content, email, local, zalo)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON campaigns list",
    ),
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
            c.id,
            c.name,
            c.channel.upper(),
            f"${c.budget:,.2f}",
            str(c.conversions),
            f"${c.cpa:,.2f}",
            f"[{status_style}]{c.status.upper()}[/{status_style}]",
        )
    console.print(table)


@campaign_app.command(name="update")
def campaign_update(
    campaign_id: str = typer.Argument(
        ...,
        help="Campaign ID to update",
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="New status: draft, active, paused, completed",
    ),
    budget: Optional[float] = typer.Option(
        None,
        "--budget",
        "-b",
        help="Updated budget in USD",
    ),
    impressions: Optional[int] = typer.Option(
        None,
        "--impressions",
        "-i",
        help="Updated total impressions",
    ),
    conversions: Optional[int] = typer.Option(
        None,
        "--conversions",
        "-c",
        help="Updated total conversions",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON updated campaign",
    ),
) -> None:
    """🔄 Update campaign status, budget, impressions, or conversions."""
    engine = get_marketing_engine()
    camp = engine.update_campaign(
        campaign_id=campaign_id,
        status=status,
        budget=budget,
        impressions=impressions,
        conversions=conversions,
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


@marketing_app.command(name="content")
def marketing_content(
    topic: str = typer.Argument(
        ...,
        help="Core topic or product feature to create copy for",
    ),
    channel: str = typer.Option(
        "social",
        "--channel",
        "-c",
        help="Destination platform: 'social', 'linkedin', 'zalo', 'blog'",
    ),
    content_type: str = typer.Option(
        "post",
        "--type",
        "-t",
        help="Content format (e.g. post, article, thread, script)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON content item",
    ),
) -> None:
    """✍️ Synthesize ready-to-use marketing copy and creative with hashtags and CTA."""
    engine = get_marketing_engine()
    item = engine.generate_content(topic=topic, channel=channel, content_type=content_type)

    if json_output:
        print(json.dumps(item.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold]Platform:[/bold] [cyan]{item.channel.upper()}[/cyan] ({item.content_type})\n"
            f"[bold]Headline:[/bold] [bold yellow]{item.headline}[/bold yellow]\n\n"
            f"[bold]Copy Body:[/bold]\n{item.body}\n\n"
            f"[bold]Hashtags:[/bold] {' '.join(item.hashtags)}\n"
            f"[bold]Call-To-Action:[/bold] [green]{item.call_to_action}[/green]",
            title="Generated Ready-to-Use Content",
            border_style="magenta",
            box=ROUNDED,
        )
    )


@marketing_app.command(name="seo")
def marketing_seo(
    keyword: str = typer.Argument(
        ...,
        help="Target focus keyword or search phrase",
    ),
    domain: str = typer.Option(
        "mekongcli.dev",
        "--domain",
        "-d",
        help="Target website domain",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON SEO audit report",
    ),
) -> None:
    """🔍 Analyze focus keywords, generate on-page recommendations, and uncover content gaps."""
    engine = get_marketing_engine()
    audit = engine.generate_seo_audit(keyword=keyword, domain=domain)

    if json_output:
        print(json.dumps(audit.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold magenta]SEO BLUEPRINT — {audit.keyword.upper()}[/bold magenta] ({audit.domain})\n\n"
            f"[bold]Recommended Title:[/bold]\n{audit.recommended_title}\n\n"
            f"[bold]Meta Description:[/bold]\n{audit.recommended_meta_description}\n\n"
            f"[bold]Target Density:[/bold] {audit.target_keyword_density}\n\n"
            f"[bold]Heading Structure Outline:[/bold]\n" + "\n".join(f"  • {h}" for h in audit.heading_structure),
            title="On-Page SEO & Content Architecture",
            border_style="magenta",
            box=ROUNDED,
        )
    )

    gap_table = Table(title="Content Gaps & Backlink Opportunities", box=ROUNDED)
    gap_table.add_column("Uncovered Content Gaps", style="yellow")
    gap_table.add_column("Recommended Backlink Channels", style="cyan")

    max_len = max(len(audit.content_gap_topics), len(audit.backlink_opportunities))
    for i in range(max_len):
        gap = audit.content_gap_topics[i] if i < len(audit.content_gap_topics) else ""
        link = audit.backlink_opportunities[i] if i < len(audit.backlink_opportunities) else ""
        gap_table.add_row(gap, link)
    console.print(gap_table)


@marketing_app.command(name="growth")
def marketing_growth(
    hypothesis: str = typer.Argument(
        ...,
        help="Growth hypothesis to test (e.g. 'Interactive demo increases signup rate')",
    ),
    metric: str = typer.Option(
        "Signup Conversion Rate",
        "--metric",
        "-m",
        help="Primary target success metric",
    ),
    lift: str = typer.Option(
        "+25%",
        "--lift",
        "-l",
        help="Target minimum detectable effect (MDE)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON growth experiment",
    ),
) -> None:
    """🧪 Design scientifically structured growth A/B experiments and sample sizes."""
    engine = get_marketing_engine()
    exp = engine.create_growth_experiment(hypothesis=hypothesis, target_metric=metric, target_lift=lift)

    if json_output:
        print(json.dumps(exp.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold green]GROWTH EXPERIMENT DESIGN — {exp.id}[/bold green]\n\n"
            f"[bold]Hypothesis:[/bold] {exp.hypothesis}\n"
            f"[bold]Primary Metric:[/bold] [cyan]{exp.target_metric}[/cyan] (Target Lift: [bold green]{exp.target_lift}[/bold green])\n"
            f"[bold]Sample Size / Variant:[/bold] {exp.sample_size_per_variant:,} visitors\n"
            f"[bold]Runtime Duration:[/bold] {exp.duration_days} days\n\n"
            f"[bold]Control (A):[/bold] {exp.variant_a}\n"
            f"[bold]Variant (B):[/bold] {exp.variant_b}\n\n"
            f"[bold]Decision Rule:[/bold] {exp.decision_rule}",
            title="A/B Testing Framework",
            border_style="green",
            box=ROUNDED,
        )
    )


@marketing_app.command(name="bootstrap")
def marketing_bootstrap(
    business_name: str = typer.Argument(
        ...,
        help="Business or product name",
    ),
    industry: str = typer.Option(
        "B2B SaaS",
        "--industry",
        "-i",
        help="Industry vertical or category",
    ),
    export: bool = typer.Option(
        True,
        "--export/--no-export",
        help="Export markdown blueprint to plans/marketing/",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON bootstrap plan",
    ),
) -> None:
    """🚀 Generate a full 30-day marketing bootstrap strategy and editorial calendar."""
    engine = get_marketing_engine()
    plan = engine.bootstrap_plan(business_name=business_name, industry=industry, export=export)

    if json_output:
        print(json.dumps(plan.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold magenta]30-DAY MARKETING STRATEGY — {plan.business_name}[/bold magenta] ({plan.industry})\n\n"
            f"[bold]Strategic Overview:[/bold]\n{plan.strategy_summary}\n\n"
            + (f"[dim]Exported to:[/dim] [cyan]{plan.exported_path}[/cyan]\n" if plan.exported_path else ""),
            title="Bootstrap Marketing OS",
            border_style="magenta",
            box=ROUNDED,
        )
    )

    table = Table(title="30-Day Editorial & Promotion Schedule", box=ROUNDED)
    table.add_column("Day", style="bold", width=10)
    table.add_column("Channel / Platform", style="cyan", width=18)
    table.add_column("Execution Action")

    for item in plan.content_calendar_30d:
        table.add_row(item["day"], item["platform"], item["action"])
    console.print(table)


def register_marketing_command(app: typer.Typer) -> None:
    """Register the 'marketing' command group onto the main Typer application."""
    app.add_typer(marketing_app, name="marketing")

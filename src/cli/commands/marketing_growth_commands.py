# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Content, SEO, growth experiments, and bootstrap subcommands for Marketing Suite."""

from __future__ import annotations

import json

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.marketing_engine import get_marketing_engine

console = Console()


def marketing_content(
    topic: str = typer.Argument(..., help="Core topic or product feature to create copy for"),
    channel: str = typer.Option("social", "--channel", "-c", help="Destination platform: 'social', 'linkedin', 'zalo', 'blog'"),
    content_type: str = typer.Option("post", "--type", "-t", help="Content format (e.g. post, article, thread, script)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON content item"),
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


def marketing_seo(
    keyword: str = typer.Argument(..., help="Target focus keyword or search phrase"),
    domain: str = typer.Option("mekongcli.dev", "--domain", "-d", help="Target website domain"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON SEO audit report"),
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


def marketing_growth(
    hypothesis: str = typer.Argument(..., help="Growth hypothesis to test (e.g. 'Interactive demo increases signup rate')"),
    metric: str = typer.Option("Signup Conversion Rate", "--metric", "-m", help="Primary target success metric"),
    lift: str = typer.Option("+25%", "--lift", "-l", help="Target minimum detectable effect (MDE)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON growth experiment"),
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


def marketing_bootstrap(
    business_name: str = typer.Argument(..., help="Business or product name"),
    industry: str = typer.Option("B2B SaaS", "--industry", "-i", help="Industry vertical or category"),
    export: bool = typer.Option(True, "--export/--no-export", help="Export markdown blueprint to plans/marketing/"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON bootstrap plan"),
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

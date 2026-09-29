# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/content_command.py — CLI command surface for Content Marketing & Editorial Publishing Suite.
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

from src.core.content_engine import get_content_engine

console = Console()
content_app = typer.Typer(
    name="content",
    help="✍️ Content Marketing & Editorial Publishing: Multi-format generation, calendar, and channel reach",
    no_args_is_help=False,
)


@content_app.callback(invoke_without_command=True)
def content_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON editorial overview",
    ),
) -> None:
    """✍️ Content Marketing Overview: Editorial calendar, published content, and distribution channels."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_content_engine()
    cal = engine.get_calendar()
    status = engine.get_status()

    if json_output:
        summary = {**status, "calendar": cal}
        print(json.dumps(summary, indent=2))
        return

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="left")
    grid.add_row(
        f"📝 [bold]Total Content Items:[/bold] [bold green]{status['total_content_items']}[/bold green]",
        f"🚀 [bold]Published Items:[/bold] [bold cyan]{status['published_items']}[/bold cyan]",
    )
    grid.add_row(
        f"⏳ [bold]Scheduled In Pipeline:[/bold] [bold yellow]{cal['scheduled_count']}[/bold yellow]",
        f"✍️ [bold]Working Drafts:[/bold] [bold magenta]{cal['drafts_count']}[/bold magenta]",
    )
    grid.add_row(
        f"📡 [bold]Active Channels:[/bold] [bold blue]{status['active_channels']}[/bold blue]",
        f"🏛️ [bold]Content Pillars:[/bold] [bold white]{status['registered_pillars']}[/bold white]",
    )

    console.print(
        Panel(
            grid,
            title="[bold green]✍️ Mekong Content Marketing & Editorial Hub[/bold green]",
            subtitle=f"[dim]DB: {status['db_path']} | Engine: {status['status']}[/dim]",
            border_style="green",
            box=ROUNDED,
        )
    )

    # Content Pillars Table
    p_table = Table(
        title="🏛️ Core Content Pillars & Publication Cadence",
        box=ROUNDED,
        show_header=True,
        header_style="bold yellow",
    )
    p_table.add_column("Pillar Key", style="bold")
    p_table.add_column("Name")
    p_table.add_column("Frequency", justify="center")
    p_table.add_column("Published", justify="center")
    p_table.add_column("Drafts", justify="center")
    p_table.add_column("Next Due Date", style="dim")

    for p_key, p_data in cal["pillars"].items():
        p_table.add_row(
            p_key,
            p_data["name"],
            p_data["frequency"],
            str(p_data["published_count"]),
            str(p_data["drafts_count"]),
            p_data["next_due_date"],
        )
    console.print(p_table)


@content_app.command("generate")
def content_generate(
    pillar: str = typer.Option(..., "--pillar", "-p", help="Content pillar: one-person-company, ai-agents, solo-founder, binh-phap, zenos"),
    format_type: str = typer.Option("blog", "--format", "-f", help="Output format: blog, twitter, linkedin, youtube_script, newsletter"),
    topic: str = typer.Option("", "--topic", "-t", help="Custom article or post topic (defaults to pillar highlight)"),
    channel: str = typer.Option("", "--channel", "-c", help="Target distribution channel (e.g. blog, twitter, indiehackers)"),
    save: bool = typer.Option(False, "--save", "-s", help="Save synthesized post to SQLite database"),
    save_file: bool = typer.Option(False, "--file", help="Export synthesized markdown file to content/ directory"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Directory to save generated markdown file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON post"),
) -> None:
    """⚡ Generate structured, ready-to-publish content for any pillar and format."""
    engine = get_content_engine()
    item = engine.generate_content(
        pillar=pillar,
        format_type=format_type,
        topic=topic,
        channel=channel,
    )

    if save or save_file:
        item = engine.save_content(item, output_dir=output_dir, save_file=save_file)

    if json_output:
        print(json.dumps(item, indent=2))
        return

    meta = item.get("metadata", {})
    tags_str = " ".join(meta.get("tags", []))

    summary_panel = Panel(
        f"[bold]Pillar:[/bold] {item['pillar']} | [bold]Format:[/bold] {item['format']} | "
        f"[bold]Channel:[/bold] {item['channel']}\n"
        f"[bold]Estimated Read Time:[/bold] {meta.get('estimated_read_time', 'N/A')} | "
        f"[bold]Words:[/bold] {meta.get('word_count', 0)}\n"
        f"[dim]{tags_str}[/dim]",
        title=f"📝 Generated Content: {item['title']}",
        border_style="cyan",
        box=ROUNDED,
    )
    console.print(summary_panel)

    console.print(Panel(item["body"], title="[bold white]Content Body[/bold white]", box=ROUNDED, border_style="dim"))

    if item.get("file_path"):
        console.print(f"[bold green]💾 Exported to markdown file:[/bold green] [cyan]{item['file_path']}[/cyan]")
    elif save:
        console.print(f"[bold green]💾 Saved to content ledger:[/bold green] [cyan]{item['id']}[/cyan]")


@content_app.command("calendar")
def content_calendar(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON calendar"),
) -> None:
    """📅 Show the editorial calendar schedule, publication frequencies, and due dates."""
    engine = get_content_engine()
    cal = engine.get_calendar()

    if json_output:
        print(json.dumps(cal, indent=2))
        return

    table = Table(
        title="📅 Mekong Editorial Publication Calendar",
        box=ROUNDED,
        header_style="bold green",
    )
    table.add_column("Pillar", style="bold")
    table.add_column("Frequency")
    table.add_column("Target Channels")
    table.add_column("Published", justify="center")
    table.add_column("Drafts", justify="center")
    table.add_column("Next Due Date", justify="center", style="bold yellow")

    for p_key, p_info in cal["pillars"].items():
        channels_str = ", ".join(p_info["target_channels"])
        table.add_row(
            p_info["name"],
            p_info["frequency"],
            channels_str,
            str(p_info["published_count"]),
            str(p_info["drafts_count"]),
            p_info["next_due_date"],
        )

    console.print(table)


@content_app.command("channels")
def content_channels(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON channel stats"),
) -> None:
    """📡 Display distribution channels, audience size, and publication metrics."""
    engine = get_content_engine()
    channels = engine.get_channel_stats()

    if json_output:
        print(json.dumps(channels, indent=2))
        return

    table = Table(
        title="📡 Mekong Content Distribution Channels",
        box=ROUNDED,
        header_style="bold cyan",
    )
    table.add_column("Channel ID", style="bold")
    table.add_column("Channel Name")
    table.add_column("Status", justify="center")
    table.add_column("Followers / Subs", justify="right")
    table.add_column("Posts Published", justify="right")
    table.add_column("Avg Engagement", justify="right", style="green")

    for ch in channels:
        table.add_row(
            ch["channel_id"],
            ch["name"],
            f"[green]{ch['status']}[/green]",
            f"{ch['followers']:,}",
            str(ch["posts_published"]),
            f"{ch['engagement_rate']}%",
        )

    console.print(table)


@content_app.command("list")
def content_list(
    status: str = typer.Option("all", "--status", "-s", help="Filter by status: draft, scheduled, published, all"),
    pillar: str = typer.Option("", "--pillar", "-p", help="Filter by content pillar"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON items list"),
) -> None:
    """📋 List tracked content items with format, channel, and publication state."""
    engine = get_content_engine()
    items = engine.list_content(status=status, pillar=pillar)

    if json_output:
        print(json.dumps(items, indent=2))
        return

    if not items:
        console.print(f"[yellow]No content items found matching status '{status}'.[/yellow]")
        return

    table = Table(
        title=f"📋 Content Ledger ({status.capitalize()})",
        box=ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("ID", style="bold cyan")
    table.add_column("Title")
    table.add_column("Pillar")
    table.add_column("Format")
    table.add_column("Channel")
    table.add_column("Status", justify="center")
    table.add_column("Created", style="dim")

    for i in items:
        stat_color = "green" if i["status"] == "published" else "yellow" if i["status"] == "scheduled" else "dim"
        table.add_row(
            i["id"],
            i["title"][:35],
            i["pillar"],
            i["format"],
            i["channel"],
            f"[{stat_color}]{i['status']}[/{stat_color}]",
            i["created_at"][:10],
        )

    console.print(table)


@content_app.command("publish")
def content_publish(
    content_id: str = typer.Argument(..., help="Content item ID to mark as published"),
    channel: str = typer.Option("", "--channel", "-c", help="Distribution channel to publish to"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON confirmation"),
) -> None:
    """🚀 Mark a drafted or scheduled content item as published."""
    engine = get_content_engine()
    res = engine.update_status(content_id=content_id, new_status="published", channel=channel)

    if json_output:
        print(json.dumps(res, indent=2))
        return

    if res.get("success"):
        console.print(
            f"[bold green]🚀 Content Successfully Published:[/bold green] [cyan]{res['id']}[/cyan] "
            f"via [bold]{res['channel']}[/bold] at [dim]{res['published_at']}[/dim]"
        )
    else:
        console.print(f"[bold red]Error:[/bold red] {res.get('error')}")


@content_app.command("pillars")
def content_pillars(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON pillars"),
) -> None:
    """🏛️ Display official content pillars, frequencies, and target distribution channels."""
    engine = get_content_engine()
    pillars = engine.get_pillars()

    if json_output:
        print(json.dumps(pillars, indent=2))
        return

    table = Table(
        title="🏛️ Mekong Official Content Pillars",
        box=ROUNDED,
        header_style="bold yellow",
    )
    table.add_column("Pillar Key", style="bold")
    table.add_column("Name")
    table.add_column("Frequency")
    table.add_column("Channels")
    table.add_column("Description", style="dim")

    for key, p in pillars.items():
        table.add_row(
            key,
            p["name"],
            p["frequency"],
            ", ".join(p["target_channels"]),
            p["description"],
        )

    console.print(table)


def register_content_command(app: typer.Typer) -> None:
    """Register the 'content' command group onto the main Typer application."""
    app.add_typer(content_app, name="content")

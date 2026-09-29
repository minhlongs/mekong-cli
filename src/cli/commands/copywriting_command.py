# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/copywriting_command.py — CLI command surface for Conversion Copywriting & Persuasion Engine.
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

from src.core.copywriting_engine import get_copywriting_engine

console = Console()
copywriting_app = typer.Typer(
    name="copywriting",
    help="✍️ Conversion Copywriting & Persuasion Engine: High-converting formulas, headlines, and landing page copy",
    no_args_is_help=False,
)


@copywriting_app.callback(invoke_without_command=True)
def copywriting_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON copywriting overview",
    ),
) -> None:
    """✍️ Copywriting Overview: Conversion formulas, writing style guides, and saved projects."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_copywriting_engine()
    status = engine.get_status()
    formulas = engine.get_formulas()
    styles = engine.get_styles()

    if json_output:
        summary = {**status, "formulas": formulas, "styles": styles}
        print(json.dumps(summary, indent=2))
        return

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="left")
    grid.add_row(
        f"📚 [bold]Conversion Formulas:[/bold] [bold green]{status['registered_formulas']}[/bold green]",
        f"🎨 [bold]Tone Style Guides:[/bold] [bold cyan]{status['registered_styles']}[/bold cyan]",
    )
    grid.add_row(
        f"💾 [bold]Saved Copy Projects:[/bold] [bold yellow]{status['saved_projects_count']}[/bold yellow]",
        f"⚡ [bold]Engine Status:[/bold] [bold green]{status['status']}[/bold green]",
    )

    console.print(
        Panel(
            grid,
            title="[bold green]✍️ Mekong Conversion Copywriting Engine[/bold green]",
            subtitle=f"[dim]DB: {status['db_path']}[/dim]",
            border_style="green",
            box=ROUNDED,
        )
    )

    # Formulas table
    f_table = Table(
        title="🧠 Conversion Copywriting Frameworks",
        box=ROUNDED,
        show_header=True,
        header_style="bold yellow",
    )
    f_table.add_column("Formula", style="bold")
    f_table.add_column("Name")
    f_table.add_column("Best For")
    f_table.add_column("Core Steps", style="dim")

    for f_key, f_data in formulas.items():
        f_table.add_row(
            f_key.upper(),
            f_data["name"],
            f_data["best_for"],
            " ➔ ".join(f_data["steps"]),
        )
    console.print(f_table)


@copywriting_app.command("generate")
def copywriting_generate(
    product_name: str = typer.Argument(..., help="Product or service name"),
    audience: str = typer.Option("Founders & Engineers", "--audience", "-a", help="Target customer segment"),
    formula: str = typer.Option("pas", "--formula", "-f", help="Framework: pas, aida, bab, fab, 4us"),
    copy_type: str = typer.Option("landing_page", "--type", "-t", help="Copy format: landing_page, email, headline, cta"),
    benefit: str = typer.Option("", "--benefit", "-b", help="Primary value proposition or customer outcome"),
    style: str = typer.Option("direct_response", "--style", "-s", help="Tone style: direct_response, technical_founder, punchy_minimalist, storytelling"),
    save: bool = typer.Option(False, "--save", help="Save synthesized copy project to SQLite database"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON copy"),
) -> None:
    """⚡ Synthesize high-converting copy using proven direct-response frameworks."""
    engine = get_copywriting_engine()
    item = engine.generate_copy(
        product_name=product_name,
        target_audience=audience,
        formula=formula,
        copy_type=copy_type,
        key_benefit=benefit,
        style=style,
    )

    if save:
        item = engine.save_project(item)

    if json_output:
        print(json.dumps(item, indent=2))
        return

    meta = item.get("metadata", {})
    summary_panel = Panel(
        f"[bold]Product:[/bold] {item['product_name']} | [bold]Audience:[/bold] {item['target_audience']}\n"
        f"[bold]Formula:[/bold] {meta.get('formula_name', item['formula'])} | [bold]Style:[/bold] {meta.get('style_name', 'Direct Response')}\n"
        f"[bold]Sections:[/bold] {', '.join(meta.get('sections', []))} | [bold]Words:[/bold] {meta.get('word_count', 0)}",
        title=f"📝 Generated Copy: {item['title']}",
        border_style="cyan",
        box=ROUNDED,
    )
    console.print(summary_panel)

    console.print(Panel(item["copy_text"], title="[bold white]Copy Output[/bold white]", box=ROUNDED, border_style="dim"))

    if save:
        console.print(f"[bold green]💾 Saved to copywriting ledger:[/bold green] [cyan]{item['id']}[/cyan]")


@copywriting_app.command("headline")
def copywriting_headline(
    product_name: str = typer.Argument(..., help="Product or tool name"),
    value_prop: str = typer.Option("automate development workflows", "--value", "-v", help="Core benefit or capability"),
    count: int = typer.Option(5, "--count", "-c", help="Number of variations to generate"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON headlines"),
) -> None:
    """🎯 Generate high-impact headline variations categorized by psychological angle."""
    engine = get_copywriting_engine()
    headlines = engine.generate_headlines(
        product_name=product_name,
        value_prop=value_prop,
        count=count,
    )

    if json_output:
        print(json.dumps(headlines, indent=2))
        return

    table = Table(
        title=f"🎯 Headline Variations for '{product_name}'",
        box=ROUNDED,
        header_style="bold green",
    )
    table.add_column("#", justify="center")
    table.add_column("Psychological Angle", style="bold yellow")
    table.add_column("Headline Text")

    for h in headlines:
        table.add_row(
            str(h["index"]),
            h["angle"],
            h["headline"],
        )
    console.print(table)


@copywriting_app.command("cta")
def copywriting_cta(
    action_goal: str = typer.Argument("start free trial", help="Desired customer conversion action"),
    risk_reversal: str = typer.Option("", "--reversal", "-r", help="Risk reversal microcopy (e.g. No credit card required)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON CTAs"),
) -> None:
    """🔘 Generate optimized call-to-action button copy with risk-reversal microcopy."""
    engine = get_copywriting_engine()
    ctas = engine.generate_cta(action_goal=action_goal, risk_reversal=risk_reversal)

    if json_output:
        print(json.dumps(ctas, indent=2))
        return

    table = Table(
        title="🔘 High-Converting Call-To-Action (CTA) Variations",
        box=ROUNDED,
        header_style="bold cyan",
    )
    table.add_column("Variant Type", style="bold")
    table.add_column("Button Copy", style="bold green")
    table.add_column("Risk-Reversal Microcopy", style="dim")

    for c in ctas:
        table.add_row(
            c["type"],
            c["button_text"],
            c["microcopy"],
        )
    console.print(table)


@copywriting_app.command("formulas")
def copywriting_formulas(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON formulas catalog"),
) -> None:
    """🧠 Display registered conversion copywriting frameworks and steps."""
    engine = get_copywriting_engine()
    formulas = engine.get_formulas()

    if json_output:
        print(json.dumps(formulas, indent=2))
        return

    table = Table(
        title="🧠 Direct-Response Copywriting Frameworks",
        box=ROUNDED,
        header_style="bold yellow",
    )
    table.add_column("Key", style="bold")
    table.add_column("Formula Name")
    table.add_column("Best Use Case")
    table.add_column("Framework Description", style="dim")

    for key, f in formulas.items():
        table.add_row(
            key.upper(),
            f["name"],
            f["best_for"],
            f["description"],
        )
    console.print(table)


@copywriting_app.command("styles")
def copywriting_styles(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON styles catalog"),
) -> None:
    """🎨 Display tone guidelines, audience rules, and voice principles."""
    engine = get_copywriting_engine()
    styles = engine.get_styles()

    if json_output:
        print(json.dumps(styles, indent=2))
        return

    table = Table(
        title="🎨 Brand Voice & Writing Style Guides",
        box=ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Style Key", style="bold")
    table.add_column("Style Name")
    table.add_column("Tone Description")
    table.add_column("Core Writing Rules", style="dim")

    for key, s in styles.items():
        table.add_row(
            key,
            s["name"],
            s["tone"],
            " • ".join(s["rules"]),
        )
    console.print(table)


@copywriting_app.command("list")
def copywriting_list(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum projects to display"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON projects list"),
) -> None:
    """📋 List saved copywriting projects and generated assets."""
    engine = get_copywriting_engine()
    projects = engine.list_projects(limit=limit)

    if json_output:
        print(json.dumps(projects, indent=2))
        return

    if not projects:
        console.print("[yellow]No copywriting projects saved yet. Generate one with `mekong copywriting generate --save`.[/yellow]")
        return

    table = Table(
        title="📋 Saved Copywriting Projects",
        box=ROUNDED,
        header_style="bold blue",
    )
    table.add_column("ID", style="bold cyan")
    table.add_column("Title")
    table.add_column("Product")
    table.add_column("Formula")
    table.add_column("Type")
    table.add_column("Created", style="dim")

    for p in projects:
        table.add_row(
            p["id"],
            p["title"][:35],
            p["product_name"],
            p["formula"].upper(),
            p["type"],
            p["created_at"][:10],
        )
    console.print(table)


def register_copywriting_command(app: typer.Typer) -> None:
    """Register the 'copywriting' command group onto the main Typer application."""
    app.add_typer(copywriting_app, name="copywriting")

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for the Founder Genome Assessment (``mekong founder``).

Commands
--------
overview    Display engine health, psychometric distributions, and recent profiles.
assess      Run a founder genome assessment and store in the database.
review      Load and display a founder genome.
list        List all assessed founders with optional risk level filtering.
analyze     Synthesize psychometric strengths, blindspots, and team recommendations.
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

from src.core.founder_engine import get_founder_engine

logger = logging.getLogger(__name__)
console = Console()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

founder_app = typer.Typer(
    name="founder",
    help="🧬 Founder Genome Assessment — personality, values, fears, risk, biases",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)


# ---------------------------------------------------------------------------
# Overview Callback
# ---------------------------------------------------------------------------


@founder_app.callback(invoke_without_command=True)
def founder_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON founder genome overview",
    ),
) -> None:
    """🧬 Founder Genome Overview: Psychometric distributions, active archetypes, and recent assessments."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_founder_engine()
    status = engine.get_status()
    recent = engine.list_founders(limit=10)

    if json_output:
        overview = {
            **status,
            "recent_founders": recent,
        }
        print(json.dumps(overview, indent=2))
        return

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="left")
    grid.add_row(
        f"🧬 [bold]Total Assessed:[/bold] [bold cyan]{status['total_founders']}[/bold cyan]",
        f"📊 [bold]Assessments Logged:[/bold] [bold green]{status['total_assessments_logged']}[/bold green]",
    )
    dist = status["risk_distribution"]
    grid.add_row(
        f"🛡️ [bold]Conservative:[/bold] [bold blue]{dist['conservative']}[/bold blue] | "
        f"⚖️ [bold]Moderate:[/bold] [bold yellow]{dist['moderate']}[/bold yellow] | "
        f"🚀 [bold]Aggressive:[/bold] [bold red]{dist['aggressive']}[/bold red]",
        f"⚡ [bold]Status:[/bold] [bold green]{status['status']}[/bold green]",
    )

    console.print(
        Panel(
            grid,
            title="[bold green]🧬 Mekong Founder Genome & Psychometric Engine[/bold green]",
            subtitle=f"[dim]DB: {status['db_path']}[/dim]",
            border_style="green",
            box=ROUNDED,
        )
    )

    table = Table(
        title="🌟 Recent Assessed Founders",
        box=ROUNDED,
        header_style="bold yellow",
    )
    table.add_column("Name", style="bold cyan")
    table.add_column("Archetype", style="magenta")
    table.add_column("Risk Level", justify="center")
    table.add_column("Biases", justify="right")
    table.add_column("Assessed At", style="dim")
    table.add_column("Mission", style="dim")

    for f in recent:
        risk_color = (
            "blue" if f["risk_level"] == "conservative"
            else "yellow" if f["risk_level"] == "moderate"
            else "red"
        )
        table.add_row(
            f["name"],
            f["archetype"],
            f"[{risk_color}]{f['risk_level'].upper()}[/{risk_color}]",
            str(f["biases_count"]),
            f["assessed_at"][:10],
            f["mission"][:40] + ("..." if len(f["mission"]) > 40 else ""),
        )
    console.print(table)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@founder_app.command(name="assess")
def assess_cmd(
    name: str = typer.Option(
        "",
        "--name",
        "-n",
        help="Founder identifier or name (auto-generated if omitted)",
    ),
    mission: str = typer.Option(
        "",
        "--mission",
        "-m",
        help="Founder mission or purpose statement",
    ),
    tipi_json: str = typer.Option(
        "{}",
        "--tipi",
        help='JSON string of TIPI-10 responses (e.g. \'{"tipi_01": 6}\')',
    ),
    values_json: str = typer.Option(
        "[]",
        "--values",
        help="JSON array of selected Schwartz value IDs",
    ),
    fears_json: str = typer.Option(
        "[]",
        "--fears",
        help="JSON array of fear entries",
    ),
    risk_json: str = typer.Option(
        "{}",
        "--risk",
        help="JSON dict of risk dimension ratings (1-10)",
    ),
    biases_json: str = typer.Option(
        "{}",
        "--biases",
        help="JSON dict of bias yes/no responses",
    ),
    particle_id: str = typer.Option(
        "",
        "--particle-id",
        "-p",
        help="Optional ZenOS particle ID for identity linkage",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON",
    ),
) -> None:
    """Assess a founder genome and store it in the database."""
    try:
        tipi = json.loads(tipi_json) if tipi_json else {}
        values = json.loads(values_json) if values_json else []
        fears = json.loads(fears_json) if fears_json else []
        risk = json.loads(risk_json) if risk_json else {}
        biases = json.loads(biases_json) if biases_json else {}
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]✗ Error: Invalid JSON input --[/bold red] {exc}")
        raise typer.Exit(code=1)

    founder_name = name.strip() or (f"founder-{mission[:16].replace(' ', '-').lower()}" if mission else "founder-anonymous")

    engine = get_founder_engine()
    genome = engine.assess_founder(
        name=founder_name,
        mission=mission,
        tipi_responses=tipi,
        values=values,
        fears=fears,
        risk_ratings=risk,
        bias_responses=biases,
        particle_id=particle_id or None,
    )

    if json_output:
        print(json.dumps(genome, indent=2))
        return

    b5 = genome["big_five"]
    b5_str = (
        f"O: {b5['openness']} | C: {b5['conscientiousness']} | "
        f"E: {b5['extraversion']} | A: {b5['agreeableness']} | "
        f"ES: {b5['emotional_stability']} (N: {b5['neuroticism']})"
    )
    risk_color = (
        "blue" if genome["risk_level"] == "conservative"
        else "yellow" if genome["risk_level"] == "moderate"
        else "red"
    )

    panel = Panel(
        f"[bold]Founder:[/bold] [cyan]{genome['name']}[/cyan] ({genome['id']})\n"
        f"[bold]Archetype:[/bold] [magenta]{genome['archetype']}[/magenta]\n"
        f"[bold]Risk Level:[/bold] [{risk_color}]{genome['risk_level'].upper()}[/{risk_color}]\n"
        f"[bold]Mission:[/bold] {genome['mission']}\n\n"
        f"[bold]Big Five Traits (1-100):[/bold]\n{b5_str}\n\n"
        f"[bold]Identified Biases:[/bold] {', '.join(genome['cognitive_biases']) or 'None detected'}\n"
        f"[bold]Core Values:[/bold] {', '.join(genome['values'])}",
        title="✅ Founder Genome Assessed Successfully",
        border_style="green",
        box=ROUNDED,
    )
    console.print(panel)


@founder_app.command(name="review")
def review_cmd(
    founder_id: str = typer.Argument(
        ...,
        help="Founder name or entity ID in database",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON",
    ),
) -> None:
    """Load and display a founder genome profile."""
    engine = get_founder_engine()
    entity = engine.get_founder(founder_id)
    if entity is None:
        console.print(f"[bold red]✗ Founder not found:[/bold red] {founder_id}")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(entity, indent=2, default=str))
        return

    b5 = entity["big_five"]
    risk = entity["risk_profile"]

    panel = Panel(
        f"[bold]Founder:[/bold] [cyan]{entity['name']}[/cyan] ({entity['id']})\n"
        f"[bold]Archetype:[/bold] [magenta]{entity['archetype']}[/magenta] | "
        f"[bold]Risk Level:[/bold] [yellow]{entity['risk_level'].upper()}[/yellow]\n"
        f"[bold]Mission:[/bold] {entity['mission']}\n\n"
        f"[bold]Big Five (1-100):[/bold] O:{b5['openness']} C:{b5['conscientiousness']} "
        f"E:{b5['extraversion']} A:{b5['agreeableness']} ES:{b5['emotional_stability']}\n"
        f"[bold]Risk 5D (10-100):[/bold] Fin:{risk['financial']} Ops:{risk['operational']} "
        f"Rep:{risk['reputational']} Comp:{risk['compliance']} Tech:{risk['technical']}\n\n"
        f"[bold]Biases:[/bold] {', '.join(entity['cognitive_biases']) or 'None'}\n"
        f"[bold]Assessed At:[/bold] {entity['assessed_at']}",
        title="🧬 Founder Genome Review",
        border_style="cyan",
        box=ROUNDED,
    )
    console.print(panel)


@founder_app.command(name="list")
def list_cmd(
    risk_level: str = typer.Option(
        "all",
        "--risk",
        "-r",
        help="Filter by risk level: conservative | moderate | aggressive | all",
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        "-l",
        help="Max results to display",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON",
    ),
) -> None:
    """List all assessed founders with optional risk filtering."""
    engine = get_founder_engine()
    founders = engine.list_founders(risk_level=risk_level, limit=limit)

    if json_output:
        print(json.dumps(founders, indent=2))
        return

    if not founders:
        console.print("[yellow]No founders found matching criteria.[/yellow]")
        return

    table = Table(
        title="🧬 Assessed Founders Registry",
        box=ROUNDED,
        header_style="bold yellow",
    )
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold cyan")
    table.add_column("Archetype", style="magenta")
    table.add_column("Risk Level", justify="center")
    table.add_column("Biases Count", justify="right")
    table.add_column("Assessed At", style="dim")

    for f in founders:
        risk_color = (
            "blue" if f["risk_level"] == "conservative"
            else "yellow" if f["risk_level"] == "moderate"
            else "red"
        )
        table.add_row(
            f["id"],
            f["name"],
            f["archetype"],
            f"[{risk_color}]{f['risk_level'].upper()}[/{risk_color}]",
            str(f["biases_count"]),
            f["assessed_at"][:10],
        )
    console.print(table)


@founder_app.command(name="analyze")
def analyze_cmd(
    name_or_id: str = typer.Argument(
        ...,
        help="Founder name or entity ID to analyze",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON",
    ),
) -> None:
    """Synthesize psychometric strengths, blindspots, and team recommendations."""
    engine = get_founder_engine()
    res = engine.analyze_founder(name_or_id)

    if json_output:
        print(json.dumps(res, indent=2))
        return

    if not res.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {res.get('error')}")
        raise typer.Exit(code=1)

    strengths = "\n".join(f"  • {s}" for s in res["strengths"]) or "  • Standard balanced capabilities"
    blindspots = "\n".join(f"  • {b}" for b in res["blindspots"]) or "  • No major cognitive vulnerabilities identified"
    recs = "\n".join(f"  • {r}" for r in res["strategic_recommendations"]) or "  • Maintain ongoing autonomous execution"

    panel = Panel(
        f"[bold]Founder:[/bold] [cyan]{res['name']}[/cyan] ({res['id']})\n"
        f"[bold]Archetype:[/bold] [magenta]{res['archetype']}[/magenta] | "
        f"[bold]Risk Level:[/bold] [yellow]{res['risk_level'].upper()}[/yellow]\n\n"
        f"[bold green]Strategic Strengths:[/bold green]\n{strengths}\n\n"
        f"[bold red]Potential Blindspots:[/bold red]\n{blindspots}\n\n"
        f"[bold cyan]Actionable Recommendations:[/bold cyan]\n{recs}",
        title="🧠 Founder Psychometric & Strategic Analysis",
        border_style="magenta",
        box=ROUNDED,
    )
    console.print(panel)


def register(cli: typer.Typer) -> None:
    """Registration hook for main CLI app."""
    cli.add_typer(founder_app, name="founder", help="🧬 Founder Genome Assessment")

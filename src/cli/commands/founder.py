# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for the Founder Genome Assessment (``mekong founder``).

Commands
--------
assess      Run a founder genome assessment and store in the behaviour graph.
review      Load and display a founder genome from the behaviour graph.
list        List all assessed founders in the behaviour graph.

Import path used by ``src/cli/app_setup.py``::

    from src.cli.commands.founder import founder_app
"""

from __future__ import annotations

import json
import os

import typer

from src.mekong.founder.assess import (
    assess_founder,
    list_founders,
    review_founder,
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

founder_app = typer.Typer(
    name="founder",
    help="Founder Genome Assessment — personality, values, fears, risk, biases",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------


def _default_db() -> str:
    return os.environ.get(
        "MEKONG_GRAPH_DB",
        os.path.join(os.getcwd(), ".mekong", "graph.db"),
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@founder_app.command(name="assess")
def assess_cmd(
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
    db: str = typer.Option(
        _default_db,
        "--db",
        help="Path to graph database",
    ),
) -> None:
    """Assess a founder genome and store it in the behaviour graph.

    Provide assessment data via JSON options.  Returns the genome JSON
    on success.
    """
    try:
        tipi = json.loads(tipi_json)
        values = json.loads(values_json)
        fears = json.loads(fears_json)
        risk = json.loads(risk_json)
        biases = json.loads(biases_json)
    except json.JSONDecodeError as exc:
        typer.echo(f"Error: invalid JSON input -- {exc}", err=True)
        raise typer.Exit(code=1)

    genome = assess_founder(
        mission=mission,
        tipi_responses=tipi,
        values=values,
        fears=fears,
        risk_ratings=risk,
        bias_responses=biases,
        particle_id=particle_id or None,
        db_path=db,
    )

    typer.echo(genome_to_output(genome))


@founder_app.command(name="review")
def review_cmd(
    founder_id: str = typer.Argument(
        ...,
        help="Founder entity ID in the behaviour graph",
    ),
    db: str = typer.Option(
        _default_db,
        "--db",
        help="Path to graph database",
    ),
) -> None:
    """Load and display a founder genome from the behaviour graph."""
    entity = review_founder(founder_id, db_path=db)
    if entity is None:
        typer.echo(f"Founder not found: {founder_id}", err=True)
        raise typer.Exit(code=1)

    typer.echo(json.dumps(entity, indent=2, default=str))


@founder_app.command(name="list")
def list_cmd(
    db: str = typer.Option(
        _default_db,
        "--db",
        help="Path to graph database",
    ),
) -> None:
    """List all assessed founders in the behaviour graph."""
    founders = list_founders(db_path=db)
    if not founders:
        typer.echo("No founders found in behaviour graph.")
        return

    typer.echo(f"Found {len(founders)} founder(s):")
    for f in founders:
        meta = f.get("metadata", {})
        typer.echo(
            f"  {f['id']}  |  {f['name']}  |  "
            f"risk={meta.get('risk_level', '?')}  |  "
            f"biases={len(meta.get('cognitive_biases', []))}  |  "
            f"{f['created_at']}"
        )


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def genome_to_output(genome: object) -> str:
    """Serialise a genome object to indented JSON for CLI display."""
    from src.mekong.founder.assess import genome_to_dict as _to_dict

    return json.dumps(_to_dict(genome), indent=2, default=str)

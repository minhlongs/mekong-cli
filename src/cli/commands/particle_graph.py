# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for the ZenOS behavior graph (``mekong particle graph``).

Commands
--------
record      Record a behavior between two entities.
trust       Compute or retrieve the trust score between two entities.
detect      Run collusion detection.
status      Show graph metadata summary.
"""

from __future__ import annotations

import os

import typer

from src.mekong.graph.api import (
    detect_collusion,
    get_status,
    get_trust,
    record_behavior,
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

graph_app = typer.Typer(
    name="graph",
    help="Behavior graph — trust & collusion detection",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------


def _default_db() -> str:
    return os.environ.get("MEKONG_GRAPH_DB", os.path.join(os.getcwd(), ".mekong", "graph.db"))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@graph_app.command(name="record")
def record_cmd(
    source_id: str = typer.Argument(..., help="Source entity ID"),
    source_name: str = typer.Option("", "--source-name", help="Source entity name (defaults to source_id)"),
    target_id: str = typer.Argument(..., help="Target entity ID"),
    target_name: str = typer.Option("", "--target-name", help="Target entity name (defaults to target_id)"),
    action: str = typer.Argument(..., help="Action verb (e.g. trade, refer, bid_win)"),
    value: float = typer.Option(0.0, "--value", "-v", help="Numeric value for the behavior"),
    payload: str = typer.Option("{}", "--payload", "-p", help="JSON payload string"),
    db: str = typer.Option(_default_db, "--db", help="Path to graph database"),
) -> None:
    """Record a behavior edge between two entities."""
    import json

    try:
        payload_dict = json.loads(payload) if payload else {}
    except json.JSONDecodeError:
        typer.echo(f"Error: payload is not valid JSON: {payload}", err=True)
        raise typer.Exit(code=1)

    result = record_behavior(
        source_id=source_id,
        source_name=source_name or source_id,
        target_id=target_id,
        target_name=target_name or target_id,
        action=action,
        payload=payload_dict,
        value=value,
        db_path=db,
    )
    typer.echo(f"Behavior recorded: id={result['behavior_id']}")


@graph_app.command(name="trust")
def trust_cmd(
    source_id: str = typer.Argument(..., help="Source entity ID"),
    target_id: str = typer.Argument(..., help="Target entity ID"),
    db: str = typer.Option(_default_db, "--db", help="Path to graph database"),
) -> None:
    """Compute or retrieve the trust score between two entities."""
    result = get_trust(
        source_id=source_id,
        target_id=target_id,
        db_path=db,
    )
    typer.echo(
        f"Trust: source={result['source_id']} target={result['target_id']} "
        f"score={result['score']}/100 confidence={result['confidence']}% "
        f"behaviors={result['behavior_count']} "
        f"{'(cold start)' if result.get('cold_start') else ''}"
    )


@graph_app.command(name="detect")
def detect_cmd(
    pattern: str = typer.Option(
        None,
        "--pattern",
        "-p",
        help="Collusion pattern: price_parallelism, deal_rotation, market_allocation",
    ),
    entity: str = typer.Option(
        None,
        "--entity",
        "-e",
        help="Filter results to flags involving this entity",
    ),
    db: str = typer.Option(_default_db, "--db", help="Path to graph database"),
) -> None:
    """Run collusion detection and show results."""
    results = detect_collusion(
        pattern=pattern,
        entity_id=entity,
        db_path=db,
    )
    if not results:
        typer.echo("No collusion flags detected.")
        return

    typer.echo(f"Found {len(results)} collusion flag(s):")
    for flag in results:
        typer.echo(
            f"  [{flag['severity']}] {flag['pattern']}: "
            f"{flag['entity_a_id']} <-> {flag['entity_b_id']} "
            f"(id={flag['id']})"
        )


@graph_app.command(name="status")
def status_cmd(
    db: str = typer.Option(_default_db, "--db", help="Path to graph database"),
) -> None:
    """Show graph database metadata summary."""
    result = get_status(db_path=db)
    typer.echo("Graph Status:")
    typer.echo(f"  Schema version:    {result['schema_version']}")
    typer.echo(f"  Entities:          {result['entities']}")
    typer.echo(f"  Behaviors:         {result['behaviors']}")
    typer.echo(f"  Trust scores:      {result['trust_scores']}")
    typer.echo(f"  Active collusion:  {result['active_collusion_flags']}")

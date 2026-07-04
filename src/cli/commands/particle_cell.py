"""CLI commands for the AI Cell Runtime Engine (``mekong cell run``).

Wires into ``particle_app`` in ``app_setup.py`` as a sub-app::

    mekong cell run <role> --particle <dir> --prompt "analyze ..."
    mekong cell run <role> --particle <dir> --prompt "analyze" --auto-compliance
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from typing import Optional

from dataclasses import asdict

from src.mekong.cells.config import (
    find_cell_configs,
    load_cell_config,
    resolve_particle_config,
)
from src.mekong.cells.guardian import load_guardian_thresholds, run_guardian_review
from src.mekong.cells.runner import (
    run_cell,
    run_compliance,
    run_strategist,
    run_strategist_with_compliance,
)
from src.cli.commands.particle_init import particle_app
from src.mekong.cells.types import CellConfig
from src.mekong.graph.network import (
    connect_particles,
    cross_particle_strategist,
    particle_network_status,
)
from src.mekong.graph.store import get_behaviors, open_db

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

cell_app = typer.Typer(
    name="cell",
    help="AI Cell Runtime Engine — execute and audit autonomous cells",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def _fail(msg: str, code: int = 1) -> None:
    typer.echo(f"Error: {msg}", err=True)
    raise typer.Exit(code=code)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@cell_app.command(name="run")
def run_cmd(
    role: str = typer.Argument(
        ...,
        help="Cell role identifier (e.g. strategist, compliance)",
    ),
    particle: str = typer.Option(
        ".",
        "--particle",
        "-p",
        help="Particle directory path or name",
    ),
    prompt: str = typer.Option(
        "",
        "--prompt",
        "-m",
        help="Task prompt for the AI Cell",
    ),
    input: Optional[Path] = typer.Option(  # noqa: A002
        None,
        "--input",
        "-i",
        help="Read prompt from a file instead of --prompt",
        exists=True,
        readable=True,
    ),
    auto_compliance: bool = typer.Option(
        False,
        "--auto-compliance",
        "-c",
        help="Run constitutional compliance check after execution",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-f",
        help="Path to cell YAML config file (default: "
             "<particle>/cells/<role>.yaml)",
        exists=True,
        readable=True,
    ),
    network: bool = typer.Option(
        False,
        "--network",
        "-w",
        help="Include trust-network context (strategist only)",
    ),
) -> None:
    """Execute an AI Cell and return its recommendation as JSON.

    Usage examples::

        # Run from within a particle directory
        mekong cell run strategist --prompt "analyze the market"

        # Specify a particle directory
        mekong cell run strategist --particle ./my-particle --prompt "analyze"

        # Read prompt from a file
        mekong cell run strategist --input /tmp/prompt.txt

        # Run with compliance check
        mekong cell run strategist \\
            --particle ./my-particle \\
            --prompt "propose budget" \\
            --auto-compliance

        # Run with trust-network awareness (strategist only)
        mekong cell run strategist \\
            --particle ./my-particle \\
            --prompt "analyze partnerships" \\
            --network

        # Explicit config path
        mekong cell run strategist \\
            --particle ./my-particle \\
            --config ./my-particle/cells/strategist.yaml \\
            --prompt "analyze"
    """
    # 1. Resolve particle directory
    try:
        particle_dir = resolve_particle_config(particle)
    except FileNotFoundError as exc:
        _fail(str(exc))

    # 2. Load cell config
    if config_path:
        config_file = config_path
    else:
        config_file = particle_dir / "cells" / f"{role}.yaml"

    if not config_file.exists():
        _fail(
            f"Cell config not found: {config_file}. "
            f"Use --config to specify an explicit path, or ensure "
            f"{particle_dir}/cells/{role}.yaml exists."
        )

    try:
        config: CellConfig = load_cell_config(str(config_file))
    except (FileNotFoundError, ValueError) as exc:
        _fail(str(exc))

    # 3. Resolve prompt
    resolved_prompt = prompt
    if input:
        resolved_prompt = input.read_text(encoding="utf-8").strip()
    if not resolved_prompt:
        _fail("No prompt provided. Use --prompt or --input.")

    # 4. Handle strategist with trust-network awareness
    if network and role == "strategist":
        try:
            result = cross_particle_strategist(
                particle_id=particle,
                question=resolved_prompt,
            )
        except (ValueError, FileNotFoundError, RuntimeError) as exc:
            _fail(str(exc))
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # 5. Handle strategist with auto-compliance shortcut
    if auto_compliance and role == "strategist":
        try:
            result: dict[str, object] = run_strategist_with_compliance(
                particle_id=particle,
                prompt=resolved_prompt,
            )
        except (ValueError, FileNotFoundError, RuntimeError) as exc:
            _fail(str(exc))
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # 6. Execute cell — use run_strategist for strategist, run_cell for others
    try:
        if role == "strategist":
            recommendation = run_strategist(
                config=config,
                particle_dir=str(particle_dir),
                prompt=resolved_prompt,
            )
        else:
            recommendation = run_cell(
                config=config,
                particle_dir=str(particle_dir),
                prompt=resolved_prompt,
            )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        _fail(str(exc))

    # 7. Optional compliance check (for non-strategist roles or strategist
    #    without --auto-compliance — strategist+auto-compliance is handled
    #    above by run_strategist_with_compliance)
    compliance_result = None
    if auto_compliance:
        try:
            compliance_result = run_compliance(
                config=config,
                particle_dir=str(particle_dir),
                recommendation=recommendation,
            )
        except (ValueError, FileNotFoundError) as exc:
            typer.echo(f"Compliance check error: {exc}", err=True)

    # 8. Output
    output: dict[str, object] = {
        "role": config.role,
        "particle": str(particle_dir),
        "recommendation": {
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "rationale": recommendation.rationale,
            "risk_factors": recommendation.risk_factors,
            "estimated_impact": recommendation.estimated_impact,
        },
    }

    if compliance_result:
        output["compliance"] = {
            "verdict": compliance_result.verdict,
            "checked_articles": compliance_result.checked_articles,
            "violations": compliance_result.violations,
            "warnings": compliance_result.warnings,
        }

    typer.echo(json.dumps(output, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Command: list — enumerate cell configs for a particle
# ---------------------------------------------------------------------------


@cell_app.command(name="list")
def list_cmd(
    particle: str = typer.Argument(
        ...,
        help="Particle directory path or name",
    ),
) -> None:
    """List available AI Cell configurations for a particle.

    Scans the particle's ``cells/`` directory for YAML config files and
    displays their contents.

    Usage examples::

        # List cells in the current particle directory
        mekong cell list .

        # List cells for a named particle
        mekong cell list my-particle
    """
    try:
        particle_dir = resolve_particle_config(particle)
    except FileNotFoundError as exc:
        _fail(str(exc))

    configs = find_cell_configs(particle_dir)

    output: list[dict[str, object]] = []
    for cfg in configs:
        entry: dict[str, object] = {}
        for k, v in cfg.items():
            if not k.startswith("_"):
                entry[str(k)] = v
        entry["config_path"] = str(cfg["_path"])
        output.append(entry)

    typer.echo(json.dumps({
        "particle": str(particle_dir),
        "cells": output,
    }, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Command: history — show recent cell executions from the behavior graph
# ---------------------------------------------------------------------------


@cell_app.command(name="history")
def history_cmd(
    particle: str = typer.Argument(
        ...,
        help="Particle directory path or name",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of recent executions to show",
    ),
) -> None:
    """Show recent AI Cell executions from the behavior graph.

    Queries the ZenOS behavior graph for the most recent cell executions
    involving the specified particle.

    Usage examples::

        # Show last 10 executions for the current particle
        mekong cell history .

        # Show last 5 executions for a named particle
        mekong cell history my-particle --limit 5
    """
    try:
        particle_dir = resolve_particle_config(particle)
    except FileNotFoundError as exc:
        _fail(str(exc))

    db_path: str | None = None  # Use environment default
    conn = open_db(db_path)
    try:
        target_id = f"particle:{particle_dir.name}"
        behaviors = get_behaviors(
            conn,
            target_id=target_id,
            limit=limit,
        )
    finally:
        conn.close()

    output: list[dict[str, object]] = [
        {
            "id": b.id,
            "source_id": b.source_id,
            "action": b.action,
            "value": b.value,
            "timestamp": b.timestamp,
        }
        for b in behaviors
    ]

    typer.echo(json.dumps({
        "particle": str(particle_dir),
        "history": output,
    }, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Command: guardian — run a Guardian Cell health review
# ---------------------------------------------------------------------------


@cell_app.command(name="guardian")
def guardian_cmd(
    particle: str = typer.Argument(
        ...,
        help="Particle identifier to review (e.g. particle:alpha)",
    ),
    hours: int = typer.Option(
        168,
        "--hours",
        "-t",
        help="Review window in hours (default 168 = 7 days)",
    ),
) -> None:
    """Run a Guardian Cell health review for a particle.

    Queries the ZenOS behavior graph for the last *hours* hours and
    produces a health report with status (GREEN / YELLOW / RED),
    violation metrics, collusion flags, trust trend, and any alerts.

    Usage examples::

        # Review a particle with default 7-day window
        mekong cell run guardian particle:alpha

        # Review with a custom 30-day window
        mekong cell run guardian particle:alpha --hours 720

        # Short form
        mekong cell run guardian particle:alpha -t 720
    """
    thresholds = load_guardian_thresholds(particle)
    report = run_guardian_review(particle, thresholds, hours_back=hours)
    typer.echo(json.dumps(asdict(report), indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Command: connect — establish a trust relationship between two particles
# ---------------------------------------------------------------------------


@particle_app.command(name="connect")
def connect_cmd(
    particle_a: str = typer.Argument(
        ...,
        help="First particle name or directory path",
    ),
    particle_b: str = typer.Argument(
        ...,
        help="Second particle name or directory path",
    ),
) -> None:
    """Establish a trust relationship between two particles.

    Registers both particles in the behavior graph, records bidirectional
    connection behaviors, and computes default trust scores (50 / neutral).

    Usage examples::

        # Connect two particles by name
        mekong particle connect alpha beta

        # Connect by directory path
        mekong particle connect ./particles/alpha ./particles/beta
    """
    try:
        result = connect_particles(
            particle_a=particle_a,
            particle_b=particle_b,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        _fail(str(exc))

    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Command: status — show particle network status
# ---------------------------------------------------------------------------


@particle_app.command(name="status")
def status_cmd(
    particle_id: str = typer.Argument(
        ...,
        help="Particle name or directory path",
    ),
) -> None:
    """Show a particle's network status — connections, trust, and collusion.

    Queries the behavior graph for all behaviors, trust scores, and collusion
    flags involving the specified particle.

    Usage examples::

        # Status for a named particle
        mekong particle status alpha

        # Status by directory path
        mekong particle status ./particles/alpha
    """
    try:
        info = particle_network_status(particle_id=particle_id)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        _fail(str(exc))

    typer.echo(json.dumps(info, indent=2, ensure_ascii=False))

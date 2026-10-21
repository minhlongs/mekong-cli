# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Cell execution command (`mekong cell run`) for AI Cell Runtime Engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
import sys

import typer

from src.mekong.cells.config import load_cell_config, resolve_particle_config
from src.mekong.cells.runner import (
    run_cell,
    run_compliance,
    run_strategist,
    run_strategist_with_compliance,
)
from src.mekong.cells.types import CellConfig
from src.mekong.graph.network import cross_particle_strategist


def _fail(msg: str, code: int = 1) -> None:
    typer.echo(f"Error: {msg}", err=True)
    raise typer.Exit(code=code)


def _lookup(attr: str, fallback: object) -> object:
    mod = sys.modules.get("src.cli.commands.particle_cell")
    return getattr(mod, attr, fallback) if mod is not None else fallback


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
        help="Path to cell YAML config file (default: <particle>/cells/<role>.yaml)",
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
    """Execute an AI Cell and return its recommendation as JSON."""
    resolve_fn = _lookup("resolve_particle_config", resolve_particle_config)
    load_cfg_fn = _lookup("load_cell_config", load_cell_config)
    try:
        particle_dir = resolve_fn(particle)  # type: ignore[operator]
    except FileNotFoundError as exc:
        _fail(str(exc))

    config_file = config_path if config_path else particle_dir / "cells" / f"{role}.yaml"
    if not config_file.exists():
        _fail(
            f"Cell config not found: {config_file}. "
            f"Use --config to specify an explicit path, or ensure "
            f"{particle_dir}/cells/{role}.yaml exists."
        )

    try:
        config: CellConfig = load_cfg_fn(str(config_file))  # type: ignore[operator]
    except (FileNotFoundError, ValueError) as exc:
        _fail(str(exc))

    resolved_prompt = input.read_text(encoding="utf-8").strip() if input else prompt
    if not resolved_prompt:
        _fail("No prompt provided. Use --prompt or --input.")

    if network and role == "strategist":
        cross_fn = _lookup("cross_particle_strategist", cross_particle_strategist)
        try:
            result = cross_fn(particle_id=particle, question=resolved_prompt)  # type: ignore[operator]
        except (ValueError, FileNotFoundError, RuntimeError) as exc:
            _fail(str(exc))
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if auto_compliance and role == "strategist":
        strat_comp_fn = _lookup("run_strategist_with_compliance", run_strategist_with_compliance)
        try:
            result = strat_comp_fn(particle_id=particle, prompt=resolved_prompt)  # type: ignore[operator]
        except (ValueError, FileNotFoundError, RuntimeError) as exc:
            _fail(str(exc))
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    try:
        if role == "strategist":
            strat_fn = _lookup("run_strategist", run_strategist)
            recommendation = strat_fn(  # type: ignore[operator]
                config=config,
                particle_dir=str(particle_dir),
                prompt=resolved_prompt,
            )
        else:
            cell_fn = _lookup("run_cell", run_cell)
            recommendation = cell_fn(  # type: ignore[operator]
                config=config,
                particle_dir=str(particle_dir),
                prompt=resolved_prompt,
            )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        _fail(str(exc))

    compliance_result = None
    if auto_compliance:
        comp_fn = _lookup("run_compliance", run_compliance)
        try:
            compliance_result = comp_fn(  # type: ignore[operator]
                config=config,
                particle_dir=str(particle_dir),
                recommendation=recommendation,
            )
        except (ValueError, FileNotFoundError) as exc:
            typer.echo(f"Compliance check error: {exc}", err=True)

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

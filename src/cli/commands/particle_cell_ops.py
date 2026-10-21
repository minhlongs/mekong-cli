# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Cell list, history, guardian, and particle network connect/status commands."""

from __future__ import annotations

from dataclasses import asdict
import json
import sys

import typer

from src.cli.commands.particle_cell_run import _fail, _lookup
from src.mekong.cells.config import find_cell_configs, resolve_particle_config
from src.mekong.cells.guardian import load_guardian_thresholds, run_guardian_review
from src.mekong.graph.network import connect_particles, particle_network_status
from src.mekong.graph.store import get_behaviors, open_db


def list_cmd(
    particle: str = typer.Argument(
        ...,
        help="Particle directory path or name",
    ),
) -> None:
    """List available AI Cell configurations for a particle."""
    resolve_fn = _lookup("resolve_particle_config", resolve_particle_config)
    find_fn = _lookup("find_cell_configs", find_cell_configs)
    try:
        particle_dir = resolve_fn(particle)  # type: ignore[operator]
    except FileNotFoundError as exc:
        _fail(str(exc))

    configs = find_fn(particle_dir)  # type: ignore[operator]

    output: list[dict[str, object]] = []
    for cfg in configs:
        entry: dict[str, object] = {
            str(k): v for k, v in cfg.items() if not k.startswith("_")
        }
        entry["config_path"] = str(cfg["_path"])
        output.append(entry)

    typer.echo(json.dumps({
        "particle": str(particle_dir),
        "cells": output,
    }, indent=2, ensure_ascii=False))


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
    """Show recent AI Cell executions from the behavior graph."""
    resolve_fn = _lookup("resolve_particle_config", resolve_particle_config)
    open_db_fn = _lookup("open_db", open_db)
    get_behaviors_fn = _lookup("get_behaviors", get_behaviors)
    try:
        particle_dir = resolve_fn(particle)  # type: ignore[operator]
    except FileNotFoundError as exc:
        _fail(str(exc))

    conn = open_db_fn(None)  # type: ignore[operator]
    try:
        target_id = f"particle:{particle_dir.name}"
        behaviors = get_behaviors_fn(conn, target_id=target_id, limit=limit)  # type: ignore[operator]
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
    """Run a Guardian Cell health review for a particle."""
    load_thresh_fn = _lookup("load_guardian_thresholds", load_guardian_thresholds)
    run_guard_fn = _lookup("run_guardian_review", run_guardian_review)
    thresholds = load_thresh_fn(particle)  # type: ignore[operator]
    report = run_guard_fn(particle, thresholds, hours_back=hours)  # type: ignore[operator]
    typer.echo(json.dumps(asdict(report), indent=2, ensure_ascii=False))


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
    """Establish a trust relationship between two particles."""
    connect_fn = _lookup("connect_particles", connect_particles)
    try:
        result = connect_fn(particle_a=particle_a, particle_b=particle_b)  # type: ignore[operator]
    except (FileNotFoundError, ValueError, RuntimeError):
        try:
            from src.core.particle_engine import ParticleEngine
            result = ParticleEngine().connect_particles(particle_a=particle_a, particle_b=particle_b)
        except Exception as exc:
            _fail(str(exc))

    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


def status_cmd(
    particle_id: str = typer.Argument(
        ...,
        help="Particle name or directory path",
    ),
) -> None:
    """Show a particle's network status — connections, trust, and collusion."""
    status_fn = _lookup("particle_network_status", particle_network_status)
    try:
        info = status_fn(particle_id=particle_id)  # type: ignore[operator]
    except (FileNotFoundError, ValueError, RuntimeError):
        try:
            from src.core.particle_engine import ParticleEngine
            info = ParticleEngine().get_particle_status(particle_id_or_name=particle_id)
        except Exception as exc:
            _fail(str(exc))

    typer.echo(json.dumps(info, indent=2, ensure_ascii=False))


__all__ = [
    "connect_cmd",
    "guardian_cmd",
    "history_cmd",
    "list_cmd",
    "status_cmd",
    "sys",
]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Multi-particle network operations for the ZenOS behavior graph."""

from __future__ import annotations

import json
import os
from typing import Any

from src.mekong.cells.config import load_cell_config, resolve_particle_config
from src.mekong.cells.strategist import parse_strategist_output
from src.mekong.cells.types import CellConfig
from src.mekong.constitution.parser import parse_constitution
from src.mekong.graph.api import record_behavior
from src.mekong.graph.network_llm import (
    _NETWORK_DEFAULT_DB_PATH,
    _OPENROUTER_BASE_URL,
    _build_network_strategist_prompts,
    _call_llm,
    _entity_id,
    _get_api_key,
)
from src.mekong.graph.network_queries import particle_network_status
from src.mekong.graph.store import ensure_entity, find_collusion, open_db


def connect_particles(
    particle_a: str,
    particle_b: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Establish a trust relationship between two particles."""
    try:
        dir_a = resolve_particle_config(particle_a)
        dir_b = resolve_particle_config(particle_b)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Particle not found: {exc}") from exc

    name_a, name_b = dir_a.name, dir_b.name
    id_a, id_b = _entity_id(name_a), _entity_id(name_b)

    conn = open_db(db_path)
    try:
        ensure_entity(conn, id_a, name_a, kind="particle")
        ensure_entity(conn, id_b, name_b, kind="particle")

        from src.mekong.graph.store import record_behavior as _record_behavior
        from src.mekong.graph.trust import compute_trust

        _record_behavior(conn, source_id=id_a, target_id=id_b, action="particle_connect", payload={"initiator": name_a})
        _record_behavior(conn, source_id=id_b, target_id=id_a, action="particle_connect", payload={"initiator": name_a})
        score_ab, _ = compute_trust(conn, id_a, id_b)
        score_ba, _ = compute_trust(conn, id_b, id_a)

        result: dict[str, Any] = {
            "status": "connected",
            "particle_a": {"id": id_a, "name": name_a, "path": str(dir_a)},
            "particle_b": {"id": id_b, "name": name_b, "path": str(dir_b)},
            "trust": {f"{name_a}_to_{name_b}": score_ab, f"{name_b}_to_{name_a}": score_ba},
        }
    finally:
        conn.close()

    from rich.console import Console

    console = Console()
    console.print(f"[bold green]Connected[/] {name_a} <-> {name_b}")
    console.print(f"  Trust: {name_a}->{name_b} = {score_ab}/100")
    console.print(f"  Trust: {name_b}->{name_a} = {score_ba}/100")
    return result


def cross_particle_strategist(
    particle_id: str,
    question: str,
    network_size: int = 3,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Run a strategist cell considering the particle's trust network."""
    try:
        particle_dir = resolve_particle_config(particle_id)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Particle not found: {exc}") from exc

    entity = _entity_id(particle_dir.name)
    constitution_path = particle_dir / "ZENOS.md"
    if not constitution_path.exists():
        raise FileNotFoundError(
            f"Constitution not found at {constitution_path}. "
            f"Ensure '{particle_dir}' is a valid particle directory."
        )
    constitution = parse_constitution(str(constitution_path))

    network_context: list[dict[str, Any]] = []
    conn = open_db(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM trust_scores WHERE source_id = ? AND score >= 50 ORDER BY score DESC LIMIT ?",
            (entity, network_size),
        ).fetchall()
        for row in rows:
            peer_id: str = row["target_id"]
            peer_ent = conn.execute("SELECT name, kind FROM entities WHERE id = ?", (peer_id,)).fetchone()
            network_context.append({
                "source_id": entity,
                "target_id": peer_id,
                "target_name": peer_ent["name"] if peer_ent else peer_id,
                "score": row["score"],
                "confidence": row["confidence"],
                "behavior_count": row["behavior_count"],
            })
    finally:
        conn.close()

    system_prompt, user_prompt = _build_network_strategist_prompts(
        particle_dir.name, constitution, question, network_context
    )

    config_path = particle_dir / "cells" / "strategist.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Strategist cell config not found at {config_path}. "
            f"Ensure '{particle_dir}' has a 'cells/strategist.yaml' file."
        )
    config: CellConfig = load_cell_config(str(config_path))
    if config.privileges.max_budget <= 0:
        raise ValueError(f"Cell '{config.role}' budget exhausted: max_budget={config.privileges.max_budget}.")

    raw = _call_llm(system_prompt, user_prompt, config.model)
    recommendation = parse_strategist_output(json.dumps(raw))

    record_behavior(
        source_id=f"cell:{config.role}",
        source_name=f"Strategist AI Cell: {config.role} (network)",
        target_id=entity,
        target_name=particle_dir.name,
        action="network_strategist_recommendation",
        payload={
            "model": config.model,
            "question": question[:200],
            "recommendation": recommendation.recommendation[:200],
            "confidence": recommendation.confidence,
            "network_size": len(network_context),
        },
        value=recommendation.confidence,
        db_path=db_path,
    )

    return {
        "role": config.role,
        "particle": str(particle_dir),
        "network_context": {"peer_count": len(network_context), "peers": network_context},
        "recommendation": {
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "rationale": recommendation.rationale,
            "risk_factors": recommendation.risk_factors,
            "estimated_impact": recommendation.estimated_impact,
        },
    }


__all__ = [
    "_NETWORK_DEFAULT_DB_PATH",
    "_OPENROUTER_BASE_URL",
    "_call_llm",
    "_entity_id",
    "_get_api_key",
    "connect_particles",
    "cross_particle_strategist",
    "find_collusion",
    "os",
    "particle_network_status",
]

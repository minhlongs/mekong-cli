# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Multi-particle network operations for the ZenOS behavior graph.

Provides high-level operations for connecting particles, inspecting network
status, and running strategist cells with trust-network context.
"""

from __future__ import annotations

import json
import os
from typing import Any

from src.mekong.cells.config import load_cell_config, resolve_particle_config
from src.mekong.cells.strategist import parse_strategist_output
from src.mekong.cells.types import CellConfig
from src.mekong.constitution.parser import parse_constitution
from src.mekong.graph.api import record_behavior
from src.mekong.graph.store import (
    ensure_entity,
    find_collusion,
    open_db,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NETWORK_DEFAULT_DB_PATH = ".mekong/graph.db"

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entity_id(name: str) -> str:
    """Build a particle entity ID from a directory name."""
    return f"particle:{name}"


def _get_api_key() -> str:
    """Return the first available LLM API key."""
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "No LLM API key found. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY."
        )
    return key


def _call_llm(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    """Call the LLM via the OpenRouter-compatible API and return parsed JSON.

    Mirrors the private helper in src.mekong.cells.runner for consistency.
    """
    import re

    import requests

    api_key = _get_api_key()
    base_url = os.environ.get("OPENROUTER_BASE_URL", _OPENROUTER_BASE_URL)

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        if "error" in data:
            err = data["error"]
            raise RuntimeError(f"LLM API error: {err.get('message', err)}")
    except requests.RequestException as exc:
        raise RuntimeError(f"LLM API call failed: {exc}") from exc

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("LLM returned no choices")

    content = choices[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("LLM returned empty content")

    # Strip code fences
    content = content.strip()
    if content.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()
        else:
            brace_start = content.find("{")
            if brace_start >= 0:
                content = content[brace_start:]
                if content.endswith("```"):
                    content = content[:-3].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM response is not valid JSON: {exc}\nRaw: {content[:500]}"
        ) from exc


# ---------------------------------------------------------------------------
# Public API — connect_particles
# ---------------------------------------------------------------------------


def connect_particles(
    particle_a: str,
    particle_b: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Establish a trust relationship between two particles.

    Steps
    -----
    1. Resolve both particle directories.
    2. Register both particles as entities in the behavior graph.
    3. Record ``particle_connect`` behaviors in both directions.
    4. Compute and persist trust scores (default 50 / neutral via cold start).
    5. Return a summary of the connection.

    Parameters
    ----------
    particle_a:
        Name, path, or identifier for the first particle.
    particle_b:
        Name, path, or identifier for the second particle.
    db_path:
        Optional path to the behavior graph database. Uses the environment
        default when ``None``.

    Returns
    -------
    dict
        A summary containing the connection status, entity IDs, and trust scores.
    """
    # 1. Resolve particle directories
    try:
        dir_a = resolve_particle_config(particle_a)
        dir_b = resolve_particle_config(particle_b)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Particle not found: {exc}") from exc

    name_a = dir_a.name
    name_b = dir_b.name
    id_a = _entity_id(name_a)
    id_b = _entity_id(name_b)

    # 2. Open DB and establish connection
    conn = open_db(db_path)
    try:
        # 3. Ensure both entities exist
        ensure_entity(conn, id_a, name_a, kind="particle")
        ensure_entity(conn, id_b, name_b, kind="particle")

        # 4. Record particle_connect behaviors in both directions
        from src.mekong.graph.store import record_behavior as _record_behavior

        _record_behavior(
            conn,
            source_id=id_a,
            target_id=id_b,
            action="particle_connect",
            payload={"initiator": name_a},
        )
        _record_behavior(
            conn,
            source_id=id_b,
            target_id=id_a,
            action="particle_connect",
            payload={"initiator": name_a},
        )

        # 5. Compute and persist trust scores (cold start -> 50 neutral)
        from src.mekong.graph.trust import compute_trust

        score_ab, _ = compute_trust(conn, id_a, id_b)
        score_ba, _ = compute_trust(conn, id_b, id_a)

        result: dict[str, Any] = {
            "status": "connected",
            "particle_a": {"id": id_a, "name": name_a, "path": str(dir_a)},
            "particle_b": {"id": id_b, "name": name_b, "path": str(dir_b)},
            "trust": {
                f"{name_a}_to_{name_b}": score_ab,
                f"{name_b}_to_{name_a}": score_ba,
            },
        }
    finally:
        conn.close()

    # 6. Print confirmation
    from rich.console import Console

    console = Console()
    console.print(f"[bold green]Connected[/] {name_a} <-> {name_b}")
    console.print(f"  Trust: {name_a}->{name_b} = {score_ab}/100")
    console.print(f"  Trust: {name_b}->{name_a} = {score_ba}/100")

    return result


# ---------------------------------------------------------------------------
# Public API — particle_network_status
# ---------------------------------------------------------------------------


def particle_network_status(
    particle_id: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Show a particle's network connections, trust scores, and collusion flags.

    Parameters
    ----------
    particle_id:
        Name, path, or identifier for the particle.
    db_path:
        Optional path to the behavior graph database.

    Returns
    -------
    dict
        Structured result with connections, trust scores, and collusion flags.
    """
    # 1. Resolve particle directory
    try:
        particle_dir = resolve_particle_config(particle_id)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Particle not found: {exc}") from exc

    entity = _entity_id(particle_dir.name)

    # 2. Open DB
    conn = open_db(db_path)
    try:
        # 3. Query behaviors involving this particle (as source or target)
        as_source = conn.execute(
            "SELECT * FROM behaviors WHERE source_id = ? ORDER BY timestamp DESC LIMIT 100",
            (entity,),
        ).fetchall()
        as_target = conn.execute(
            "SELECT * FROM behaviors WHERE target_id = ? ORDER BY timestamp DESC LIMIT 100",
            (entity,),
        ).fetchall()

        behaviors_list: list[dict[str, Any]] = []
        for row in as_source:
            behaviors_list.append({
                "id": row["id"],
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "action": row["action"],
                "value": row["value"],
                "timestamp": row["timestamp"],
            })
        for row in as_target:
            behaviors_list.append({
                "id": row["id"],
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "action": row["action"],
                "value": row["value"],
                "timestamp": row["timestamp"],
            })

        # Deduplicate by id and re-sort newest first
        seen: set[int] = set()
        unique_behaviors: list[dict[str, Any]] = []
        for b in sorted(behaviors_list, key=lambda x: x["timestamp"], reverse=True):
            if b["id"] not in seen:
                seen.add(b["id"])
                unique_behaviors.append(b)

        # 4. Query trust scores for this particle (outgoing and incoming)
        outgoing_trust = conn.execute(
            "SELECT * FROM trust_scores WHERE source_id = ? ORDER BY score DESC",
            (entity,),
        ).fetchall()
        incoming_trust = conn.execute(
            "SELECT * FROM trust_scores WHERE target_id = ? ORDER BY score DESC",
            (entity,),
        ).fetchall()

        def _trust_row(row: Any) -> dict[str, Any]:
            return {
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "score": row["score"],
                "confidence": row["confidence"],
                "behavior_count": row["behavior_count"],
                "updated_at": row["updated_at"],
            }

        # 5. Query collusion flags involving this particle
        collusion_flags = find_collusion(conn, entity_id=entity, active_only=True)
        collusion_list: list[dict[str, Any]] = [
            {
                "id": f.id,
                "pattern": f.pattern,
                "entity_a_id": f.entity_a_id,
                "entity_b_id": f.entity_b_id,
                "severity": f.severity,
                "detected_at": f.detected_at,
            }
            for f in collusion_flags
        ]

        # 6. Find unique counterparties
        counterparties: set[str] = set()
        for row in outgoing_trust:
            counterparties.add(row["target_id"])
        for row in incoming_trust:
            counterparties.add(row["source_id"])

        # Look up entity names for counterparties
        counterparty_info: dict[str, dict[str, Any]] = {}
        for cid in counterparties:
            ent = conn.execute(
                "SELECT name, kind, metadata FROM entities WHERE id = ?",
                (cid,),
            ).fetchone()
            if ent:
                counterparty_info[cid] = {
                    "name": ent["name"],
                    "kind": ent["kind"],
                }

    finally:
        conn.close()

    return {
        "particle": {
            "id": entity,
            "name": particle_dir.name,
            "path": str(particle_dir),
        },
        "behaviors": unique_behaviors,
        "behaviors_count": len(unique_behaviors),
        "outgoing_trust": [_trust_row(r) for r in outgoing_trust],
        "incoming_trust": [_trust_row(r) for r in incoming_trust],
        "counterparties": {
            cid: counterparty_info.get(cid, {})
            for cid in sorted(counterparties)
        },
        "collusion_flags": collusion_list,
    }


# ---------------------------------------------------------------------------
# Public API — cross_particle_strategist
# ---------------------------------------------------------------------------


def cross_particle_strategist(
    particle_id: str,
    question: str,
    network_size: int = 3,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Run a strategist cell considering the particle's trust network.

    Loads the particle's constitution, queries the trust network for connected
    particles with trust >= 50, includes the network context in the strategist
    system prompt, and returns the recommendation alongside network context.

    Parameters
    ----------
    particle_id:
        Name, path, or identifier for the particle.
    question:
        The strategic question to analyze.
    network_size:
        Maximum number of peer particles to include in the network context
        (default 3).
    db_path:
        Optional path to the behavior graph database.

    Returns
    -------
    dict
        The strategist recommendation augmented with network context.
    """
    # 1. Resolve particle directory
    try:
        particle_dir = resolve_particle_config(particle_id)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Particle not found: {exc}") from exc

    entity = _entity_id(particle_dir.name)

    # 2. Load constitution
    constitution_path = particle_dir / "ZENOS.md"
    if not constitution_path.exists():
        raise FileNotFoundError(
            f"Constitution not found at {constitution_path}. "
            f"Ensure '{particle_dir}' is a valid particle directory."
        )
    constitution = parse_constitution(str(constitution_path))

    # 3. Query trust network
    network_context: list[dict[str, Any]] = []
    conn = open_db(db_path)
    try:
        # Outgoing trust scores >= 50, ordered highest first
        rows = conn.execute(
            "SELECT * FROM trust_scores WHERE source_id = ? AND score >= 50 ORDER BY score DESC LIMIT ?",
            (entity, network_size),
        ).fetchall()

        for row in rows:
            peer_id: str = row["target_id"]
            # Look up peer entity info
            peer_ent = conn.execute(
                "SELECT name, kind FROM entities WHERE id = ?",
                (peer_id,),
            ).fetchone()
            peer_name = peer_ent["name"] if peer_ent else peer_id

            network_context.append({
                "source_id": entity,
                "target_id": peer_id,
                "target_name": peer_name,
                "score": row["score"],
                "confidence": row["confidence"],
                "behavior_count": row["behavior_count"],
            })
    finally:
        conn.close()

    # 4. Build network-augmented strategist prompt
    from src.mekong.cells.strategist import _extract_mission

    mission = _extract_mission(constitution)

    network_block = ""
    if network_context:
        lines = [f"You have {len(network_context)} trusted peer particle(s):"]
        for peer in network_context:
            lines.append(
                f"  - {peer['target_name']} (trust: {peer['score']}/100, "
                f"confidence: {peer['confidence']}/100, "
                f"{peer['behavior_count']} interactions)"
            )
        network_block = (
            "\n\n--- Trust Network Context ---\n"
            + "\n".join(lines)
            + "\nConsider the perspectives, capabilities, and potential "
            "collaboration opportunities with these trusted peers when "
            "formulating your recommendation.\n"
            "--- End Trust Network Context ---"
        )

    system_prompt = (
        f"You are a Strategist AI Cell operating under the ZenOS constitution "
        f'for "{particle_dir.name}".\n\n'
        f"Your role is to analyze strategic questions and provide reasoned "
        f"recommendations that align with the particle's founding principles.\n\n"
        f"Mission Statement:\n{mission}"
        f"{network_block}\n\n"
        f"You MUST respond with a valid JSON object containing exactly these fields:\n"
        f"- recommendation: your strategic recommendation (string, REQUIRED)\n"
        f"- confidence: confidence score between 0.0 and 1.0 (number, REQUIRED)\n"
        f"- rationale: detailed explanation of your reasoning "
        f"(string, REQUIRED, MUST be non-empty)\n"
        f"- risk_factors: list of potential risks (array of strings)\n"
        f"- estimated_impact: 'low', 'medium', or 'high' (string)\n\n"
        f"Respond ONLY with the JSON object. Do NOT wrap it in markdown "
        f"code fences."
    )

    articles_summary = "\n".join(
        f"Article {a.number}: {a.title}" for a in constitution.articles
    )
    user_prompt = (
        f"Strategic Question: {question}\n\n"
        f"Particle Constitution:\n{articles_summary}\n\n"
        f"Analyze the question above in the context of the particle's "
        f"constitution and mission. Provide a strategic recommendation "
        f"with confidence score, rationale, risk factors, and estimated impact."
    )

    # 5. Load strategist cell config
    config_path = particle_dir / "cells" / "strategist.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Strategist cell config not found at {config_path}. "
            f"Ensure '{particle_dir}' has a 'cells/strategist.yaml' file."
        )
    config: CellConfig = load_cell_config(str(config_path))

    # 6. Enforce privilege gates
    if config.privileges.max_budget <= 0:
        raise ValueError(
            f"Cell '{config.role}' budget exhausted: "
            f"max_budget={config.privileges.max_budget}."
        )

    # 7. Call LLM
    raw = _call_llm(system_prompt, user_prompt, config.model)
    raw_str = json.dumps(raw)

    # 8. Parse output
    recommendation = parse_strategist_output(raw_str)

    # 9. Record to behavior graph
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

    # 10. Build return value
    return {
        "role": config.role,
        "particle": str(particle_dir),
        "network_context": {
            "peer_count": len(network_context),
            "peers": network_context,
        },
        "recommendation": {
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "rationale": recommendation.rationale,
            "risk_factors": recommendation.risk_factors,
            "estimated_impact": recommendation.estimated_impact,
        },
    }

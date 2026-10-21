# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Network status query operations for the ZenOS behavior graph."""

from __future__ import annotations

from typing import Any


def particle_network_status(
    particle_id: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Show a particle's network connections, trust scores, and collusion flags."""
    import src.mekong.graph.network as _net

    try:
        particle_dir = _net.resolve_particle_config(particle_id)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Particle not found: {exc}") from exc

    entity = _net._entity_id(particle_dir.name)

    conn = _net.open_db(db_path)
    try:
        as_source = conn.execute(
            "SELECT * FROM behaviors WHERE source_id = ? ORDER BY timestamp DESC LIMIT 100",
            (entity,),
        ).fetchall()
        as_target = conn.execute(
            "SELECT * FROM behaviors WHERE target_id = ? ORDER BY timestamp DESC LIMIT 100",
            (entity,),
        ).fetchall()

        behaviors_list: list[dict[str, Any]] = []
        for row in (*as_source, *as_target):
            behaviors_list.append({
                "id": row["id"],
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "action": row["action"],
                "value": row["value"],
                "timestamp": row["timestamp"],
            })

        seen: set[int] = set()
        unique_behaviors: list[dict[str, Any]] = []
        for b in sorted(behaviors_list, key=lambda x: x["timestamp"], reverse=True):
            if b["id"] not in seen:
                seen.add(b["id"])
                unique_behaviors.append(b)

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

        collusion_flags = _net.find_collusion(conn, entity_id=entity, active_only=True)
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

        counterparties: set[str] = set()
        for row in outgoing_trust:
            counterparties.add(row["target_id"])
        for row in incoming_trust:
            counterparties.add(row["source_id"])

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

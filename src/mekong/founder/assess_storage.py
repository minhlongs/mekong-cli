# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Behavior-graph persistence and serialization helpers for founder genomes."""

from __future__ import annotations

from typing import Any

from src.mekong.founder.types import FounderGenome


def genome_to_dict(genome: FounderGenome) -> dict[str, Any]:
    """Serialise a ``FounderGenome`` to a plain dict for JSON storage."""
    return {
        "version": genome.version,
        "assessed_at": genome.assessed_at,
        "particle_id": genome.particle_id,
        "mission": genome.mission,
        "values": genome.values,
        "big_five": genome.big_five,
        "fears": genome.fears,
        "risk_profile": genome.risk_profile,
        "cognitive_biases": genome.cognitive_biases,
        "risk_level": genome.risk_level,
        "notes": genome.notes,
    }


def _store_genome(
    genome: FounderGenome,
    uid: str,
    db_path: str | None = None,
) -> None:
    """Persist a founder genome into the behaviour graph."""
    import src.mekong.founder.assess as _assess

    conn = _assess.open_db(db_path)
    try:
        _assess.ensure_entity(
            conn,
            entity_id=uid,
            name=genome.mission[:100] if genome.mission else f"Founder {uid[:8]}",
            kind=_assess._FOUNDER_KIND,
            metadata=genome_to_dict(genome),
        )

        source_id = f"founder:{uid}"
        _assess.ensure_entity(conn, entity_id=source_id, name=source_id, kind="founder_assessment")

        if genome.particle_id:
            target_id = f"particle:{genome.particle_id}"
            _assess.ensure_entity(conn, entity_id=target_id, name=target_id, kind="particle")
        else:
            target_id = f"founder:{uid}"

        _assess.record_behavior(
            conn,
            source_id=source_id,
            target_id=target_id,
            action="founder_assessment",
            payload={
                "version": genome.version,
                "risk_level": genome.risk_level,
                "bias_count": len(genome.cognitive_biases),
            },
            value=0.0,
        )
    finally:
        conn.close()

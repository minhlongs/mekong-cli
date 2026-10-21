# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Assessment orchestration and behavior-graph integration for founder genomes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.mekong.founder.assess_storage import _store_genome, genome_to_dict
from src.mekong.founder.scoring import (
    classify_risk_level,
    extract_biases,
    score_big_five,
    score_risk,
)
from src.mekong.founder.types import FounderGenome
from src.mekong.graph.store import (
    ensure_entity,
    get_entity as _get_entity,
    open_db,
    query_entities_by_kind,
    record_behavior,
)

_FOUNDER_KIND = "founder"


def assess_founder(
    mission: str,
    tipi_responses: dict[str, int],
    values: list[str],
    fears: list[dict],
    risk_ratings: dict[str, int],
    bias_responses: dict[str, bool],
    uid: str | None = None,
    particle_id: str | None = None,
    db_path: str | None = None,
) -> FounderGenome:
    """Run a full founder assessment, store results in the behavior graph."""
    big_five = score_big_five(tipi_responses)
    risk_scores = score_risk(risk_ratings)
    identified_biases = extract_biases(bias_responses)
    risk_level = classify_risk_level(len(identified_biases), risk_scores)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    genome = FounderGenome(
        version="1.0.0",
        assessed_at=now,
        particle_id=particle_id,
        mission=mission,
        values=values,
        big_five=big_five,
        fears=fears,
        risk_profile=risk_scores,
        cognitive_biases=identified_biases,
        risk_level=risk_level,
        notes=[
            "TIPI-10 is a brief screening instrument, not a clinical diagnostic tool.",
            "Self-reported biases have inherent accuracy limitations.",
            "Risk tolerance is context-dependent; scores reflect stated preference, "
            "not necessarily revealed behavior under pressure.",
        ],
    )

    _store_genome(genome, uid or str(uuid.uuid4()), db_path)
    return genome


def review_founder(
    entity_id: str,
    db_path: str | None = None,
) -> dict[str, Any] | None:
    """Load a founder genome from the behaviour graph by entity ID."""
    conn = open_db(db_path)
    try:
        entity = _get_entity(conn, entity_id)
        if entity is None:
            return None
        return entity
    finally:
        conn.close()


def list_founders(
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Return all founder entities from the behaviour graph."""
    conn = open_db(db_path)
    try:
        return query_entities_by_kind(conn, _FOUNDER_KIND)
    finally:
        conn.close()


__all__ = [
    "FounderGenome",
    "_FOUNDER_KIND",
    "_get_entity",
    "_store_genome",
    "assess_founder",
    "ensure_entity",
    "genome_to_dict",
    "list_founders",
    "open_db",
    "query_entities_by_kind",
    "record_behavior",
    "review_founder",
]

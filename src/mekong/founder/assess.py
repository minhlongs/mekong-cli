"""Assessment orchestration and behavior-graph integration for founder genomes.

Provides programmatic entry points for running a full founder assessment,
storing results in the ZenOS behavior graph, and retrieving them later.

Graph integration
-----------------
- Founder entity stored via ``ensure_entity()`` with ``kind="founder"``.
- Genome serialised as entity ``metadata`` (JSON blob).
- Assessment recorded as a behavior edge: ``source_id=f"founder:{uid}"``,
  ``action="founder_assessment"``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.mekong.founder.questions import (
    BIAS_QUESTIONS,
    FEAR_QUESTIONS,
    RISK_DIMENSIONS,
    RISK_QUESTIONS,
    SCHWARTZ_VALUES,
    TIPI_QUESTIONS,
)
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

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_FOUNDER_KIND = "founder"
"""Entity kind string used in the behavior graph."""


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
    """Run a full founder assessment, store results in the behavior graph.

    Parameters
    ----------
    mission:
        Founder's stated mission or purpose statement.
    tipi_responses:
        Mapping of TIPI-10 question IDs (e.g. ``"tipi_01"``) to integer
        responses on the 1-7 Likert scale.
    values:
        List of selected Schwartz value IDs (e.g. ``"self_direction"``).
    fears:
        List of dicts, each with keys ``trigger``, ``predicted_behavior``,
        ``mitigation``.
    risk_ratings:
        Mapping of risk dimension to integer rating (1-10).
    bias_responses:
        Mapping of bias question IDs to boolean (True = bias present).
    uid:
        Unique identifier for this founder.  Auto-generated if omitted.
    particle_id:
        Optional ZenOS particle identifier for identity linkage.
    db_path:
        Path to the behaviour graph SQLite database.  Defaults to the
        standard ``.mekong/graph.db`` under the CWD.

    Returns
    -------
    FounderGenome
        The fully populated assessment profile.
    """
    # 1. Score everything
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

    # 2. Persist to behaviour graph
    _store_genome(genome, uid or str(uuid.uuid4()), db_path)

    return genome


def review_founder(
    entity_id: str,
    db_path: str | None = None,
) -> dict[str, Any] | None:
    """Load a founder genome from the behaviour graph by entity ID.

    Parameters
    ----------
    entity_id:
        The graph entity ID of the founder (e.g. a UUID).
    db_path:
        Path to the graph database.

    Returns
    -------
    dict or None
        Entity dict with keys ``id``, ``name``, ``kind``, ``metadata``
        (the genome), ``created_at``, or ``None`` if not found.
    """
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
    """Return all founder entities from the behaviour graph.

    Parameters
    ----------
    db_path:
        Path to the graph database.

    Returns
    -------
    list[dict]
        Each dict has keys ``id``, ``name``, ``kind``, ``metadata``
        (the genome), ``created_at``.
    """
    conn = open_db(db_path)
    try:
        return query_entities_by_kind(conn, _FOUNDER_KIND)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _store_genome(
    genome: FounderGenome,
    uid: str,
    db_path: str | None = None,
) -> None:
    """Persist a founder genome into the behaviour graph.

    1. Store the founder as an entity with ``kind="founder"``.
    2. Record a founder_assessment behaviour edge.
    """
    conn = open_db(db_path)
    try:
        # Store the founder entity with genome as metadata
        ensure_entity(
            conn,
            entity_id=uid,
            name=genome.mission[:100] if genome.mission else f"Founder {uid[:8]}",
            kind=_FOUNDER_KIND,
            metadata=genome_to_dict(genome),
        )

        # Determine behaviour-edge IDs
        source_id = f"founder:{uid}"
        # Ensure the source edge entity exists (distinct kind to avoid polluting founder listings)
        ensure_entity(conn, entity_id=source_id, name=source_id, kind="founder_assessment")

        if genome.particle_id:
            target_id = f"particle:{genome.particle_id}"
            ensure_entity(conn, entity_id=target_id, name=target_id, kind="particle")
        else:
            target_id = f"founder:{uid}"

        # Record the assessment behaviour
        record_behavior(
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


def genome_to_dict(genome: FounderGenome) -> dict[str, Any]:
    """Serialise a ``FounderGenome`` to a plain dict for JSON storage.

    Parameters
    ----------
    genome:
        The genome instance to serialise.

    Returns
    -------
    dict
        Flat dict representation of the genome.
    """
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

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data classes for the ZenOS behavior graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    """A registered actor (particle or external) in the behavior graph.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable label.
        kind: Entity type — ``"particle"``, ``"agent"``, ``"external"``.
        metadata: Arbitrary JSON-serialisable metadata.
        created_at: ISO-8601 UTC timestamp.
    """

    id: str
    name: str
    kind: str = "particle"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class Behavior:
    """A directed, typed edge between two entities.

    Attributes:
        id: Auto-incremented primary key.
        source_id: Actor that performed the action.
        target_id: Actor that received the action.
        action: Verb describing the interaction (e.g. ``"trade"``, ``"refer"``).
        payload: Arbitrary JSON-serialisable payload.
        value: Numeric scalar attached to the behavior (e.g. transaction amount).
        timestamp: ISO-8601 UTC timestamp.
    """

    id: int = 0
    source_id: str = ""
    target_id: str = ""
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    value: float = 0.0
    timestamp: str = ""


@dataclass
class TrustScore:
    """Computed trust value between two entities.

    All numeric scores are integers in the range 0-100.

    Attributes:
        source_id: Trusting entity.
        target_id: Trusted entity.
        score: Composite trust score (0-100).
        confidence: Confidence in the score (0-100).
        behavior_count: Number of behaviors observed between the pair.
        updated_at: ISO-8601 UTC timestamp.
    """

    source_id: str = ""
    target_id: str = ""
    score: int = 0
    confidence: int = 0
    behavior_count: int = 0
    updated_at: str = ""


@dataclass
class CollusionFlag:
    """A detected collusion pattern between two entities.

    Attributes:
        id: Auto-incremented primary key.
        pattern: Collusion pattern name (e.g. ``"price_parallelism"``).
        entity_a_id: First entity involved.
        entity_b_id: Second entity involved.
        evidence: JSON-serialisable evidence details.
        severity: ``"low"`` | ``"medium"`` | ``"high"`` | ``"critical"``.
        detected_at: ISO-8601 UTC timestamp.
        cleared_at: ISO-8601 UTC timestamp when cleared, or ``None``.
    """

    id: int = 0
    pattern: str = ""
    entity_a_id: str = ""
    entity_b_id: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"
    detected_at: str = ""
    cleared_at: str | None = None

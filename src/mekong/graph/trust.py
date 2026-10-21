# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Trust computation for the ZenOS behavior graph."""

from __future__ import annotations

import sqlite3

from src.mekong.graph.store import get_behavior_count, upsert_trust_score
from src.mekong.graph.trust_factors import (
    _clamp,
    _compute_collusion_penalty,
    _compute_diversity,
    _compute_network_factor,
    _compute_reciprocity,
    _compute_reputation,
    _compute_volatility,
)

ALPHA = 25    # network_factor
BETA = 20     # reciprocity
GAMMA = 15    # diversity
DELTA = 25    # reputation
EPSILON = 10  # volatility
ZETA = 5      # collusion_penalty

COLD_START_THRESHOLD = 10
COLD_START_SCORE = 50


def compute_trust(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
) -> tuple[int, int]:
    """Compute the trust score and confidence from *source_id* to *target_id*."""
    behavior_count = get_behavior_count(conn, source_id, target_id)

    if behavior_count < COLD_START_THRESHOLD:
        confidence = min(100, behavior_count * 10)
        score = _clamp(COLD_START_SCORE)
        _persist(conn, source_id, target_id, score, confidence, behavior_count)
        return score, confidence

    network_factor = _compute_network_factor(conn, source_id, target_id, behavior_count)
    reciprocity = _compute_reciprocity(conn, source_id, target_id)
    diversity = _compute_diversity(conn, source_id, target_id)
    reputation = _compute_reputation(conn, source_id, behavior_count)
    volatility = _compute_volatility(conn, source_id, target_id)
    collusion_penalty = _compute_collusion_penalty(conn, source_id, target_id)

    raw = (
        ALPHA * network_factor / 100.0
        + BETA * reciprocity / 100.0
        + GAMMA * diversity / 100.0
        + DELTA * reputation / 100.0
        - EPSILON * volatility / 100.0
        - ZETA * collusion_penalty / 100.0
    )

    score = _clamp(round(raw))
    confidence = min(100, behavior_count)

    _persist(
        conn,
        source_id,
        target_id,
        score,
        confidence,
        behavior_count,
        raw_alpha=network_factor,
        raw_beta=reciprocity,
        raw_gamma=diversity,
        raw_delta=reputation,
        raw_epsilon=volatility,
        raw_zeta=collusion_penalty,
    )
    return score, confidence


def _persist(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    score: int,
    confidence: int,
    behavior_count: int,
    raw_alpha: float = 0.0,
    raw_beta: float = 0.0,
    raw_gamma: float = 0.0,
    raw_delta: float = 0.0,
    raw_epsilon: float = 0.0,
    raw_zeta: float = 0.0,
) -> None:
    upsert_trust_score(
        conn,
        source_id=source_id,
        target_id=target_id,
        score=score,
        confidence=confidence,
        raw_alpha=raw_alpha,
        raw_beta=raw_beta,
        raw_gamma=raw_gamma,
        raw_delta=raw_delta,
        raw_epsilon=raw_epsilon,
        raw_zeta=raw_zeta,
        behavior_count=behavior_count,
    )


__all__ = [
    "ALPHA",
    "BETA",
    "COLD_START_SCORE",
    "COLD_START_THRESHOLD",
    "DELTA",
    "EPSILON",
    "GAMMA",
    "ZETA",
    "_clamp",
    "_compute_collusion_penalty",
    "_compute_diversity",
    "_compute_network_factor",
    "_compute_reciprocity",
    "_compute_reputation",
    "_compute_volatility",
    "_persist",
    "compute_trust",
]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Trust computation for the ZenOS behavior graph.

Formula
-------
    score = alpha * network_factor
          + beta  * reciprocity
          + gamma * diversity
          + delta * reputation
          - epsilon * volatility
          - zeta   * collusion_flag

All component weights are on a 0-100 scale.

Cold start
----------
If ``behavior_count < 10``, returns 50 (neutral) with ``confidence = count * 10``.
"""

from __future__ import annotations

import sqlite3

from src.mekong.graph.store import get_behavior_count, upsert_trust_score

# ---------------------------------------------------------------------------
# Weights (0-100 scale, sum <= 100 for normalised output)
# ---------------------------------------------------------------------------

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
    """Compute the trust score and confidence from *source_id* to *target_id*.

    Returns ``(score, confidence)``, both integers in the 0-100 range.
    Persists the result to the ``trust_scores`` table.
    """
    behavior_count = get_behavior_count(conn, source_id, target_id)

    # --- Cold start --------------------------------------------------------
    if behavior_count < COLD_START_THRESHOLD:
        confidence = min(100, behavior_count * 10)
        score = _clamp(COLD_START_SCORE)
        _persist(conn, source_id, target_id, score, confidence, behavior_count)
        return score, confidence

    # --- Component computations --------------------------------------------
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


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------


def _compute_network_factor(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    behavior_count: int,
) -> float:
    """How many interactions relative to the source's total activity."""
    total = conn.execute(
        "SELECT COUNT(*) AS c FROM behaviors WHERE source_id = ?",
        (source_id,),
    ).fetchone()["c"]
    if total == 0:
        return 50.0
    return min(100.0, (behavior_count / total) * 100.0)


def _compute_reciprocity(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
) -> float:
    """Does the target also interact back toward the source?"""
    reverse_count = conn.execute(
        "SELECT COUNT(*) AS c FROM behaviors WHERE source_id = ? AND target_id = ?",
        (target_id, source_id),
    ).fetchone()["c"]
    if reverse_count == 0:
        return 0.0
    return min(100.0, reverse_count * 10.0)


def _compute_diversity(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
) -> float:
    """How many distinct action types exist between the pair."""
    row = conn.execute(
        "SELECT COUNT(DISTINCT action) AS c FROM behaviors WHERE source_id = ? AND target_id = ?",
        (source_id, target_id),
    ).fetchone()
    distinct_actions = row["c"]
    return min(100.0, distinct_actions * 20.0)


def _compute_reputation(
    conn: sqlite3.Connection,
    source_id: str,
    behavior_count: int,
) -> float:
    """Normalised reputation from the source's total outgoing interaction count."""
    return min(100.0, behavior_count * 2.0)


def _compute_volatility(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
) -> float:
    """Value variance across behaviors — high variance reduces trust."""
    rows = conn.execute(
        "SELECT value FROM behaviors WHERE source_id = ? AND target_id = ? ORDER BY timestamp",
        (source_id, target_id),
    ).fetchall()
    values = [r["value"] for r in rows]
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return min(100.0, variance / 10.0)


def _compute_collusion_penalty(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
) -> float:
    """Penalty based on active collusion flags between the pair."""
    count = conn.execute(
        """SELECT COUNT(*) AS c FROM collusion_flags
           WHERE ((entity_a_id = ? AND entity_b_id = ?) OR (entity_a_id = ? AND entity_b_id = ?))
             AND cleared_at IS NULL""",
        (source_id, target_id, target_id, source_id),
    ).fetchone()["c"]
    return min(100.0, count * 25.0)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _clamp(value: int) -> int:
    return max(0, min(100, value))


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

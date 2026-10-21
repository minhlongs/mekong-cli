# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Component factor calculations for ZenOS behavior graph trust scores."""

from __future__ import annotations

import sqlite3


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


def _clamp(value: int) -> int:
    return max(0, min(100, value))

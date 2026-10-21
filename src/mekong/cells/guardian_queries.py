# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Guardian Cell data models, thresholds, and SQLite query helpers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class Alert:
    """A single observation flagged by the Guardian during review."""

    severity: str = "INFO"
    source: str = ""
    message: str = ""


@dataclass
class HealthReport:
    """Complete health snapshot for a particle over the review window."""

    status: str = "GREEN"
    total_behaviors: int = 0
    violations: int = 0
    collusion_flags: int = 0
    trust_trend: str = "stable"
    alerts: list[Alert] = field(default_factory=list)


DEFAULT_THRESHOLDS: dict[str, float] = {
    "violation_rate_warning": 0.1,
    "violation_rate_critical": 0.25,
    "collusion_flags_warning": 1,
    "trust_delta_warning": -10,
    "mission_drift_warning": 0.3,
}


def load_guardian_thresholds(particle_id: str) -> dict[str, float]:
    """Load guardian health thresholds for *particle_id*."""
    return dict(DEFAULT_THRESHOLDS)


def _iso_now() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%fZ")


def _hours_ago_iso(hours_back: int) -> str:
    """Return ISO-8601 timestamp *hours_back* hours before now."""
    return (datetime.now(timezone.utc) - timedelta(hours=hours_back)).strftime(
        "%Y-%m-%dT%H:%M:%fZ"
    )


def _query_behavior_stats(
    conn: sqlite3.Connection,
    particle_id: str,
    since_ts: str,
) -> tuple[int, int]:
    """Query total behaviors and violations for *particle_id* since *since_ts*."""
    total = conn.execute(
        """SELECT COUNT(*) AS c FROM behaviors
           WHERE (source_id = ? OR target_id = ?)
             AND timestamp >= ?""",
        (particle_id, particle_id, since_ts),
    ).fetchone()["c"]

    violations = conn.execute(
        """SELECT COUNT(*) AS c FROM behaviors
           WHERE (source_id = ? OR target_id = ?)
             AND timestamp >= ?
             AND constitutional_review = 'failed'""",
        (particle_id, particle_id, since_ts),
    ).fetchone()["c"]

    return total, violations


def _query_collusion_flags(
    conn: sqlite3.Connection,
    particle_id: str,
) -> int:
    """Count active (uncleared) collusion flags involving *particle_id* cells."""
    row = conn.execute(
        """SELECT COUNT(*) AS c FROM collusion_flags
           WHERE (entity_a_id = ? OR entity_b_id = ?)
             AND cleared_at IS NULL""",
        (particle_id, particle_id),
    ).fetchone()
    return row["c"]


def _query_trust_trend(
    conn: sqlite3.Connection,
    particle_id: str,
) -> str:
    """Determine trust trend by comparing the oldest vs newest trust score."""
    rows = conn.execute(
        """SELECT score, updated_at FROM trust_scores
           WHERE source_id = ? OR target_id = ?
           ORDER BY updated_at ASC""",
        (particle_id, particle_id),
    ).fetchall()

    if len(rows) < 2:
        return "stable"

    delta = rows[-1]["score"] - rows[0]["score"]
    if delta >= 5:
        return "improving"
    if delta <= -5:
        return "declining"
    return "stable"


def _query_trust_delta(
    conn: sqlite3.Connection,
    particle_id: str,
) -> int:
    """Return raw delta (last - first) of trust scores for *particle_id*."""
    rows = conn.execute(
        """SELECT score, updated_at FROM trust_scores
           WHERE source_id = ? OR target_id = ?
           ORDER BY updated_at ASC""",
        (particle_id, particle_id),
    ).fetchall()

    if len(rows) < 2:
        return 0
    return rows[-1]["score"] - rows[0]["score"]

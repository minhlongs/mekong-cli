"""Guardian Cell engine — system health monitoring and anomaly detection.

The Guardian is a **read-only** AI Cell that monitors particle cell clusters
for constitutional violations, collusion activity, trust erosion, and mission
drift. It produces ``HealthReport`` instances with actionable alerts.

The Guardian never writes to the graph database. It only queries.

Usage
-----
>>> from src.mekong.cells.guardian import run_guardian_review
>>> report = run_guardian_review("particle:alpha")
>>> report.status
'GREEN'
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.mekong.graph.store import open_db

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Alert:
    """A single observation flagged by the Guardian during review.

    Attributes:
        severity: ``"INFO"`` | ``"WARNING"`` | ``"CRITICAL"``
        source:  Origin of the alert (e.g. ``"violation_rate"``,
                 ``"collusion_count"``, ``"trust_trend"``).
        message: Human-readable description of the finding.
    """

    severity: str = "INFO"
    source: str = ""
    message: str = ""


@dataclass
class HealthReport:
    """Complete health snapshot for a particle over the review window.

    Attributes:
        status:           ``"GREEN"`` | ``"YELLOW"`` | ``"RED"``
        total_behaviors:  Number of behavior edges observed in the window.
        violations:       Count of behaviors where
                          ``constitutional_review = 'failed'``.
        collusion_flags:  Number of active (uncleared) collusion flags
                          involving the particle's cells.
        trust_trend:      ``"stable"`` | ``"declining"`` | ``"improving"``
        alerts:           List of :class:`Alert` instances raised during
                          the review.
    """

    status: str = "GREEN"
    total_behaviors: int = 0
    violations: int = 0
    collusion_flags: int = 0
    trust_trend: str = "stable"
    alerts: list[Alert] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS: dict[str, float] = {
    "violation_rate_warning": 0.1,
    "violation_rate_critical": 0.25,
    "collusion_flags_warning": 1,
    "trust_delta_warning": -10,
    "mission_drift_warning": 0.3,
}

# ---------------------------------------------------------------------------
# Threshold loader
# ---------------------------------------------------------------------------


def load_guardian_thresholds(particle_id: str) -> dict[str, float]:
    """Load guardian health thresholds for *particle_id*.

    Returns a copy of the default thresholds. Particle-specific threshold
    overrides are reserved for future use (e.g. loading from a config file
    stored alongside the particle's constitution).

    Parameters
    ----------
    particle_id:
        Particle identifier (e.g. ``"particle:alpha"``).

    Returns
    -------
    dict[str, float]
        Threshold configuration with the same keys as
        :data:`DEFAULT_THRESHOLDS`.

    Examples
    --------
    >>> from src.mekong.cells.guardian import load_guardian_thresholds
    >>> t = load_guardian_thresholds("particle:alpha")
    >>> t["violation_rate_warning"]
    0.1
    """
    return dict(DEFAULT_THRESHOLDS)


# ---------------------------------------------------------------------------
# Review engine
# ---------------------------------------------------------------------------


def _iso_now() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%fZ")


def _hours_ago_iso(hours_back: int) -> str:
    """Return ISO-8601 timestamp *hours_back* hours before now."""
    from datetime import timedelta

    return (datetime.now(timezone.utc) - timedelta(hours=hours_back)).strftime(
        "%Y-%m-%dT%H:%M:%fZ"
    )


def _query_behavior_stats(
    conn: sqlite3.Connection,
    particle_id: str,
    since_ts: str,
) -> tuple[int, int]:
    """Query total behaviors and violations for *particle_id* since *since_ts*.

    Returns ``(total, violations)``.  A violation is a behavior edge whose
    ``constitutional_review`` column equals ``'failed'`` and that either has
    *particle_id* as source or as target.
    """
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
    """Determine trust trend by comparing the oldest vs newest trust score.

    Scans all trust scores where *particle_id* is either source or target,
    orders by ``updated_at``, and returns:

    - ``"improving"`` if the most recent score is >= 5 points above the oldest.
    - ``"declining"`` if the most recent score is >= 5 points below the oldest.
    - ``"stable"`` otherwise.

    Returns ``"stable"`` when there are fewer than 2 distinct scores.
    """
    rows = conn.execute(
        """SELECT score, updated_at FROM trust_scores
           WHERE source_id = ? OR target_id = ?
           ORDER BY updated_at ASC""",
        (particle_id, particle_id),
    ).fetchall()

    if len(rows) < 2:
        return "stable"

    first_score = rows[0]["score"]
    last_score = rows[-1]["score"]
    delta = last_score - first_score

    if delta >= 5:
        return "improving"
    if delta <= -5:
        return "declining"
    return "stable"


def _query_trust_delta(
    conn: sqlite3.Connection,
    particle_id: str,
) -> int:
    """Return raw delta (last - first) of trust scores for *particle_id*.

    Returns 0 when fewer than 2 scores exist.
    """
    rows = conn.execute(
        """SELECT score, updated_at FROM trust_scores
           WHERE source_id = ? OR target_id = ?
           ORDER BY updated_at ASC""",
        (particle_id, particle_id),
    ).fetchall()

    if len(rows) < 2:
        return 0
    return rows[-1]["score"] - rows[0]["score"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_guardian_review(
    particle_id: str,
    thresholds: dict[str, float] | None = None,
    graph_db: str | None = None,
    hours_back: int = 168,
) -> HealthReport:
    """Run a full Guardian health review for *particle_id*.

    Steps
    -----
    1. Query the behavior graph for all edges involving *particle_id* within
       the last *hours_back* hours.
    2. Compute the violation rate = failed constitutional reviews / total.
    3. Query active collusion flags that involve the particle's cells.
    4. Query trust scores and compare oldest vs newest to determine trend.
    5. Compare every computed value against the configured thresholds.
    6. Build a list of :class:`Alert` instances for any threshold breach.
    7. Determine final status:
       - ``"RED"`` if any alert has severity ``"CRITICAL"``.
       - ``"YELLOW"`` if any alert has severity ``"WARNING"``.
       - ``"GREEN"`` otherwise.
    8. Return a :class:`HealthReport`.

    Parameters
    ----------
    particle_id:
        Identifier for the particle to review (e.g. ``"particle:alpha"``).
    thresholds:
        Optional overrides for the default thresholds. Keys are threshold names
        as defined in :data:`DEFAULT_THRESHOLDS`; values are the corresponding
        numeric limits.  Unspecified keys fall back to the defaults.
    graph_db:
        Optional path to the behavior graph SQLite database. Uses the
        environment default when ``None``.
    hours_back:
        How many hours of history to include (default 168 = 7 days).

    Returns
    -------
    HealthReport
        Complete health snapshot with status, metrics, and alerts.

    Examples
    --------
    >>> from src.mekong.cells.guardian import run_guardian_review
    >>> report = run_guardian_review("particle:alpha")
    >>> report.status
    'GREEN'
    """
    effective_thresholds = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        effective_thresholds.update(thresholds)

    since_ts = _hours_ago_iso(hours_back)

    conn = open_db(graph_db)
    try:
        # Step 1-2: Behavior stats
        total_behaviors, violations = _query_behavior_stats(conn, particle_id, since_ts)

        # Step 3: Collusion flags
        collusion_flags = _query_collusion_flags(conn, particle_id)

        # Step 4: Trust trend
        trust_trend = _query_trust_trend(conn, particle_id)

        # Step 5-6: Compare against thresholds, build alerts
        alerts: list[Alert] = []

        violation_rate = 0.0
        if total_behaviors > 0:
            violation_rate = violations / total_behaviors

        # Violation rate checks
        v_crit = effective_thresholds.get("violation_rate_critical", 0.25)
        v_warn = effective_thresholds.get("violation_rate_warning", 0.1)

        if violation_rate >= v_crit:
            alerts.append(
                Alert(
                    severity="CRITICAL",
                    source="violation_rate",
                    message=(
                        f"Violation rate {violation_rate:.1%} exceeds critical "
                        f"threshold {v_crit:.0%} ({violations} failed / {total_behaviors} total)"
                    ),
                )
            )
        elif violation_rate >= v_warn:
            alerts.append(
                Alert(
                    severity="WARNING",
                    source="violation_rate",
                    message=(
                        f"Violation rate {violation_rate:.1%} exceeds warning "
                        f"threshold {v_warn:.0%} ({violations} failed / {total_behaviors} total)"
                    ),
                )
            )

        # Collusion flag check
        collusion_warn = int(effective_thresholds.get("collusion_flags_warning", 1))
        if collusion_flags > collusion_warn:
            alerts.append(
                Alert(
                    severity="WARNING",
                    source="collusion_flags",
                    message=(
                        f"Active collusion flags ({collusion_flags}) exceed "
                        f"warning threshold ({collusion_warn})"
                    ),
                )
            )
        elif collusion_flags > 0:
            # Exactly at the warning boundary — still worth an INFO alert
            alerts.append(
                Alert(
                    severity="INFO",
                    source="collusion_flags",
                    message=(
                        f"Active collusion flags ({collusion_flags}) at or "
                        f"near warning threshold ({collusion_warn})"
                    ),
                )
            )

        # Trust delta check
        trust_delta = _query_trust_delta(conn, particle_id)
        trust_delta_warn = effective_thresholds.get("trust_delta_warning", -10)

        if trust_delta <= trust_delta_warn:
            alerts.append(
                Alert(
                    severity="WARNING",
                    source="trust_trend",
                    message=(
                        f"Trust score delta ({trust_delta}) meets or exceeds "
                        f"warning threshold ({trust_delta_warn}) — trend is {trust_trend}"
                    ),
                )
            )

        # Mission drift check (check for behaviors with action containing "drift")
        mission_drift_count = conn.execute(
            """SELECT COUNT(*) AS c FROM behaviors
               WHERE (source_id = ? OR target_id = ?)
                 AND timestamp >= ?
                 AND action LIKE '%drift%'""",
            (particle_id, particle_id, since_ts),
        ).fetchone()["c"]

        drift_warn = effective_thresholds.get("mission_drift_warning", 0.3)
        if total_behaviors > 0 and (mission_drift_count / total_behaviors) >= drift_warn:
            alerts.append(
                Alert(
                    severity="WARNING",
                    source="mission_drift",
                    message=(
                        f"Mission drift behaviors ({mission_drift_count}/{total_behaviors}) "
                        f"exceed warning threshold ({drift_warn:.0%})"
                    ),
                )
            )
        elif mission_drift_count > 0:
            alerts.append(
                Alert(
                    severity="INFO",
                    source="mission_drift",
                    message=f"Mission drift behaviors detected ({mission_drift_count})",
                )
            )

        # Step 7: Determine overall status
        any_critical = any(a.severity == "CRITICAL" for a in alerts)
        any_warning = any(a.severity == "WARNING" for a in alerts)

        if any_critical:
            status = "RED"
        elif any_warning:
            status = "YELLOW"
        else:
            status = "GREEN"

    finally:
        conn.close()

    # Step 8: Return HealthReport
    return HealthReport(
        status=status,
        total_behaviors=total_behaviors,
        violations=violations,
        collusion_flags=collusion_flags,
        trust_trend=trust_trend,
        alerts=alerts,
    )

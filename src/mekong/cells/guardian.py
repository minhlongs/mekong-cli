# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Guardian Cell engine — system health monitoring and anomaly detection."""

from __future__ import annotations

import sqlite3

from src.mekong.cells.guardian_queries import (
    DEFAULT_THRESHOLDS,
    Alert,
    HealthReport,
    _hours_ago_iso,
    _iso_now,
    _query_behavior_stats,
    _query_collusion_flags,
    _query_trust_delta,
    _query_trust_trend,
    load_guardian_thresholds,
)
from src.mekong.graph.store import open_db


def run_guardian_review(
    particle_id: str,
    thresholds: dict[str, float] | None = None,
    graph_db: str | None = None,
    hours_back: int = 168,
) -> HealthReport:
    """Run a full Guardian health review for *particle_id*."""
    effective_thresholds = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        effective_thresholds.update(thresholds)

    since_ts = _hours_ago_iso(hours_back)

    conn = open_db(graph_db)
    try:
        total_behaviors, violations = _query_behavior_stats(conn, particle_id, since_ts)
        collusion_flags = _query_collusion_flags(conn, particle_id)
        trust_trend = _query_trust_trend(conn, particle_id)

        alerts: list[Alert] = []

        violation_rate = 0.0
        if total_behaviors > 0:
            violation_rate = violations / total_behaviors

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

    return HealthReport(
        status=status,
        total_behaviors=total_behaviors,
        violations=violations,
        collusion_flags=collusion_flags,
        trust_trend=trust_trend,
        alerts=alerts,
    )


__all__ = [
    "Alert",
    "DEFAULT_THRESHOLDS",
    "HealthReport",
    "_hours_ago_iso",
    "_iso_now",
    "_query_behavior_stats",
    "_query_collusion_flags",
    "_query_trust_delta",
    "_query_trust_trend",
    "load_guardian_thresholds",
    "run_guardian_review",
    "sqlite3",
]

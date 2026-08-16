# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Collusion detection algorithms for the ZenOS behavior graph.

Each detector runs within a transaction to ensure isolation.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from src.mekong.graph.store import insert_collusion_flag
from src.mekong.graph.types import CollusionFlag

# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


def detect_price_parallelism(
    conn: sqlite3.Connection,
    min_occurrences: int = 3,
    window_hours: int = 24,
    action: str | None = None,
) -> list[CollusionFlag]:
    """Detect entities setting identical prices within a time window.

    Queries all behaviors of the given *action* (default ``"set_price"``)
    and groups by ``(source_id, value)`` within a *window_hours* sliding window.
    If 3+ occurrences share the same value within the window, a flag is raised.

    All queries are wrapped in a transaction for isolation.
    """
    action = action or "set_price"
    flags: list[CollusionFlag] = []

    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(
            """SELECT source_id, target_id, value, timestamp
               FROM behaviors
               WHERE action = ?
               ORDER BY source_id, value, timestamp""",
            (action,),
        ).fetchall()

        # Group by value and check for multiple distinct source_ids
        # Query already filtered by action, so group key is just value
        groups: dict[float, list[dict[str, Any]]] = {}
        for r in rows:
            key = r["value"]
            groups.setdefault(key, []).append(r)

        for value, entries in groups.items():
            distinct_sources = set(e["source_id"] for e in entries)
            if len(distinct_sources) < 2:
                continue  # Collusion requires at least 2 distinct entities
            if len(entries) < min_occurrences:
                continue
            # Check that all occurrences fall within the time window
            sorted_entries = sorted(entries, key=lambda e: e["timestamp"])
            ts_first = sorted_entries[0]["timestamp"]
            ts_last = sorted_entries[-1]["timestamp"]
            if _hours_between(ts_last, ts_first) <= window_hours:
                sources = list(distinct_sources)
                for i in range(len(sources)):
                    for j in range(i + 1, len(sources)):
                        flag_id = insert_collusion_flag(
                            conn,
                            pattern="price_parallelism",
                            entity_a_id=sources[i],
                            entity_b_id=sources[j],
                            evidence={
                                "value": value,
                                "action": action,
                                "occurrences": len(entries),
                                "window_hours": _hours_between(ts_last, ts_first),
                            },
                            severity="medium",
                        )
                        flags.append(
                            CollusionFlag(
                                id=flag_id,
                                pattern="price_parallelism",
                                entity_a_id=sources[i],
                                entity_b_id=sources[j],
                                evidence={
                                    "value": value,
                                    "occurrences": len(entries),
                                },
                                severity="medium",
                            )
                        )
        conn.commit()
    except BaseException:
        conn.rollback()
        raise

    return flags


def detect_deal_rotation(
    conn: sqlite3.Connection,
    min_transactions: int = 5,
    action: str | None = None,
) -> list[CollusionFlag]:
    """Detect alternating win patterns — a signal of bid rotation.

    Looks for a cycle where entity A wins, then B wins, then A wins again
    across consecutive ``"bid_win"`` actions (or custom *action*).
    Requires at least *min_transactions* entries to flag.
    """
    action = action or "bid_win"
    flags: list[CollusionFlag] = []

    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(
            """SELECT id, source_id, target_id, timestamp
               FROM behaviors
               WHERE action = ?
               ORDER BY timestamp ASC""",
            (action,),
        ).fetchall()

        if len(rows) < min_transactions:
            conn.commit()
            return flags

        # Check each pair of entities for alternating wins
        entities_seen: set[str] = set()
        for r in rows:
            entities_seen.add(r["source_id"])
            entities_seen.add(r["target_id"])

        entity_list = list(entities_seen)
        for i in range(len(entity_list)):
            for j in range(i + 1, len(entity_list)):
                a, b = entity_list[i], entity_list[j]
                seq: list[str] = []
                for r in rows:
                    if r["source_id"] in (a, b):
                        seq.append(r["source_id"])

                if len(seq) >= min_transactions:
                    alternating = True
                    for k in range(1, len(seq)):
                        if seq[k] == seq[k - 1]:
                            alternating = False
                            break
                    if alternating:
                        flag_id = insert_collusion_flag(
                            conn,
                            pattern="deal_rotation",
                            entity_a_id=a,
                            entity_b_id=b,
                            evidence={
                                "sequence": seq,
                                "length": len(seq),
                            },
                            severity="high",
                        )
                        flags.append(
                            CollusionFlag(
                                id=flag_id,
                                pattern="deal_rotation",
                                entity_a_id=a,
                                entity_b_id=b,
                                evidence={
                                    "sequence": seq,
                                    "length": len(seq),
                                },
                                severity="high",
                            )
                        )
        conn.commit()
    except BaseException:
        conn.rollback()
        raise

    return flags


def detect_market_allocation(
    conn: sqlite3.Connection,
    action: str | None = None,
) -> list[CollusionFlag]:
    """Detect market allocation — zero cross-over in counterparty sets.

    Two entities are flagged if they have non-overlapping sets of counterparties
    for the given *action* (default ``"trade"``), suggesting a tacit agreement
    to avoid each other's turf.
    """
    action = action or "trade"
    flags: list[CollusionFlag] = []

    conn.execute("BEGIN IMMEDIATE")
    try:
        # Get all entities that perform this action
        entity_rows = conn.execute(
            "SELECT DISTINCT source_id FROM behaviors WHERE action = ?",
            (action,),
        ).fetchall()
        entity_ids = [r["source_id"] for r in entity_rows]

        for i in range(len(entity_ids)):
            for j in range(i + 1, len(entity_ids)):
                a, b = entity_ids[i], entity_ids[j]

                a_targets = set(
                    r["target_id"]
                    for r in conn.execute(
                        "SELECT DISTINCT target_id FROM behaviors WHERE source_id = ? AND action = ?",
                        (a, action),
                    ).fetchall()
                )
                b_targets = set(
                    r["target_id"]
                    for r in conn.execute(
                        "SELECT DISTINCT target_id FROM behaviors WHERE source_id = ? AND action = ?",
                        (b, action),
                    ).fetchall()
                )

                # Skip if either has no counterparties
                if not a_targets or not b_targets:
                    continue

                intersection = a_targets & b_targets
                if len(intersection) == 0:
                    flag_id = insert_collusion_flag(
                        conn,
                        pattern="market_allocation",
                        entity_a_id=a,
                        entity_b_id=b,
                        evidence={
                            "entity_a_targets": list(a_targets),
                            "entity_b_targets": list(b_targets),
                        },
                        severity="high",
                    )
                    flags.append(
                        CollusionFlag(
                            id=flag_id,
                            pattern="market_allocation",
                            entity_a_id=a,
                            entity_b_id=b,
                            evidence={
                                "entity_a_targets": list(a_targets),
                                "entity_b_targets": list(b_targets),
                            },
                            severity="high",
                        )
                    )
        conn.commit()
    except BaseException:
        conn.rollback()
        raise

    return flags


# ---------------------------------------------------------------------------
# Aggregate runner
# ---------------------------------------------------------------------------


def run_all_detectors(
    conn: sqlite3.Connection,
) -> dict[str, list[CollusionFlag]]:
    """Run all collusion detectors and return results grouped by pattern."""
    return {
        "price_parallelism": detect_price_parallelism(conn),
        "deal_rotation": detect_deal_rotation(conn),
        "market_allocation": detect_market_allocation(conn),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hours_between(later: str, earlier: str) -> float:
    """Approximate hours between two ISO-8601 timestamps (no external deps)."""
    from datetime import datetime, timezone

    fmt = "%Y-%m-%dT%H:%M:%S"
    # Handle fractional seconds
    ts1 = later[:19] if len(later) >= 19 else later
    ts2 = earlier[:19] if len(earlier) >= 19 else earlier
    try:
        dt1 = datetime.strptime(ts1, fmt).replace(tzinfo=timezone.utc)
        dt2 = datetime.strptime(ts2, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        return 0.0
    return abs((dt1 - dt2).total_seconds()) / 3600.0

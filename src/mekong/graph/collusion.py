# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Collusion detection algorithms for the ZenOS behavior graph."""

from __future__ import annotations

import sqlite3
from typing import Any

from src.mekong.graph.collusion_detectors import (
    _hours_between,
    detect_deal_rotation,
    detect_market_allocation,
)
from src.mekong.graph.store import insert_collusion_flag
from src.mekong.graph.types import CollusionFlag


def detect_price_parallelism(
    conn: sqlite3.Connection,
    min_occurrences: int = 3,
    window_hours: int = 24,
    action: str | None = None,
) -> list[CollusionFlag]:
    """Detect entities setting identical prices within a time window."""
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

        groups: dict[float, list[dict[str, Any]]] = {}
        for r in rows:
            groups.setdefault(r["value"], []).append(r)

        for value, entries in groups.items():
            distinct_sources = set(e["source_id"] for e in entries)
            if len(distinct_sources) < 2 or len(entries) < min_occurrences:
                continue
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


def run_all_detectors(
    conn: sqlite3.Connection,
) -> dict[str, list[CollusionFlag]]:
    """Run all collusion detectors and return results grouped by pattern."""
    return {
        "price_parallelism": detect_price_parallelism(conn),
        "deal_rotation": detect_deal_rotation(conn),
        "market_allocation": detect_market_allocation(conn),
    }


__all__ = [
    "CollusionFlag",
    "_hours_between",
    "detect_deal_rotation",
    "detect_market_allocation",
    "detect_price_parallelism",
    "insert_collusion_flag",
    "run_all_detectors",
]

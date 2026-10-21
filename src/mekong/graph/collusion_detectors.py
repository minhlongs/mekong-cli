# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Secondary collusion detectors and timestamp helpers for the behavior graph."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from src.mekong.graph.types import CollusionFlag


def _hours_between(later: str, earlier: str) -> float:
    """Approximate hours between two ISO-8601 timestamps (no external deps)."""
    fmt = "%Y-%m-%dT%H:%M:%S"
    ts1 = later[:19] if len(later) >= 19 else later
    ts2 = earlier[:19] if len(earlier) >= 19 else earlier
    try:
        dt1 = datetime.strptime(ts1, fmt).replace(tzinfo=timezone.utc)
        dt2 = datetime.strptime(ts2, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        return 0.0
    return abs((dt1 - dt2).total_seconds()) / 3600.0


def detect_deal_rotation(
    conn: sqlite3.Connection,
    min_transactions: int = 5,
    action: str | None = None,
) -> list[CollusionFlag]:
    """Detect alternating win patterns — a signal of bid rotation."""
    import src.mekong.graph.collusion as _col

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

        entities_seen: set[str] = set()
        for r in rows:
            entities_seen.add(r["source_id"])
            entities_seen.add(r["target_id"])

        entity_list = list(entities_seen)
        for i in range(len(entity_list)):
            for j in range(i + 1, len(entity_list)):
                a, b = entity_list[i], entity_list[j]
                seq: list[str] = [r["source_id"] for r in rows if r["source_id"] in (a, b)]

                if len(seq) >= min_transactions:
                    alternating = all(seq[k] != seq[k - 1] for k in range(1, len(seq)))
                    if alternating:
                        flag_id = _col.insert_collusion_flag(
                            conn,
                            pattern="deal_rotation",
                            entity_a_id=a,
                            entity_b_id=b,
                            evidence={"sequence": seq, "length": len(seq)},
                            severity="high",
                        )
                        flags.append(
                            CollusionFlag(
                                id=flag_id,
                                pattern="deal_rotation",
                                entity_a_id=a,
                                entity_b_id=b,
                                evidence={"sequence": seq, "length": len(seq)},
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
    """Detect market allocation — zero cross-over in counterparty sets."""
    import src.mekong.graph.collusion as _col

    action = action or "trade"
    flags: list[CollusionFlag] = []

    conn.execute("BEGIN IMMEDIATE")
    try:
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

                if not a_targets or not b_targets:
                    continue

                if len(a_targets & b_targets) == 0:
                    flag_id = _col.insert_collusion_flag(
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

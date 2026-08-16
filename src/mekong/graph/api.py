# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Public API for the ZenOS behavior graph module.

Thin wrappers that open a connection, perform the operation, and return
JSON-serialisable results.
"""

from __future__ import annotations

from typing import Any

from src.mekong.graph.collusion import (
    detect_deal_rotation,
    detect_market_allocation,
    detect_price_parallelism,
)
from src.mekong.graph.store import (
    ensure_entity,
    find_collusion,
    get_status as _get_store_status,
    get_trust_score,
    open_db,
    record_behavior as _record_behavior,
)
from src.mekong.graph.trust import compute_trust


def record_behavior(
    source_id: str,
    source_name: str,
    target_id: str,
    target_name: str,
    action: str,
    payload: dict[str, Any] | None = None,
    value: float = 0.0,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Record a behavior and return the behavior ID."""
    conn = open_db(db_path)
    try:
        ensure_entity(conn, source_id, source_name)
        ensure_entity(conn, target_id, target_name)
        behavior_id = _record_behavior(
            conn, source_id, target_id, action, payload, value
        )
        return {"behavior_id": behavior_id, "status": "recorded"}
    finally:
        conn.close()


def get_trust(
    source_id: str,
    target_id: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Compute (or retrieve cached) trust score between two entities.

    Returns dict with ``score``, ``confidence``, ``behavior_count``, and
    ``cold_start`` flag.
    """
    conn = open_db(db_path)
    try:
        # Ensure entities exist (needed for foreign key on trust_scores)
        ensure_entity(conn, source_id, source_id)
        ensure_entity(conn, target_id, target_id)

        # Check for cached score first
        cached = get_trust_score(conn, source_id, target_id)
        if cached is not None:
            return {
                "source_id": source_id,
                "target_id": target_id,
                "score": cached.score,
                "confidence": cached.confidence,
                "behavior_count": cached.behavior_count,
                "cold_start": cached.behavior_count < 10,
            }

        # Compute fresh
        score, confidence = compute_trust(conn, source_id, target_id)
        behavior_count = conn.execute(
            "SELECT COUNT(*) AS c FROM behaviors WHERE source_id = ? AND target_id = ?",
            (source_id, target_id),
        ).fetchone()["c"]

        return {
            "source_id": source_id,
            "target_id": target_id,
            "score": score,
            "confidence": confidence,
            "behavior_count": behavior_count,
            "cold_start": behavior_count < 10,
        }
    finally:
        conn.close()


def detect_collusion(
    pattern: str | None = None,
    entity_id: str | None = None,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Detect collusion patterns.

    If *pattern* is provided, only that detector runs. Supported patterns:
    ``"price_parallelism"``, ``"deal_rotation"``, ``"market_allocation"``, or
    ``None`` (run all). If *entity_id* is set, results are filtered to flags
    involving that entity.
    """
    conn = open_db(db_path)
    try:
        if pattern:
            detectors = {
                "price_parallelism": lambda: detect_price_parallelism(conn),
                "deal_rotation": lambda: detect_deal_rotation(conn),
                "market_allocation": lambda: detect_market_allocation(conn),
            }
            detector = detectors.get(pattern)
            if detector:
                detector()
        else:
            # Run all detectors
            detect_price_parallelism(conn)
            detect_deal_rotation(conn)
            detect_market_allocation(conn)

        # Query results
        flags = find_collusion(conn, pattern=pattern, entity_id=entity_id)
        return [
            {
                "id": f.id,
                "pattern": f.pattern,
                "entity_a_id": f.entity_a_id,
                "entity_b_id": f.entity_b_id,
                "evidence": f.evidence,
                "severity": f.severity,
                "detected_at": f.detected_at,
            }
            for f in flags
        ]
    finally:
        conn.close()


def get_status(
    db_path: str | None = None,
) -> dict[str, Any]:
    """Return graph status summary."""
    conn = open_db(db_path)
    try:
        return _get_store_status(conn)
    finally:
        conn.close()

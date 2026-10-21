# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Trust, collusion, status queries, and row mappers for the behavior graph store."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from src.mekong.graph.types import Behavior, CollusionFlag, TrustScore


def upsert_trust_score(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    score: int,
    confidence: int,
    raw_alpha: float = 0.0,
    raw_beta: float = 0.0,
    raw_gamma: float = 0.0,
    raw_delta: float = 0.0,
    raw_epsilon: float = 0.0,
    raw_zeta: float = 0.0,
    behavior_count: int = 0,
) -> None:
    """Insert or update a trust score between two entities."""
    conn.execute(
        """INSERT INTO trust_scores
               (source_id, target_id, score, confidence,
                raw_alpha, raw_beta, raw_gamma, raw_delta, raw_epsilon, raw_zeta,
                behavior_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(source_id, target_id) DO UPDATE SET
               score           = excluded.score,
               confidence      = excluded.confidence,
               raw_alpha       = excluded.raw_alpha,
               raw_beta        = excluded.raw_beta,
               raw_gamma       = excluded.raw_gamma,
               raw_delta       = excluded.raw_delta,
               raw_epsilon     = excluded.raw_epsilon,
               raw_zeta        = excluded.raw_zeta,
               behavior_count  = excluded.behavior_count,
               updated_at      = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')""",
        (
            source_id,
            target_id,
            score,
            confidence,
            raw_alpha,
            raw_beta,
            raw_gamma,
            raw_delta,
            raw_epsilon,
            raw_zeta,
            behavior_count,
        ),
    )


def get_trust_score(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
) -> TrustScore | None:
    """Return the stored trust score, or ``None`` if not computed yet."""
    row = conn.execute(
        "SELECT * FROM trust_scores WHERE source_id = ? AND target_id = ?",
        (source_id, target_id),
    ).fetchone()
    if row is None:
        return None
    return TrustScore(
        source_id=row["source_id"],
        target_id=row["target_id"],
        score=row["score"],
        confidence=row["confidence"],
        behavior_count=row["behavior_count"],
        updated_at=row["updated_at"],
    )


def insert_collusion_flag(
    conn: sqlite3.Connection,
    pattern: str,
    entity_a_id: str,
    entity_b_id: str,
    evidence: dict[str, Any],
    severity: str = "medium",
) -> int:
    """Insert a collusion flag and return its ID."""
    cur = conn.execute(
        """INSERT INTO collusion_flags (pattern, entity_a_id, entity_b_id, evidence, severity)
           VALUES (?, ?, ?, ?, ?)""",
        (pattern, entity_a_id, entity_b_id, json.dumps(evidence), severity),
    )
    return cur.lastrowid or 0


def find_collusion(
    conn: sqlite3.Connection,
    pattern: str | None = None,
    entity_id: str | None = None,
    active_only: bool = True,
) -> list[CollusionFlag]:
    """Query collusion flags with optional filters."""
    clauses: list[str] = []
    params: list[Any] = []

    if pattern is not None:
        clauses.append("pattern = ?")
        params.append(pattern)
    if entity_id is not None:
        clauses.append("(entity_a_id = ? OR entity_b_id = ?)")
        params.extend([entity_id, entity_id])
    if active_only:
        clauses.append("cleared_at IS NULL")

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM collusion_flags {where} ORDER BY detected_at DESC",
        params,
    ).fetchall()

    return [_row_to_collusion(r) for r in rows]


def get_status(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return a snapshot of graph metadata — entity count, edge count, etc."""
    entity_count = conn.execute("SELECT COUNT(*) AS c FROM entities").fetchone()["c"]
    behavior_count = conn.execute("SELECT COUNT(*) AS c FROM behaviors").fetchone()["c"]
    trust_count = conn.execute("SELECT COUNT(*) AS c FROM trust_scores").fetchone()["c"]
    collusion_count = conn.execute(
        "SELECT COUNT(*) AS c FROM collusion_flags WHERE cleared_at IS NULL"
    ).fetchone()["c"]

    version_row = conn.execute(
        "SELECT value FROM graph_meta WHERE key = 'schema_version'"
    ).fetchone()
    schema_version = int(version_row["value"]) if version_row else 0

    return {
        "schema_version": schema_version,
        "entities": entity_count,
        "behaviors": behavior_count,
        "trust_scores": trust_count,
        "active_collusion_flags": collusion_count,
    }


def _row_to_behavior(row: sqlite3.Row) -> Behavior:
    return Behavior(
        id=row["id"],
        source_id=row["source_id"],
        target_id=row["target_id"],
        action=row["action"],
        payload=json.loads(row["payload"]) if isinstance(row["payload"], str) else {},
        value=row["value"],
        timestamp=row["timestamp"],
    )


def _row_to_collusion(row: sqlite3.Row) -> CollusionFlag:
    return CollusionFlag(
        id=row["id"],
        pattern=row["pattern"],
        entity_a_id=row["entity_a_id"],
        entity_b_id=row["entity_b_id"],
        evidence=json.loads(row["evidence"]) if isinstance(row["evidence"], str) else {},
        severity=row["severity"],
        detected_at=row["detected_at"],
        cleared_at=row["cleared_at"],
    )

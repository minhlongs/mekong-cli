# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite connection management and CRUD operations for the behavior graph.

Uses WAL mode for concurrent reads and ``BEGIN IMMEDIATE`` for multi-statement
write transactions to avoid ``SQLITE_BUSY`` under parallel agents.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.mekong.graph.schema import init_db
from src.mekong.graph.types import Behavior, CollusionFlag, TrustScore

# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

_DEFAULT_DB_PATH = ".mekong/graph.db"


def _ensure_dir(path: str) -> None:
    parent = Path(path).parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def open_db(db_path: str | None = None) -> sqlite3.Connection:
    """Open (or create) the graph database at *db_path*.

    Enables WAL mode and initialises the schema on first connection.
    Returns a :class:`sqlite3.Connection` with ``row_factory = sqlite3.Row``.
    """
    path = db_path or _DEFAULT_DB_PATH
    _ensure_dir(path)

    # Autocommit mode — no implicit transactions.
    # Callers must explicitly BEGIN IMMEDIATE / COMMIT for multi-statement writes.
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    # Ensure schema exists
    init_db(conn)

    return conn


def close_db(conn: sqlite3.Connection) -> None:
    """Close the database connection gracefully."""
    conn.close()


# ---------------------------------------------------------------------------
# Entity helpers
# ---------------------------------------------------------------------------


def ensure_entity(
    conn: sqlite3.Connection,
    entity_id: str,
    name: str,
    kind: str = "particle",
    metadata: dict[str, Any] | None = None,
) -> None:
    """Insert an entity if it does not exist; otherwise update its name."""
    conn.execute(
        """INSERT INTO entities (id, name, kind, metadata)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
               name = excluded.name,
               kind = excluded.kind,
               metadata = excluded.metadata""",
        (entity_id, name, kind, json.dumps(metadata or {})),
    )


def get_entity(
    conn: sqlite3.Connection,
    entity_id: str,
) -> dict[str, Any] | None:
    """Retrieve a single entity by its ID.

    Returns a dict with keys *id*, *name*, *kind*, *metadata*, *created_at*
    or ``None`` if not found.
    """
    row = conn.execute(
        "SELECT id, name, kind, metadata, created_at FROM entities WHERE id = ?",
        (entity_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "kind": row["kind"],
        "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else {},
        "created_at": row["created_at"],
    }


def query_entities_by_kind(
    conn: sqlite3.Connection,
    kind: str,
) -> list[dict[str, Any]]:
    """Return all entities matching *kind*, ordered by creation time ascending."""
    rows = conn.execute(
        "SELECT id, name, kind, metadata, created_at FROM entities WHERE kind = ? ORDER BY created_at ASC",
        (kind,),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "kind": r["kind"],
            "metadata": json.loads(r["metadata"]) if isinstance(r["metadata"], str) else {},
            "created_at": r["created_at"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Behavior CRUD
# ---------------------------------------------------------------------------


def record_behavior(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
    value: float = 0.0,
    timestamp: str | None = None,
) -> int:
    """Insert a behavior edge and return its ID.

    Uses ``BEGIN IMMEDIATE`` to prevent write conflicts.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute(
            """INSERT INTO behaviors (source_id, target_id, action, payload, value, timestamp)
               VALUES (?, ?, ?, ?, ?, COALESCE(?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now')))""",
            (source_id, target_id, action, json.dumps(payload or {}), value, timestamp),
        )
        conn.commit()
        return cur.lastrowid or 0
    except BaseException:
        conn.rollback()
        raise


def get_behaviors(
    conn: sqlite3.Connection,
    source_id: str | None = None,
    target_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
) -> list[Behavior]:
    """Query behaviors with optional filters."""
    clauses: list[str] = []
    params: list[Any] = []

    if source_id is not None:
        clauses.append("source_id = ?")
        params.append(source_id)
    if target_id is not None:
        clauses.append("target_id = ?")
        params.append(target_id)
    if action is not None:
        clauses.append("action = ?")
        params.append(action)

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM behaviors {where} ORDER BY timestamp DESC LIMIT ?",
        (*params, limit),
    ).fetchall()

    return [_row_to_behavior(r) for r in rows]


def get_behavior_count(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
) -> int:
    """Return the number of behaviors between a source and target."""
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM behaviors WHERE source_id = ? AND target_id = ?",
        (source_id, target_id),
    ).fetchone()
    return row["cnt"] if row else 0


# ---------------------------------------------------------------------------
# Trust score CRUD
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Collusion CRUD
# ---------------------------------------------------------------------------


def insert_collusion_flag(
    conn: sqlite3.Connection,
    pattern: str,
    entity_a_id: str,
    entity_b_id: str,
    evidence: dict[str, Any],
    severity: str = "medium",
) -> int:
    """Insert a collusion flag and return its ID.

    Caller is responsible for transaction management (BEGIN/COMMIT).
    """
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
        params,  # <-- was missing! params must be passed to execute()
    ).fetchall()

    return [_row_to_collusion(r) for r in rows]


# ---------------------------------------------------------------------------
# Status / meta
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


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

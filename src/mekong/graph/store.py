# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite connection management and CRUD operations for the behavior graph."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.mekong.graph.schema import init_db
from src.mekong.graph.store_queries import (
    _row_to_behavior,
    _row_to_collusion,
    find_collusion,
    get_status,
    get_trust_score,
    insert_collusion_flag,
    upsert_trust_score,
)
from src.mekong.graph.types import Behavior, CollusionFlag, TrustScore

_DEFAULT_DB_PATH = ".mekong/graph.db"


def _ensure_dir(path: str) -> None:
    parent = Path(path).parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def open_db(db_path: str | None = None) -> sqlite3.Connection:
    """Open (or create) the graph database at *db_path*."""
    path = db_path or _DEFAULT_DB_PATH
    _ensure_dir(path)
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    init_db(conn)
    return conn


def close_db(conn: sqlite3.Connection) -> None:
    """Close the database connection gracefully."""
    conn.close()


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


def get_entity(conn: sqlite3.Connection, entity_id: str) -> dict[str, Any] | None:
    """Retrieve a single entity by its ID."""
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


def query_entities_by_kind(conn: sqlite3.Connection, kind: str) -> list[dict[str, Any]]:
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


def record_behavior(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
    value: float = 0.0,
    timestamp: str | None = None,
) -> int:
    """Insert a behavior edge and return its ID."""
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


def get_behavior_count(conn: sqlite3.Connection, source_id: str, target_id: str) -> int:
    """Return the number of behaviors between a source and target."""
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM behaviors WHERE source_id = ? AND target_id = ?",
        (source_id, target_id),
    ).fetchone()
    return row["cnt"] if row else 0


__all__ = [
    "Behavior", "CollusionFlag", "TrustScore", "_DEFAULT_DB_PATH",
    "_ensure_dir", "_row_to_behavior", "_row_to_collusion", "close_db",
    "ensure_entity", "find_collusion", "get_behavior_count", "get_behaviors",
    "get_entity", "get_status", "get_trust_score", "insert_collusion_flag",
    "open_db", "query_entities_by_kind", "record_behavior", "upsert_trust_score",
]

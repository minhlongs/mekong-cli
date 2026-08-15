"""Seed memory — SQLite-backed store with agent isolation."""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

CHROMA_PATH: str = os.getenv("CHROMA_PATH", "/tmp/seed_chroma")
SQLITE_PATH: str = os.getenv("SQLITE_PATH", "/tmp/seed_memory.db")


class SeedMemory:
    """Memory store with agent-scoped access."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else Path(SQLITE_PATH)
        self._ensure_schema()
        self._conn: sqlite3.Connection | None = None

    def _ensure_schema(self) -> None:
        conn = sqlite3.connect(str(self.path))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS memories ("
            "  doc_id TEXT PRIMARY KEY,"
            "  agent_id TEXT NOT NULL,"
            "  content TEXT,"
            "  metadata TEXT,"
            "  created_at REAL"
            ")"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_created "
            "ON memories(agent_id, created_at DESC)"
        )
        conn.commit()
        conn.close()

    def _conn_ref(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def remember(
        self,
        agent_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persist a memory entry. Returns a string doc_id."""
        doc_id = str(uuid.uuid4())
        meta = dict(metadata) if metadata else {}
        meta.setdefault("agent_id", agent_id)
        conn = self._conn_ref()
        conn.execute(
            "INSERT INTO memories (doc_id, agent_id, content, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (doc_id, agent_id, content, json.dumps(meta), time.time()),
        )
        conn.commit()
        return doc_id

    def recall(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Return matches for query via LIKE on content."""
        conn = self._conn_ref()
        rows = conn.execute(
            "SELECT doc_id, agent_id, content, metadata, created_at "
            "FROM memories WHERE content LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_recent(
        self,
        agent_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return most recent entries for agent_id, newest first."""
        conn = self._conn_ref()
        rows = conn.execute(
            "SELECT doc_id, agent_id, content, metadata, created_at "
            "FROM memories WHERE agent_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (agent_id, limit),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def clear_agent_memory(self, agent_id: str) -> None:
        """Delete all entries for agent_id."""
        conn = self._conn_ref()
        conn.execute("DELETE FROM memories WHERE agent_id = ?", (agent_id,))
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        d["metadata"] = json.loads(d.get("metadata") or "{}")
        return d

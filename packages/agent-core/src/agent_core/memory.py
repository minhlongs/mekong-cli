"""SeedMemory — SQLite metadata + optional ChromaDB vector store.

ChromaDB is lazy-imported; if not installed, semantic `recall()` falls back to
LIKE search on SQLite so the package still runs with `poetry install` (no
`--with vector`). This keeps the default install lean.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_ROOT = Path.home() / ".agent-core"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    id         TEXT PRIMARY KEY,
    agent_id   TEXT NOT NULL,
    content    TEXT NOT NULL,
    metadata   TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mem_agent ON memories (agent_id);
CREATE INDEX IF NOT EXISTS idx_mem_created ON memories (created_at);

CREATE TABLE IF NOT EXISTS eval_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   TEXT NOT NULL,
    dataset_hash TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    score        REAL NOT NULL,
    passed       INTEGER NOT NULL,
    total        INTEGER NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_eval_dataset ON eval_runs (dataset_name, created_at);
"""


@dataclass
class MemoryRecord:
    id: str
    agent_id: str
    content: str
    metadata: dict[str, Any]
    created_at: str


class SeedMemory:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)
        self.sqlite_path = self.root / "memory.db"
        self.chroma_path = self.root / "chroma"
        self._init_sqlite()
        self._chroma_client: Any = None

    def _init_sqlite(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA_SQL)
            conn.commit()
        self._chmod_0600(self.sqlite_path)

    @staticmethod
    def _chmod_0600(p: Path) -> None:
        try:
            os.chmod(str(p), stat.S_IRUSR | stat.S_IWUSR)
        except OSError as e:
            log.debug("chmod 0600 failed on %s: %s", p, e)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.sqlite_path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        try:
            yield conn
        finally:
            conn.close()

    def _chroma(self):  # pragma: no cover - exercised only when chromadb installed
        if self._chroma_client is None:
            try:
                import chromadb
                self.chroma_path.mkdir(parents=True, exist_ok=True)
                self._chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
            except Exception as e:
                # ImportError or pydantic compat issue (e.g. Python 3.14 + old chromadb)
                log.debug("chromadb unavailable: %s — falling back to SQLite", e)
                return None
        return self._chroma_client

    def remember(
        self,
        agent_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        doc_id = str(uuid.uuid4())
        ts = datetime.now(UTC).isoformat()
        meta_json = json.dumps(metadata or {})
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO memories (id, agent_id, content, metadata, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (doc_id, agent_id, content, meta_json, ts),
            )
            conn.commit()
        client = self._chroma()
        if client is not None:  # pragma: no cover
            coll = client.get_or_create_collection(name=agent_id)
            coll.add(documents=[content], metadatas=[metadata or {}], ids=[doc_id])
        return doc_id

    def recall(self, agent_id: str, query: str, n_results: int = 3) -> list[str]:
        client = self._chroma()
        if client is not None:  # pragma: no cover
            coll = client.get_or_create_collection(name=agent_id)
            res = coll.query(query_texts=[query], n_results=n_results)
            docs = (res.get("documents") or [[]])[0]
            if docs:
                return list(docs)
        return self._sqlite_like(agent_id, query, n_results)

    def _sqlite_like(self, agent_id: str, query: str, n: int) -> list[str]:
        like = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT content FROM memories WHERE agent_id = ? AND content LIKE ? "
                "ORDER BY created_at DESC LIMIT ?",
                (agent_id, like, n),
            ).fetchall()
        return [r[0] for r in rows]

    def get_recent(self, agent_id: str, limit: int = 5) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, agent_id, content, metadata, created_at FROM memories "
                "WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
                (agent_id, limit),
            ).fetchall()
        return [
            MemoryRecord(
                id=r[0],
                agent_id=r[1],
                content=r[2],
                metadata=json.loads(r[3] or "{}"),
                created_at=r[4],
            )
            for r in rows
        ]

    def prune_agent(self, agent_id: str, keep_last_n: int) -> int:
        """Delete all but the newest ``keep_last_n`` rows for ``agent_id``. Returns deleted count.

        ``keep_last_n`` must be >=0. 0 means delete everything (same as clear_agent
        but without touching chroma). Chroma vector store is pruned by id for the
        same rows so SQLite and Chroma stay in sync.
        """
        if keep_last_n < 0:
            raise ValueError("keep_last_n must be >= 0")
        with self._connect() as conn:
            # Find ids to delete: all rows except newest N by created_at DESC.
            stale = conn.execute(
                "SELECT id FROM memories WHERE agent_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT -1 OFFSET ?",
                (agent_id, keep_last_n),
            ).fetchall()
            if not stale:
                return 0
            stale_ids = [r[0] for r in stale]
            placeholders = ",".join("?" * len(stale_ids))
            conn.execute(
                f"DELETE FROM memories WHERE id IN ({placeholders})", stale_ids
            )
            conn.commit()
        client = self._chroma()
        if client is not None:  # pragma: no cover
            try:
                coll = client.get_or_create_collection(name=agent_id)
                coll.delete(ids=stale_ids)
            except Exception as e:
                log.debug("chroma prune failed: %s", e)
        return len(stale_ids)

    def clear_agent(self, agent_id: str) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM memories WHERE agent_id = ?", (agent_id,))
            conn.commit()
            deleted = cur.rowcount
        client = self._chroma()
        if client is not None:  # pragma: no cover
            try:
                client.delete_collection(name=agent_id)
            except Exception as e:
                log.debug("chroma delete failed: %s", e)
        return deleted

    def record_eval_run(
        self,
        dataset_name: str,
        dataset_hash: str,
        score: float,
        passed: int,
        total: int,
        details: Any,
    ) -> int:
        """Persist an eval run and return the new row id."""
        ts = datetime.now(UTC).isoformat()
        details_json = json.dumps(details, ensure_ascii=False, sort_keys=True)
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO eval_runs "
                "(created_at, dataset_hash, dataset_name, score, passed, total, details_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ts, dataset_hash, dataset_name, score, passed, total, details_json),
            )
            conn.commit()
            return cur.lastrowid  # type: ignore[return-value]

    def recent_eval_runs(self, dataset_name: str, limit: int = 5) -> list[dict]:
        """Return the most recent eval runs for the given dataset_name (newest first)."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, created_at, dataset_hash, dataset_name, "
                "score, passed, total, details_json "
                "FROM eval_runs WHERE dataset_name = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (dataset_name, limit),
            ).fetchall()
        return [
            {
                "id": r[0],
                "created_at": r[1],
                "dataset_hash": r[2],
                "dataset_name": r[3],
                "score": r[4],
                "passed": r[5],
                "total": r[6],
                "details": json.loads(r[7] or "{}"),
            }
            for r in rows
        ]

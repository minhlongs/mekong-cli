"""Agent memory: ChromaDB (semantic) + SQLite (metadata)."""

from __future__ import annotations

import atexit
import json
import logging
import sqlite3
import uuid
from typing import Any

import chromadb

from .config import CHROMA_PATH, SQLITE_PATH
from .llm_client import get_llm_client

logger = logging.getLogger(__name__)

_instance: "SeedMemory | None" = None


class SeedMemory:
    """Per-agent memory with semantic recall and recent history."""

    def __init__(self) -> None:
        self._chroma = chromadb.PersistentClient(path=CHROMA_PATH)
        self._sql = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        self._init_sql()
        atexit.register(self._sql.close)

    def _init_sql(self) -> None:
        self._sql.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._sql.commit()

    def remember(self, agent_id: str, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Store a memory entry. Returns doc_id."""
        doc_id = str(uuid.uuid4())
        metadata = metadata or {}

        # Vector store (semantic search)
        try:
            col = self._chroma.get_or_create_collection(name=agent_id)
            embedding = get_llm_client().embed(content)
            if embedding:
                col.add(documents=[content], metadatas=[metadata], ids=[doc_id], embeddings=[embedding])
            else:
                col.add(documents=[content], metadatas=[metadata], ids=[doc_id])
        except Exception as e:
            logger.warning("Chroma store failed (non-fatal): %s", e)

        # SQLite (fast recent lookup)
        self._sql.execute(
            "INSERT INTO memories (id, agent_id, content, metadata) VALUES (?, ?, ?, ?)",
            (doc_id, agent_id, content, json.dumps(metadata)),
        )
        self._sql.commit()
        return doc_id

    def recall(self, agent_id: str, query: str, n_results: int = 3) -> list[str]:
        """Semantic search for relevant memories."""
        try:
            col = self._chroma.get_or_create_collection(name=agent_id)
            embedding = get_llm_client().embed(query)
            if embedding:
                results = col.query(query_embeddings=[embedding], n_results=n_results)
            else:
                results = col.query(query_texts=[query], n_results=n_results)
            return results.get("documents", [[]])[0]
        except Exception as e:
            logger.warning("Recall failed: %s", e)
            return []

    def get_recent(self, agent_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Return most recent memories by timestamp."""
        cur = self._sql.execute(
            "SELECT content, metadata, created_at FROM memories WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
            (agent_id, limit),
        )
        return [
            {"content": r[0], "metadata": json.loads(r[1] or "{}"), "created_at": r[2]}
            for r in cur.fetchall()
        ]

    def clear_agent_memory(self, agent_id: str) -> None:
        """Delete all memories for an agent."""
        try:
            self._chroma.delete_collection(name=agent_id)
        except Exception:
            pass
        self._sql.execute("DELETE FROM memories WHERE agent_id = ?", (agent_id,))
        self._sql.commit()


def get_memory() -> SeedMemory:
    """Return singleton SeedMemory."""
    global _instance
    if _instance is None:
        _instance = SeedMemory()
    return _instance

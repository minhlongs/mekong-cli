# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps MemoryStore (YAML+vector) to satisfy MemoryStore Protocol."""

from __future__ import annotations

import json
from typing import Any

from src.core.memory_canonical import MemoryStore
from src.core.protocols import MemoryHit


class MemoryStoreAdapter:
    """Thin adapter mapping MemoryStore Protocol methods to MemoryStore methods.

    Protocol → Implementation:
    - store(key, value, ttl)   → record(MemoryEntry) with encoded bytes
    - retrieve(key)            → query(goal_pattern) with decoded bytes
    - delete(key)              → remove matching entries
    - search(query, limit)     → semantic_search(query, limit)
    """

    def __init__(self, store: MemoryStore | None = None) -> None:
        self._store = store or MemoryStore()

    def store(self, key: str, value: bytes, ttl: int | None = None) -> None:
        """Store bytes value under key."""
        try:
            decoded: dict[str, Any] = json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            decoded = {"raw": value.decode("utf-8", errors="replace")}

        from dataclasses import dataclass, field
        import time

        @dataclass
        class _Entry:
            goal: str
            status: str
            timestamp: float = field(default_factory=time.time)
            context: dict[str, Any] = field(default_factory=dict)

        entry = _Entry(goal=key, status="success", context=decoded)
        self._store.record(entry)  # type: ignore[arg-type]

    def retrieve(self, key: str) -> bytes | None:
        """Retrieve bytes value for key, or None if missing."""
        entries = self._store.query(key)
        if not entries:
            return None
        entry = entries[0]
        if not entry.context:
            return None
        try:
            return json.dumps(entry.context).encode("utf-8")
        except (TypeError, ValueError):
            return str(entry.context).encode("utf-8")

    def delete(self, key: str) -> bool:
        """Delete entry matching key. Returns True if removed."""
        entries = self._store.query(key)
        if not entries:
            return False
        matched = [e for e in entries if e.goal == key]
        if not matched:
            return False
        self._store._entries = [
            e for e in self._store._entries if e.goal != key
        ]
        self._store._save()
        return True

    def search(self, query: str, limit: int = 10) -> list[MemoryHit]:
        """Semantic search returning MemoryHit-compatible results."""
        results: list[MemoryHit] = []
        entries = self._store.semantic_search(query, top_k=limit)
        for idx, entry in enumerate(entries[:limit]):
            results.append(
                MemoryHit(
                    key=entry.goal,
                    score=1.0 - (idx * 0.1),
                    data=str(entry.context).encode("utf-8"),
                    metadata={
                        "status": entry.status,
                        "timestamp": entry.timestamp,
                        "error_summary": entry.error_summary,
                    },
                )
            )
        return results
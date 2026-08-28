# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Conformant adapter: wraps memory_canonical.MemoryStore to satisfy the
``protocols.MemoryStore`` Protocol (src/core/protocols.py).

Protocol → canonical implementation mapping:
- store(key, value, ttl)  → record(MemoryEntry) — value kept as base64 in context
- retrieve(key)           → query(key) — exact-goal match, bytes decoded back
- delete(key)             → filter matching entries + persist (no per-key API upstream)
- search(query, limit)    → semantic_search(query) with substring fallback,
                            results mapped to MemoryHit-shaped dataclasses

The canonical store has no native TTL or per-key delete; TTL is honored by
storing ``expires_at`` in the entry context and filtering on read. This adapter
wraps — it never rewrites — memory_canonical.MemoryStore.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from src.core.memory_canonical import MemoryEntry, MemoryStore
from src.core.protocols import MemoryHit

_VALUE_KEY = "value_b64"
_EXPIRES_KEY = "expires_at"


@dataclass
class MemoryHitResult:
    """Concrete MemoryHit-shaped result (the Protocol itself is not instantiable)."""

    key: str
    score: float
    data: bytes
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryStoreConformant:
    """Wraps memory_canonical.MemoryStore to satisfy protocols.MemoryStore."""

    def __init__(
        self,
        store: MemoryStore | None = None,
        store_path: str | None = None,
    ) -> None:
        self._store = store if store is not None else MemoryStore(store_path=store_path)

    # --- protocols.MemoryStore interface ---

    def store(self, key: str, value: bytes, ttl: int | None = None) -> None:
        """Persist bytes under key via canonical record()."""
        context: Dict[str, Any] = {
            _VALUE_KEY: base64.b64encode(value).decode("ascii"),
        }
        if ttl is not None:
            context[_EXPIRES_KEY] = time.time() + ttl
        entry = MemoryEntry(goal=key, status="success", context=context)
        self._store.record(entry)

    def retrieve(self, key: str) -> bytes | None:
        """Return the most recent non-expired value for key, or None."""
        for entry in reversed(self._store.query(key)):
            if entry.goal != key or self._is_expired(entry):
                continue
            return self._decode(entry)
        return None

    def delete(self, key: str) -> bool:
        """Remove all entries matching key. Returns True if anything was removed."""
        kept = [e for e in self._store._entries if e.goal != key]
        removed = len(kept) < len(self._store._entries)
        if removed:
            self._store._entries = kept
            self._store._save()
        return removed

    def search(self, query: str, limit: int = 10) -> Sequence[MemoryHit]:
        """Semantic search with substring fallback, mapped to MemoryHit shapes."""
        hits: List[MemoryHitResult] = []
        seen: set[str] = set()

        # 1) Vector semantic search (canonical path).
        for entry in self._store.semantic_search(query, top_k=limit):
            self._accept(entry, query, seen, score=1.0, out=hits)

        # 2) Substring fallback — hash-based vectors rarely clear the canonical
        #    similarity threshold, so text matching keeps search usable.  Match
        #    directly against _entries because query() returns early after its
        #    own semantic pass and would not yield all substring matches.
        needle = query.lower()
        for entry in self._store._entries:
            if len(hits) >= limit:
                break
            if needle and needle not in entry.goal.lower():
                continue
            self._accept(entry, query, seen, score=0.5, out=hits)

        return hits[:limit]

    # --- Helpers ---

    def _accept(
        self,
        entry: MemoryEntry,
        query: str,
        seen: set[str],
        score: float,
        out: List[MemoryHitResult],
    ) -> bool:
        """Append entry as a hit if it matches and is fresh; returns True if added."""
        if entry.goal in seen or self._is_expired(entry):
            return False
        if query and query.lower() not in entry.goal.lower():
            return False
        seen.add(entry.goal)
        data = self._decode(entry) or b""
        out.append(
            MemoryHitResult(
                key=entry.goal,
                score=score,
                data=data,
                metadata={
                    "status": entry.status,
                    "timestamp": entry.timestamp,
                },
            )
        )
        return True

    @staticmethod
    def _is_expired(entry: MemoryEntry) -> bool:
        expires_at = (entry.context or {}).get(_EXPIRES_KEY)
        return expires_at is not None and time.time() >= float(expires_at)

    @staticmethod
    def _decode(entry: MemoryEntry) -> bytes | None:
        encoded = (entry.context or {}).get(_VALUE_KEY)
        if not encoded:
            return None
        try:
            return base64.b64decode(encoded.encode("ascii"))
        except (ValueError, UnicodeEncodeError):
            return None


__all__ = [
    "MemoryHitResult",
    "MemoryStoreConformant",
]

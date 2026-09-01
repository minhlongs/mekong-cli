# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps MemoryStore (YAML+vector) to satisfy MemoryStore Protocol.

Conforms to ``protocols.MemoryStore`` (store/retrieve/delete/search) by mapping
onto ``memory_canonical.MemoryStore`` (the YAML+vector execution-memory store).

Protocol → canonical implementation:
- store(key, value, ttl)  → record(MemoryEntry) — value kept as base64 in
  context; TTL stored as ``expires_at`` (the canonical store has no native TTL).
- retrieve(key)           → query(key) — exact-goal match, value decoded from
  base64, expired entries filtered out.
- delete(key)             → filter matching entries + persist (no per-key API).
- search(query, limit)    → semantic_search(query) with substring fallback,
  results mapped to concrete MemoryHitResult dataclasses.

The canonical store has no native TTL or per-key delete; TTL is honored by
storing ``expires_at`` in the entry context and filtering on read. This adapter
wraps — it never rewrites — ``memory_canonical.MemoryStore``.
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
    """Concrete MemoryHit-shaped result (the Protocol is not instantiable)."""

    key: str
    score: float
    data: bytes
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryStoreAdapter:
    """Wraps memory_canonical.MemoryStore to satisfy protocols.MemoryStore.

    The default no-arg constructor (``MemoryStoreAdapter()``) builds an
    underlying ``MemoryStore`` at its default path — existing callers rely on
    this, so it must remain supported.
    """

    def __init__(self, store: MemoryStore | None = None) -> None:
        self._store = store or MemoryStore()

    # --- protocols.MemoryStore interface ---

    def store(self, key: str, value: bytes, ttl: int | None = None) -> None:
        """Store bytes value under key.

        Bytes are base64-encoded into the entry context so arbitrary binary
        (non-UTF8) round-trips bit-exact. When ``ttl`` is given, an
        ``expires_at`` timestamp (seconds) is stored alongside; ``retrieve()``
        treats entries past that instant as absent.
        """
        context: Dict[str, Any] = {
            _VALUE_KEY: base64.b64encode(value).decode("ascii"),
        }
        if ttl is not None:
            context[_EXPIRES_KEY] = time.time() + ttl
        self._store.record(MemoryEntry(goal=key, status="success", context=context))

    def retrieve(self, key: str) -> bytes | None:
        """Return the most recent non-expired value for key, or None.

        Iterates query() results newest-first, skipping entries whose goal does
        not exactly match or whose TTL has elapsed, then decodes the base64
        value.
        """
        for entry in reversed(self._store.query(key)):
            if entry.goal != key or _is_expired(entry):
                continue
            decoded = _decode_value(entry)
            if decoded is not None:
                return decoded
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
        """Semantic search with substring fallback, mapped to MemoryHit shapes.

        The canonical hash-based vectors rarely clear the 0.3 similarity
        threshold, so a substring fallback over ``_entries`` keeps search
        usable. Results are de-duplicated by goal and capped at ``limit``.
        """
        hits: List[MemoryHitResult] = []
        seen: set[str] = set()

        # 1) Vector semantic search (canonical path).
        for entry in self._store.semantic_search(query, top_k=limit):
            _accept_hit(entry, query, seen, score=1.0, out=hits)

        # 2) Substring fallback against stored goals.
        needle = query.lower()
        for entry in self._store._entries:
            if len(hits) >= limit:
                break
            if needle and needle not in entry.goal.lower():
                continue
            _accept_hit(entry, query, seen, score=0.5, out=hits)

        return hits[:limit]


# --- Module-level helpers (stateless over a single entry) ---


def _is_expired(entry: MemoryEntry) -> bool:
    """True if the entry has an expires_at timestamp that has elapsed."""
    expires_at = (entry.context or {}).get(_EXPIRES_KEY)
    return expires_at is not None and time.time() >= float(expires_at)


def _decode_value(entry: MemoryEntry) -> bytes | None:
    """Decode the base64-stored value from an entry's context, or None."""
    encoded = (entry.context or {}).get(_VALUE_KEY)
    if not encoded:
        return None
    try:
        return base64.b64decode(encoded.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        return None


def _accept_hit(
    entry: MemoryEntry,
    query: str,
    seen: set[str],
    score: float,
    out: List[MemoryHitResult],
) -> bool:
    """Append entry as a hit if it matches and is fresh; True if added."""
    if entry.goal in seen or _is_expired(entry):
        return False
    if query and query.lower() not in entry.goal.lower():
        return False
    seen.add(entry.goal)
    out.append(
        MemoryHitResult(
            key=entry.goal,
            score=score,
            data=_decode_value(entry) or b"",
            metadata={
                "status": entry.status,
                "timestamp": entry.timestamp,
            },
        )
    )
    return True


__all__ = [
    "MemoryHitResult",
    "MemoryStoreAdapter",
]

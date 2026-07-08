"""Append-only JSONL memory store for agent action history.

Schema: {timestamp, agent, action, outcome, tags}
Persists to .mekong/memory.jsonl (one JSON object per line).
Provides append, search, list, and clear operations.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_PATH = Path(".mekong/memory.jsonl")


@dataclass
class MemoryEntry:
    """Single execution memory record."""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    agent: str = ""
    action: str = ""
    outcome: str = ""
    tags: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


def _json_sorted(value: dict[str, Any]) -> str:
    """Serialize dict deterministically (sorted keys, ASCII-normalised)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _goal_context_hash(goal: str, context: str) -> str:
    """Deterministic hash for duplicate detection."""
    return hashlib.sha256(f"{goal}:{context}".encode()).hexdigest()


class MemoryStore:
    """Append-only JSONL memory store.

    Reads and writes .mekong/memory.jsonl, one JSON object per line.
    Provides append, recent list, tag/keyword search, and clear.
    """

    def __init__(self, path: str | Path = DEFAULT_MEMORY_PATH) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    def append(self, entry: MemoryEntry) -> None:
        """Append a new memory entry (append-only, never mutate)."""
        if not entry.agent or not entry.action:
            raise ValueError("agent and action are required")
        data = asdict(entry)
        data["context"] = json.loads(_json_sorted(entry.context))
        line = json.dumps(data, sort_keys=True, ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        logger.debug("memory.append agent=%s action=%s", entry.agent, entry.action)

    def recent(self, limit: int = 20) -> list[MemoryEntry]:
        """Return the most recent entries (up to limit)."""
        entries: list[MemoryEntry] = []
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            logger.debug("Failed to read memory store: %s", exc)
            return []
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                entries.append(MemoryEntry(**data))
            except (json.JSONDecodeError, TypeError) as exc:
                logger.debug("Skipping malformed memory line: %s", exc)
            if len(entries) >= limit:
                break
        return entries

    def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Search recent entries by substring match against action/tags/outcome.

        Args:
            query: Lowercase token or phrase to match.
            limit: Max results to return.

        Returns:
            Most recent matching entries, up to limit.
        """
        q = query.lower().strip()
        if not q:
            return []
        hits: list[MemoryEntry] = []
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            logger.debug("Failed to read memory store: %s", exc)
            return []
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                entry = MemoryEntry(**data)
            except (json.JSONDecodeError, TypeError) as exc:
                logger.debug("Skipping malformed memory line: %s", exc)
                continue
            haystack = " ".join(
                [
                    entry.action,
                    entry.outcome,
                    entry.agent,
                    " ".join(entry.tags),
                    _json_sorted(entry.context),
                ]
            ).lower()
            if q in haystack:
                hits.append(entry)
                if len(hits) >= limit:
                    break
        return hits

    def clear(self) -> int:
        """Wipe all entries. Returns number of lines removed."""
        count = 0
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
            count = sum(1 for line in lines if line.strip())
        except OSError as exc:
            logger.debug("Failed to count memory entries: %s", exc)
        self._path.write_text("", encoding="utf-8")
        return count

    def has_similar(self, goal: str, context: str, lookback: int = 50) -> MemoryEntry | None:
        """Return the most recent entry matching the same goal+context hash, if any.

        Used for duplicate-action detection.
        """
        target_hash = _goal_context_hash(goal, context)
        for entry in self.recent(limit=lookback):
            if _goal_context_hash(entry.action, _json_sorted(entry.context)) == target_hash:
                return entry
        return None


def memory_search(query: str, limit: int = 5, path: str | Path = DEFAULT_MEMORY_PATH) -> list[MemoryEntry]:
    """Convenience helper: search memory store.

    Args:
        query: Free-form search string.
        limit: Max entries to return (default 5).
        path: Override memory path (default .mekong/memory.jsonl).

    Returns:
        Matching MemoryEntry list, most recent first.
    """
    store = MemoryStore(path=path)
    return store.search(query, limit=limit)


def _action_context_hash(action: str, context: str) -> str:
    """Deterministic hash of action + context (used as duplicate key)."""
    return hashlib.sha256(f"{action}:{context}".encode()).hexdigest()


__all__ = [
    "MemoryEntry",
    "DEFAULT_MEMORY_PATH",
    "MemoryStore",
    "memory_search",
]


__all__ = [
    "MemoryEntry",
    "DEFAULT_MEMORY_PATH",
    "MemoryStore",
    "memory_search",
]

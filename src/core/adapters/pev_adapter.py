# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps PEV harness MemoryStore to implement MemoryBridge."""

from __future__ import annotations

from typing import Any

from src.core.memory_bridge import (  # noqa: F401
    MemoryBridge,
    MemoryKind,
    MemoryRecord,
)


class PevBridge:
    """Wraps PEV harness MemoryStore (in-memory dict) to satisfy MemoryBridge."""

    def __init__(self) -> None:
        try:
            from src.harness.pev.memory import MemoryStore as PevMemoryStore
            self._store = PevMemoryStore()
            self._has_pev = True
        except Exception:
            self._has_pev = False
            self._store = None  # type: ignore[assignment]
            self._fallback_store: dict[str, Any] = {}

    # --- MemoryBridge interface ---

    def record(self, item: MemoryRecord) -> str:
        """Persist to PEV MemoryStore (or fallback store). Returns entry_id."""
        if not self._has_pev:
            return self._fallback_record(item)
        entry_id = str(item.created_at)
        self._store.store(
            key=entry_id,
            value={
                "content": item.content,
                "kind": item.kind.value,
                "agent_id": item.agent_id,
                "metadata": item.metadata,
                "session_id": item.session_id,
                "user_id": item.user_id,
            },
        )
        return entry_id

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        kind: MemoryKind | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> list[MemoryRecord]:
        """Keyword search across PEV entries (or fallback store if PEV unavailable)."""
        results: list[MemoryRecord] = []
        q = query.lower() if query else ""
        if self._has_pev and self._store is not None:
            keys = list(self._store._data.keys())
            for key in keys[: limit * 3]:
                entry = self._store.recall(key)
                if not entry or not isinstance(entry.value, dict):
                    continue
                value = entry.value
                content = value.get("content", "")
                if q and q not in content.lower():
                    continue
                if kind and value.get("kind") != kind.value:
                    continue
                if agent_id and value.get("agent_id") != agent_id:
                    continue
                if session_id and value.get("session_id") != session_id:
                    continue
                if user_id and value.get("user_id") != user_id:
                    continue
                results.append(self._entry_to_record(entry, key))
                if len(results) >= limit:
                    break
        else:
            # Fallback: scan in-memory dict
            for key, entry in self._fallback_store.items():
                value = entry if isinstance(entry, dict) else {"content": str(entry)}
                content = value.get("content", "")
                if q and q not in content.lower():
                    continue
                if kind and value.get("kind") != kind.value:
                    continue
                if agent_id and value.get("agent_id") != agent_id:
                    continue
                if session_id and value.get("session_id") != session_id:
                    continue
                if user_id and value.get("user_id") != user_id:
                    continue
                results.append(
                    MemoryRecord(
                        content=content,
                        kind=MemoryKind(value.get("kind", "episodic")),
                        metadata=value.get("metadata", {}),
                        created_at=value.get("created_at", 0.0),
                        agent_id=value.get("agent_id"),
                        session_id=value.get("session_id"),
                        user_id=value.get("user_id"),
                    )
                )
                if len(results) >= limit:
                    break
        return results

    def recall(
        self,
        query: str,
        *,
        k: int = 5,
        agent_id: str | None = None,
    ) -> list[dict]:
        return [
            {"content": r.content, "agent_id": r.agent_id}
            for r in self.search(query, limit=k, agent_id=agent_id)
        ]

    def recent(
        self,
        *,
        agent_id: str | None = None,
        limit: int = 20,
        kind: MemoryKind | None = None,
    ) -> list[MemoryRecord]:
        """Return most recent entries (empty query searches all)."""
        return self.search("", limit=limit, kind=kind, agent_id=agent_id)

    def delete(self, key: str) -> bool:
        """Delete entry by key."""
        if not self._has_pev:
            return self._fallback_store.pop(key, None) is not None
        try:
            self._store.forget(key)
            return True
        except Exception:
            return False

    def stats(self) -> dict[str, Any]:
        """Return count and backend info."""
        count = len(self._fallback_store)
        if self._has_pev and self._store is not None:
            try:
                count += len(self._store._data)
            except (AttributeError, TypeError):
                pass
        return {"count": count, "backend": "pev", "has_pev": self._has_pev}

    def prune_expired(self) -> int:
        """PEV memory is in-memory with no TTL — returns 0."""
        return 0

    # --- Helpers ---

    @staticmethod
    def _entry_to_record(entry: Any, key: str) -> MemoryRecord:
        ctx = entry.value if isinstance(entry.value, dict) else {}
        kind_str = ctx.get("kind", "episodic")
        try:
            kind = MemoryKind(kind_str)
        except ValueError:
            kind = MemoryKind.EPISODIC
        created = entry.created_at.timestamp() if hasattr(entry.created_at, "timestamp") else 0.0
        return MemoryRecord(
            content=ctx.get("content", ""),
            kind=kind,
            metadata=ctx.get("metadata", {}),
            agent_id=ctx.get("agent_id"),
            session_id=ctx.get("session_id"),
            user_id=ctx.get("user_id"),
            created_at=created,
        )

    def _fallback_record(self, item: MemoryRecord) -> str:
        """Store in fallback dict when PEV memory unavailable."""
        import hashlib
        key = hashlib.sha256(
            f"{item.agent_id}:{item.content[:50]}:{item.created_at}".encode()
        ).hexdigest()[:16]
        self._fallback_store[key] = {
            "content": item.content,
            "kind": item.kind.value,
            "metadata": item.metadata,
            "agent_id": item.agent_id,
            "session_id": item.session_id,
            "user_id": item.user_id,
            "created_at": item.created_at,
        }
        return key

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps ScopedMemoryStore to implement MemoryBridge."""

from __future__ import annotations

from typing import Any

from src.core.memory_bridge import (  # noqa: F401 — Protocol used in isinstance checks
    MemoryBridge,
    MemoryKind,
    MemoryRecord,
)

from .scoped_adapter_helpers import dict_to_record, make_key, make_scope


class ScopedBridge:
    """Wraps ScopedMemoryStore (in-memory dict) to satisfy MemoryBridge."""

    def __init__(self) -> None:
        from src.core.memory_scope import ScopedMemoryStore
        self._store = ScopedMemoryStore()
        self._key_scope: dict[str, str] = {}

    def record(self, item: MemoryRecord) -> str:
        """Persist to ScopedMemoryStore, returns generated key."""
        from src.core.memory_scope import ScopedMemoryEntry
        entry_id = make_key(item)
        scope = make_scope(item=item)
        entry = ScopedMemoryEntry(
            key=entry_id,
            value={
                "content": item.content,
                "kind": item.kind.value,
                "metadata": item.metadata,
                "agent_id": item.agent_id,
                "session_id": item.session_id,
                "user_id": item.user_id,
            },
            ttl=item.ttl_seconds,
            scope=scope,
        )
        self._store.store(entry)
        self._key_scope[entry_id] = self._store._scope_key(scope)
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
        """Search by query string, filtering client-side."""
        scope = make_scope(
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
        )
        q = query.lower() if query else ""
        records: list[MemoryRecord] = []
        for entry in self._store.query(scope):
            value = entry.value if isinstance(entry.value, dict) else {"content": str(entry.value)}
            content = value.get("content", "")
            if q and q not in content.lower():
                continue
            if kind and value.get("kind", "episodic") != kind.value:
                continue
            if session_id and value.get("session_id") != session_id:
                continue
            if user_id and value.get("user_id") != user_id:
                continue
            records.append(dict_to_record({
                "key": entry.key,
                "value": value,
                "created_at": entry.created_at,
            }))
            if len(records) >= limit:
                break
        return records

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
        scope = make_scope(agent_id=agent_id)
        records: list[MemoryRecord] = []
        for entry in self._store.query(scope):
            value = entry.value if isinstance(entry.value, dict) else {"content": str(entry.value)}
            if kind and value.get("kind", "episodic") != kind.value:
                continue
            records.append(dict_to_record({
                "key": entry.key,
                "value": value,
                "created_at": entry.created_at,
            }))
            if len(records) >= limit:
                break
        return records

    def delete(self, key: str) -> bool:
        """Delete by key using the stored scope_key."""
        from src.core.memory_scope import MemoryScope
        scope_key = self._key_scope.get(key)
        if scope_key is None:
            return False
        scope = MemoryScope()
        parts = scope_key.split("|")
        if len(parts) >= 5:
            scope.org_id = parts[1] or None
            scope.user_id = parts[2] or None
            scope.agent_id = parts[3] or None
            scope.session_id = parts[4] or None
        result = self._store.delete(key, scope)
        if result:
            self._key_scope.pop(key, None)
        return result

    def stats(self) -> dict[str, Any]:
        return {"count": len(self._key_scope), "backend": "scoped", "note": "in-memory only"}

    def prune_expired(self) -> int:
        return self._store.prune_expired()

    _make_scope = staticmethod(make_scope)
    _dict_to_record = staticmethod(dict_to_record)


_make_key = make_key

__all__ = ["ScopedBridge", "_make_key"]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps MemoryStore (YAML+vector) to implement MemoryBridge."""

from __future__ import annotations

from typing import Any

from src.core.memory_bridge import (  # noqa: F401
    MemoryBridge,
    MemoryKind,
    MemoryRecord,
)

from .memory_store_adapter_helpers import (
    dict_to_record,
    entry_to_record,
    fallback_text_search,
    make_id,
)


class MemoryStoreBridge:
    """Wraps MemoryStore to satisfy MemoryBridge protocol."""

    def __init__(self, store_path: str | None = None) -> None:
        from src.core.memory_canonical import MemoryStore
        self._store = MemoryStore(store_path=store_path)
        self._id_map: dict[str, Any] = {}

    def record(self, item: MemoryRecord) -> str:
        """Persist via MemoryStore.record(), returns deterministic bridge_id."""
        from src.core.memory_canonical import MemoryEntry
        entry_id = make_id(item)
        entry = MemoryEntry(
            goal=item.content[:200],
            status="success",
            context={
                "kind": item.kind.value,
                "agent_id": item.agent_id,
                "session_id": item.session_id,
                "user_id": item.user_id,
                "bridge_id": entry_id,
                **item.metadata,
            },
        )
        self._store.record(entry)
        self._id_map[entry_id] = entry
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
        """Scoped search: only returns entries recorded by THIS bridge instance."""
        candidates: list[Any] = []
        seen_ids: set[str] = set()

        try:
            for entry in self._store.semantic_search(query, top_k=limit * 4):
                ctx = entry.context or {} if hasattr(entry, "context") else (entry.get("context") or {} if isinstance(entry, dict) else {})
                bid = ctx.get("bridge_id", "")
                if bid and bid in self._id_map and bid not in seen_ids:
                    seen_ids.add(bid)
                    candidates.append(entry)
        except Exception:
            pass

        fallback = self._fallback_text_search(query, limit * 4)
        for entry in fallback:
            bid = entry.get("bridge_id", "")
            if bid and bid not in seen_ids:
                seen_ids.add(bid)
                candidates.append(entry)

        records: list[MemoryRecord] = []
        for entry in candidates:
            ctx = entry.get("context") or {} if isinstance(entry, dict) else (entry.context or {})
            if agent_id and ctx.get("agent_id") != agent_id:
                continue
            if session_id and ctx.get("session_id") != session_id:
                continue
            if user_id and ctx.get("user_id") != user_id:
                continue
            if kind and ctx.get("kind") != kind.value:
                continue
            records.append(dict_to_record(entry) if isinstance(entry, dict) else entry_to_record(entry))
            if len(records) >= limit:
                break
        return records

    def _fallback_text_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        return fallback_text_search(self._id_map, query, top_k)

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
        results = self._store.recent(limit=limit * 2)
        records: list[MemoryRecord] = []
        for entry in results:
            ctx = entry.context or {}
            if agent_id and ctx.get("agent_id") != agent_id:
                continue
            if kind and ctx.get("kind") != kind.value:
                continue
            records.append(entry_to_record(entry))
            if len(records) >= limit:
                break
        return records

    def delete(self, key: str) -> bool:
        """Delete by bridge_id via reverse lookup."""
        removed = key in self._id_map
        self._id_map.pop(key, None)
        return removed

    def stats(self) -> dict[str, Any]:
        try:
            raw = self._store.stats()
        except Exception:
            raw = {}
        return {"count": len(self._id_map), "backend": "memory_store", **raw}

    def prune_expired(self) -> int:
        return self._store.compress_old_memories()

    _make_id = staticmethod(make_id)
    _dict_to_record = staticmethod(dict_to_record)
    _entry_to_record = staticmethod(entry_to_record)


__all__ = ["MemoryStoreBridge"]

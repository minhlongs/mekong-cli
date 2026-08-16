# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps MemoryStore (YAML+vector) to implement MemoryBridge."""

from __future__ import annotations

import hashlib
from typing import Any

from src.core.memory_bridge import (  # noqa: F401
    MemoryBridge,
    MemoryKind,
    MemoryRecord,
)


class MemoryStoreBridge:
    """Wraps MemoryStore to satisfy MemoryBridge protocol."""

    def __init__(self, store_path: str | None = None) -> None:
        from src.core.memory import MemoryStore
        self._store = MemoryStore(store_path=store_path)
        # bridge_id -> MemoryEntry (for reverse lookup / future delete)
        self._id_map: dict[str, Any] = {}

    # --- MemoryBridge interface ---

    def record(self, item: MemoryRecord) -> str:
        """Persist via MemoryStore.record(), returns deterministic bridge_id."""
        from src.core.memory import MemoryEntry
        entry_id = self._make_id(item)
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
        """Scoped search: only returns entries recorded by THIS bridge instance.

        Runs semantic_search AND fallback text scan, then merges+dedupes by
        bridge_id so only entries from this bridge's _id_map survive.
        """
        candidates: list[Any] = []
        seen_ids: set[str] = set()

        # 1) Semantic search (may return stale global YAML entries)
        try:
            for entry in self._store.semantic_search(query, top_k=limit * 4):
                ctx = entry.context or {} if hasattr(entry, "context") else (entry.get("context") or {} if isinstance(entry, dict) else {})
                bid = ctx.get("bridge_id", "")
                if bid and bid in self._id_map and bid not in seen_ids:
                    seen_ids.add(bid)
                    candidates.append(entry)
        except Exception:
            pass

        # 2) Fallback text scan (already scoped to _id_map)
        fallback = self._fallback_text_search(query, limit * 4)
        for entry in fallback:
            bid = entry.get("bridge_id", "")
            if bid and bid not in seen_ids:
                seen_ids.add(bid)
                candidates.append(entry)

        # 3) Apply scope filters + convert to MemoryRecord
        records: list[MemoryRecord] = []
        for entry in candidates:
            if isinstance(entry, dict):
                ctx = entry.get("context") or {}
            else:
                ctx = entry.context or {}
            if agent_id and ctx.get("agent_id") != agent_id:
                continue
            if session_id and ctx.get("session_id") != session_id:
                continue
            if user_id and ctx.get("user_id") != user_id:
                continue
            if kind and ctx.get("kind") != kind.value:
                continue
            records.append(
                self._dict_to_record(entry) if isinstance(entry, dict) else self._entry_to_record(entry)
            )
            if len(records) >= limit:
                break
        return records

    def _fallback_text_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Text scan scoped to THIS bridge's entries via bridge_id → entry lookup."""
        q = query.lower()
        scored: list[tuple[float, dict[str, Any], str, str]] = []
        for bridge_id, entry in self._id_map.items():
            ctx = entry.context or {} if hasattr(entry, "context") else {}
            goal = getattr(entry, "goal", "") or ""
            if q and q not in goal.lower():
                continue
            score = len(goal) / (len(goal) + len(query)) if query else 1.0
            scored.append((score, ctx, bridge_id, goal))
        scored.sort(key=lambda x: -x[0])
        return [{"context": ctx, "bridge_id": bid, "goal": goal} for _, ctx, bid, goal in scored[:top_k]]

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
            records.append(self._entry_to_record(entry))
            if len(records) >= limit:
                break
        return records

    def delete(self, key: str) -> bool:
        """Delete by bridge_id via reverse lookup."""
        removed = key in self._id_map
        self._id_map.pop(key, None)
        # Best-effort removal from underlying store; ignore if not supported
        return removed

    def stats(self) -> dict[str, Any]:
        try:
            raw = self._store.stats()
        except Exception:
            raw = {}
        return {"count": len(self._id_map), "backend": "memory_store", **raw}

    def prune_expired(self) -> int:
        """Delegate to MemoryStore.compress_old_memories()."""
        return self._store.compress_old_memories()

    # --- Helpers ---

    @staticmethod
    def _dict_to_record(d: dict[str, Any]) -> MemoryRecord:
        """Build MemoryRecord from a plain dict (e.g. fallback text search result)."""
        ctx = d.get("context") or {}
        kind_str = ctx.get("kind", "episodic")
        try:
            kind = MemoryKind(kind_str)
        except ValueError:
            kind = MemoryKind.EPISODIC
        return MemoryRecord(
            content=d.get("goal", "") or ctx.get("goal", ""),
            kind=kind,
            metadata=ctx,
            agent_id=ctx.get("agent_id"),
            session_id=ctx.get("session_id"),
            user_id=ctx.get("user_id"),
        )

    @staticmethod
    def _make_id(item: MemoryRecord) -> str:
        raw = f"{item.agent_id}:{item.content[:50]}:{item.created_at}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def _entry_to_record(entry: Any) -> MemoryRecord:
        ctx = entry.context or {}
        kind_str = ctx.get("kind", "episodic")
        try:
            kind = MemoryKind(kind_str)
        except ValueError:
            kind = MemoryKind.EPISODIC
        created = getattr(entry, "timestamp", 0.0) or 0.0
        return MemoryRecord(
            content=entry.goal,
            kind=kind,
            metadata={k: v for k, v in ctx.items()
                      if k not in ("kind", "agent_id", "session_id", "user_id", "bridge_id")},
            agent_id=ctx.get("agent_id"),
            session_id=ctx.get("session_id"),
            user_id=ctx.get("user_id"),
            created_at=created,
        )

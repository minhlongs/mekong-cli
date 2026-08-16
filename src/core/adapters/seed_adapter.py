# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps SeedMemory to implement MemoryBridge."""

from __future__ import annotations

from typing import Any

from src.core.memory_bridge import (  # noqa: F401 — Protocol used in isinstance checks
    MemoryBridge,
    MemoryKind,
    MemoryRecord,
)


class SeedBridge:
    """Wraps SeedMemory (SQLite) to satisfy MemoryBridge protocol."""

    def __init__(self, path: str | None = None) -> None:
        from src.seed.memory import SeedMemory

        self._db = SeedMemory(path=path)

    # --- MemoryBridge interface ---

    def record(self, item: MemoryRecord) -> str:
        """Persist via SeedMemory.remember(), returns generated doc_id."""
        meta: dict[str, Any] = dict(item.metadata)
        meta["kind"] = item.kind.value
        meta["session_id"] = item.session_id
        meta["user_id"] = item.user_id
        if item.ttl_seconds:
            meta["ttl_seconds"] = item.ttl_seconds
        meta["expires_at"] = item.expires_at
        meta["created_at"] = item.created_at
        return self._db.remember(
            agent_id=item.agent_id or "system",
            content=item.content,
            metadata=meta,
        )

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
        results = self._db.recall(query, limit=limit)
        records: list[MemoryRecord] = []
        for r in results:
            if agent_id and r.get("agent_id") != agent_id:
                continue
            meta = r.get("metadata") or {}
            if kind and meta.get("kind") != kind.value:
                continue
            if session_id and meta.get("session_id") != session_id:
                continue
            if user_id and meta.get("user_id") != user_id:
                continue
            records.append(self._dict_to_record(r))
        return records

    def recall(
        self,
        query: str,
        *,
        k: int = 5,
        agent_id: str | None = None,
    ) -> list[dict]:
        results = self._db.recall(query, limit=k)
        if agent_id:
            results = [r for r in results if r.get("agent_id") == agent_id]
        return results

    def recent(
        self,
        *,
        agent_id: str | None = None,
        limit: int = 20,
        kind: MemoryKind | None = None,
    ) -> list[MemoryRecord]:
        """Return most recent entries across all agents."""
        results = self._db.recall("", limit=limit * 4)
        records: list[MemoryRecord] = []
        for r in results:
            if kind:
                meta = r.get("metadata") or {}
                if meta.get("kind") != kind.value:
                    continue
            if agent_id and r.get("agent_id") != agent_id:
                continue
            records.append(self._dict_to_record(r))
            if len(records) >= limit:
                break
        return records

    def delete(self, key: str) -> bool:
        """Delete doc by doc_id via SeedMemory's clear_agent_memory fallback.

        SeedMemory has no per-key delete, so we match the doc_id stored
        in the metadata (or content match as fallback).
        """
        try:
            conn = self._db._conn_ref()
        except Exception:
            return False
        row = conn.execute(
            "SELECT doc_id FROM memories WHERE doc_id = ? OR content LIKE ?",
            (key, f"%{key}%"),
        ).fetchone()
        if not row:
            return False
        try:
            conn.execute("DELETE FROM memories WHERE doc_id = ?", (key,))
            conn.commit()
            return True
        except Exception:
            return False

    def stats(self) -> dict[str, Any]:
        """Return count across all agents (no hardcoded agent_id filter)."""
        total = 0
        try:
            conn = self._db._conn_ref()
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM memories"
            ).fetchall()
            r = row[0] if row else {}
            total = r["cnt"] if r else 0
        except Exception:
            pass
        return {"count": total, "backend": "seed"}

    def prune_expired(self) -> int:
        """SeedMemory has no TTL pruning — no-op."""
        return 0

    # --- Helpers ---

    @staticmethod
    def _dict_to_record(r: dict[str, Any]) -> MemoryRecord:
        meta = r.get("metadata") or {}
        kind_str = meta.get("kind", "episodic")
        try:
            kind = MemoryKind(kind_str)
        except ValueError:
            kind = MemoryKind.EPISODIC
        return MemoryRecord(
            content=r.get("content", ""),
            kind=kind,
            metadata=meta,
            created_at=r.get("created_at", 0.0),
            agent_id=r.get("agent_id"),
            session_id=meta.get("session_id"),
            user_id=meta.get("user_id"),
        )

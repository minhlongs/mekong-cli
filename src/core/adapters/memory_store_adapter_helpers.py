# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helper transformations and search utilities for MemoryStoreBridge."""

from __future__ import annotations

import hashlib
from typing import Any

from src.core.memory_bridge import MemoryKind, MemoryRecord


def make_id(item: MemoryRecord) -> str:
    """Generate deterministic hash key for MemoryRecord."""
    raw = f"{item.agent_id}:{item.content[:50]}:{item.created_at}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def dict_to_record(d: dict[str, Any]) -> MemoryRecord:
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


def entry_to_record(entry: Any) -> MemoryRecord:
    """Convert a MemoryStore Entry into a standardized MemoryRecord."""
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
        metadata={
            k: v
            for k, v in ctx.items()
            if k not in ("kind", "agent_id", "session_id", "user_id", "bridge_id")
        },
        agent_id=ctx.get("agent_id"),
        session_id=ctx.get("session_id"),
        user_id=ctx.get("user_id"),
        created_at=created,
    )


def fallback_text_search(
    id_map: dict[str, Any], query: str, top_k: int
) -> list[dict[str, Any]]:
    """Text scan scoped to entries registered in the bridge's id_map."""
    q = query.lower()
    scored: list[tuple[float, dict[str, Any], str, str]] = []
    for bridge_id, entry in id_map.items():
        ctx = entry.context or {} if hasattr(entry, "context") else {}
        goal = getattr(entry, "goal", "") or ""
        if q and q not in goal.lower():
            continue
        score = len(goal) / (len(goal) + len(query)) if query else 1.0
        scored.append((score, ctx, bridge_id, goal))
    scored.sort(key=lambda x: -x[0])
    return [
        {"context": ctx, "bridge_id": bid, "goal": goal}
        for _, ctx, bid, goal in scored[:top_k]
    ]


__all__ = [
    "make_id",
    "dict_to_record",
    "entry_to_record",
    "fallback_text_search",
]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helper functions and transformations for ScopedBridge."""

from __future__ import annotations

import hashlib
from typing import Any

from src.core.memory_bridge import MemoryKind, MemoryRecord


def make_key(item: MemoryRecord) -> str:
    """Generate deterministic hash key for MemoryRecord."""
    raw = f"{item.agent_id}:{item.content[:50]}:{item.created_at}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_scope(
    *,
    item: MemoryRecord | None = None,
    agent_id: str | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
) -> Any:
    """Construct a MemoryScope from a record or explicit filter arguments."""
    from src.core.memory_scope import MemoryScope

    if item is not None:
        return MemoryScope(
            agent_id=item.agent_id,
            session_id=item.session_id,
            user_id=item.user_id,
        )
    return MemoryScope(
        agent_id=agent_id,
        session_id=session_id,
        user_id=user_id,
    )


def dict_to_record(r: dict[str, Any]) -> MemoryRecord:
    """Transform dictionary representation to MemoryRecord instance."""
    value = r.get("value", r)
    if isinstance(value, dict):
        content = value.get("content", "")
        kind_str = value.get("kind", "episodic")
        metadata = value.get("metadata", {})
        agent_id = value.get("agent_id")
        session_id = value.get("session_id")
        user_id = value.get("user_id")
    else:
        content = str(value)
        kind_str = "episodic"
        metadata = {}
        agent_id = None
        session_id = None
        user_id = None
    try:
        kind = MemoryKind(kind_str)
    except ValueError:
        kind = MemoryKind.EPISODIC
    return MemoryRecord(
        content=content,
        kind=kind,
        metadata=metadata,
        created_at=r.get("created_at", 0.0),
        agent_id=agent_id,
        session_id=session_id,
        user_id=user_id,
    )


__all__ = ["make_key", "make_scope", "dict_to_record"]

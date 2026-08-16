# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unified memory interface for all 7 memory modules.

Wave B4: Memory Bridge
- Provides MemoryBridge protocol as superset of MemoryBackend
- All existing memory modules remain untouched (read-only after this)
- Adapters in src/core/adapters/ wrap originals to implement bridge
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class MemoryKind(str, Enum):
    """Category of memory entry."""
    EPISODIC = "episodic" # Task execution history
    SEMANTIC = "semantic" # Learned facts/knowledge
    PROCEDURAL = "procedural" # Skills/recipes/patterns
    WORKING = "working" # Session-scoped, ephemeral


@dataclass(frozen=True)
class MemoryRecord:
    """Unified memory record. Superset of MemoryRecord from backends.py."""
    content: str
    kind: MemoryKind = MemoryKind.EPISODIC
    metadata: dict[str, Any] = field(default_factory=dict)
    # Scope dimensions
    agent_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    # TTL support
    ttl_seconds: int | None = None
    expires_at: float | None = None # Unix ts; computed from ttl_seconds
    # Provenance
    created_at: float = field(
        default_factory=lambda: datetime.now(timezone.utc).timestamp()
    )


@runtime_checkable
class MemoryBridge(Protocol):
    """Unified memory interface.

    Superset of the existing MemoryBackend protocol.
    All 7 existing memory modules are wrapped by adapters that implement this.
    """

    def record(self, item: MemoryRecord) -> str:
        """Persist a memory record. Returns the assigned ID."""
        ...

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
        """Semantic or keyword search with optional scope filtering."""
        ...

    def recall(
        self,
        query: str,
        *,
        k: int = 5,
        agent_id: str | None = None,
    ) -> list[dict]:
        """Key-based/query recall. Returns raw dicts for backward compat."""
        ...

    def recent(
        self,
        *,
        agent_id: str | None = None,
        limit: int = 20,
        kind: MemoryKind | None = None,
    ) -> list[MemoryRecord]:
        """Return most recent entries, optionally filtered."""
        ...

    def delete(self, key: str) -> bool:
        """Remove entry by key. Returns True if found and removed."""
        ...

    def stats(self) -> dict[str, Any]:
        """Aggregate statistics: counts by kind, agent, recent activity."""
        ...

    def prune_expired(self) -> int:
        """Remove all TTL-expired entries. Returns count removed."""
        ...


def get_bridge(backend: str = "seed") -> MemoryBridge:
    """Factory: return a MemoryBridge wrapped around the requested backend.

    backends:
    "seed" → src/core/adapters/seed_adapter.SeedBridge
    "memory" → src/core/adapters/memory_store_adapter.MemoryStoreBridge
    "scoped" → src/core/adapters/scoped_adapter.ScopedBridge
    "pev" → src/core/adapters/pev_adapter.PevBridge

    Lazy-imported to avoid circular deps at module load time.
    """
    if backend == "seed":
        from src.core.adapters.seed_adapter import SeedBridge
        import os
        import tempfile
        import time
        db_path = os.path.join(
            tempfile.gettempdir(),
            f"seed_mem_{os.getpid()}_{time.monotonic_ns()}.db",
        )
        return SeedBridge(path=db_path)
    if backend in ("memory", "memory_store"):
        from src.core.adapters.memory_store_adapter import MemoryStoreBridge
        return MemoryStoreBridge()
    if backend == "scoped":
        from src.core.adapters.scoped_adapter import ScopedBridge
        return ScopedBridge()
    if backend == "pev":
        from src.core.adapters.pev_adapter import PevBridge
        return PevBridge()
    raise ValueError(f"Unknown memory backend: {backend!r}")

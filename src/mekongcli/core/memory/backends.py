"""Memory backend interfaces for future Redis/Postgres/Qdrant/Neo4j adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MemoryRecord:
    goal_id: str
    kind: str
    content: str


class MemoryBackend(Protocol):
    def record(self, item: MemoryRecord) -> None:
        """Persist a memory record."""

    def search(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        """Search prior memory records."""

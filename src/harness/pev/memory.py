"""Stub: memory store for PEV orchestrator."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime, timezone

@dataclass
class MemoryEntry:
    key: str
    value: Any
    layer: str = "engineering"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MemoryStore:
    def __init__(self) -> None:
        self._store: Dict[str, MemoryEntry] = {}

    def store(self, key: str, value: Any, layer: str = "engineering") -> MemoryEntry:
        entry = MemoryEntry(key=key, value=value, layer=layer)
        self._store[key] = entry
        return entry

    def recall(self, key: str) -> Optional[MemoryEntry]:
        return self._store.get(key)

    def forget(self, key: str) -> None:
        self._store.pop(key, None)

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Memory tier separation layer."""

from enum import Enum
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MemoryTier(str, Enum):
    """Memory tier for separation of short-term vs long-term storage."""
    SESSION = "session"
    PERSISTENT = "persistent"
    ARCHIVE = "archive"


_TIER_TTL: dict[MemoryTier, int] = {
    MemoryTier.SESSION: 3600,
    MemoryTier.PERSISTENT: 86400 * 30,
    MemoryTier.ARCHIVE: 86400 * 365,
}

_TIER_PREFIX = "tier::"
_MEKONG_APP_ID = "mekong"


class MemorySeparation:
    """Memory separation layer using ScopedMemoryStore as backend."""

    def __init__(self, store: Any = None) -> None:
        if store is None:
            from src.core.memory_scope import ScopedMemoryStore
            self._store = ScopedMemoryStore()
        else:
            self._store = store

    @staticmethod
    def _composite_key(tier: MemoryTier, key: str) -> str:
        return f"{_TIER_PREFIX}{tier.value}::{key}"

    @staticmethod
    def _parse_tier_from_key(composite: str) -> tuple[Optional[MemoryTier], str]:
        if not composite.startswith(_TIER_PREFIX):
            return None, composite
        parts = composite[len(_TIER_PREFIX):].split("::", 1)
        if len(parts) == 2:
            try:
                return MemoryTier(parts[0]), parts[1]
            except ValueError:
                return None, composite
        return None, composite

    @staticmethod
    def _mekong_scope():
        from src.core.memory_scope import MemoryScope
        return MemoryScope(app_id=_MEKONG_APP_ID)

    def store(self, key: str, value: bytes, tier: MemoryTier = MemoryTier.PERSISTENT, ttl: Optional[int] = None) -> None:
        """Store a value with tier-based TTL."""
        from src.core.memory_scope import ScopedMemoryEntry
        entry = ScopedMemoryEntry(
            key=self._composite_key(tier, key), value=value,
            scope=self._mekong_scope(), ttl=ttl if ttl is not None else _TIER_TTL[tier],
        )
        self._store.store(entry)

    def store_raw(self, key: str, value: bytes, ttl: int | None = None) -> None:
        """Store a value on the canonical backend without tier tagging."""
        from src.core.memory_scope import ScopedMemoryEntry
        self._store.store(ScopedMemoryEntry(key=key, value=value, scope=self._mekong_scope(), ttl=ttl))

    def retrieve(self, key: str, tier: MemoryTier = MemoryTier.PERSISTENT) -> Optional[bytes]:
        """Retrieve a value by key within a tier."""
        entry = self._store.retrieve(self._composite_key(tier, key), self._mekong_scope())
        return entry.value if entry is not None else None

    def delete(self, key: str) -> bool:
        """Delete a value across all tiers."""
        scope = self._mekong_scope()
        for entry in self._store.query(scope):
            _, user_key = self._parse_tier_from_key(entry.key)
            if user_key == key:
                return self._store.delete(entry.key, scope)
        return False

    def search(self, query: str, limit: int = 10, tier: Optional[MemoryTier] = None) -> list[dict[str, Any]]:
        """Search entries by query string."""
        scope = self._mekong_scope()
        results: list[dict[str, Any]] = []
        q = query.lower()
        for entry in self._store.query(scope):
            entry_tier, user_key = self._parse_tier_from_key(entry.key)
            if tier is not None and entry_tier != tier:
                continue
            key_match = q in user_key.lower()
            val_str = entry.value.decode("utf-8", errors="ignore") if isinstance(entry.value, bytes) else (entry.value if isinstance(entry.value, str) else "")
            if key_match or q in val_str.lower():
                results.append({"key": user_key, "value": entry.value, "tier": entry_tier.value if entry_tier else "persistent", "timestamp": entry.created_at})
                if len(results) >= limit:
                    break
        return results

    def flush_session(self) -> int:
        """Delete all SESSION-tier entries and prune expired entries."""
        scope = self._mekong_scope()
        deleted = 0
        for entry in self._store.query(scope):
            entry_tier, _ = self._parse_tier_from_key(entry.key)
            if entry_tier == MemoryTier.SESSION:
                self._store.delete(entry.key, scope)
                deleted += 1
        self.prune_expired()
        return deleted

    def prune_expired(self) -> int:
        return int(self._store.prune_expired()) if hasattr(self._store, "prune_expired") else 0

    def list_by_tier(self, tier: MemoryTier) -> list[str]:
        return [
            user_key for entry in self._store.query(self._mekong_scope())
            for entry_tier, user_key in [self._parse_tier_from_key(entry.key)]
            if entry_tier == tier
        ]


__all__ = ["MemorySeparation", "MemoryTier"]

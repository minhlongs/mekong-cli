# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - LLM Response Cache.

Portkey-inspired caching layer for LLM responses.
Simple hash-based cache with TTL support and hit rate tracking.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import Any

from .llm_cache_models import CacheEntry, CacheStats

logger = logging.getLogger(__name__)


class LLMCache:
    """LRU cache for LLM responses with TTL and stats tracking.

    Uses ordered dict for O(1) LRU eviction.
    Cache key is SHA-256 hash of (messages + model + temperature).
    """

    def __init__(
        self,
        max_entries: int = 1000,
        default_ttl: int = 3600,
        cost_per_hit: float = 0.001,
    ) -> None:
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cost_per_hit = cost_per_hit
        self.stats = CacheStats()

    @staticmethod
    def _make_key(
        messages: list[dict[str, str]],
        model: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate deterministic cache key from request params."""
        payload = json.dumps(
            {
                "messages": messages,
                "model": model,
                "temperature": temperature,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        temperature: float = 0.7,
    ) -> CacheEntry | None:
        """Look up cached response for given request."""
        key = self._make_key(messages, model, temperature)
        if key not in self._cache:
            self.stats.misses += 1
            return None

        entry = self._cache[key]
        if entry.is_expired:
            del self._cache[key]
            self.stats.misses += 1
            self.stats.total_entries = len(self._cache)
            return None

        self._cache.move_to_end(key)
        entry.hit_count += 1
        self.stats.hits += 1
        self.stats.estimated_cost_saved += self.cost_per_hit
        logger.debug(f"[Cache] HIT key={key[:12]}... model={model}")
        return entry

    def put(
        self,
        messages: list[dict[str, str]],
        content: str,
        model: str = "",
        temperature: float = 0.7,
        usage: dict[str, int] | None = None,
        ttl: int | None = None,
    ) -> str:
        """Store LLM response in cache."""
        key = self._make_key(messages, model, temperature)
        while len(self._cache) >= self.max_entries:
            evicted_key, _ = self._cache.popitem(last=False)
            self.stats.evictions += 1
            logger.debug(f"[Cache] EVICT key={evicted_key[:12]}...")

        entry = CacheEntry(
            key=key,
            content=content,
            model=model,
            usage=usage or {},
            created_at=time.time(),
            ttl=ttl if ttl is not None else self.default_ttl,
        )
        self._cache[key] = entry
        self.stats.total_entries = len(self._cache)
        logger.debug(f"[Cache] PUT key={key[:12]}... model={model} ttl={entry.ttl}s")
        return key

    def invalidate(self, key: str) -> bool:
        """Remove a specific entry from cache."""
        if key in self._cache:
            del self._cache[key]
            self.stats.total_entries = len(self._cache)
            return True
        return False

    def clear(self) -> int:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self.stats.total_entries = 0
        return count

    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            del self._cache[key]
        self.stats.total_entries = len(self._cache)
        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """Return cache performance summary."""
        return {
            "hit_rate": round(self.stats.hit_rate, 1),
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "evictions": self.stats.evictions,
            "total_entries": self.stats.total_entries,
            "max_entries": self.max_entries,
            "estimated_cost_saved_usd": round(self.stats.estimated_cost_saved, 4),
        }


__all__ = [
    "CacheEntry",
    "CacheStats",
    "LLMCache",
]

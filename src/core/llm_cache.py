# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - LLM Response Cache."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cached LLM response."""
    key: str
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    created_at: float = 0.0
    ttl: int = 3600
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        if self.ttl <= 0:
            return False
        return (time.time() - self.created_at) > self.ttl


@dataclass
class CacheStats:
    """Aggregate cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    estimated_cost_saved: float = 0.0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) * 100 if total > 0 else 0.0


class LLMCache:
    """LRU cache for LLM responses with TTL and stats tracking."""

    def __init__(self, max_entries: int = 1000, default_ttl: int = 3600, cost_per_hit: float = 0.001) -> None:
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cost_per_hit = cost_per_hit
        self.stats = CacheStats()

    @staticmethod
    def _make_key(messages: list[dict[str, str]], model: str = "", temperature: float = 0.7) -> str:
        payload = json.dumps({"messages": messages, "model": model, "temperature": temperature}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, messages: list[dict[str, str]], model: str = "", temperature: float = 0.7) -> CacheEntry | None:
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
        self, messages: list[dict[str, str]], content: str, model: str = "",
        temperature: float = 0.7, usage: dict[str, int] | None = None, ttl: int | None = None,
    ) -> str:
        key = self._make_key(messages, model, temperature)
        while len(self._cache) >= self.max_entries:
            evicted_key, _ = self._cache.popitem(last=False)
            self.stats.evictions += 1
            logger.debug(f"[Cache] EVICT key={evicted_key[:12]}...")

        entry = CacheEntry(
            key=key, content=content, model=model, usage=usage or {},
            created_at=time.time(), ttl=ttl if ttl is not None else self.default_ttl,
        )
        self._cache[key] = entry
        self.stats.total_entries = len(self._cache)
        logger.debug(f"[Cache] PUT key={key[:12]}... model={model} ttl={entry.ttl}s")
        return key

    def invalidate(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            self.stats.total_entries = len(self._cache)
            return True
        return False

    def clear(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        self.stats.total_entries = 0
        return count

    def cleanup_expired(self) -> int:
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            del self._cache[key]
        self.stats.total_entries = len(self._cache)
        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        return {
            "hit_rate": round(self.stats.hit_rate, 1),
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "evictions": self.stats.evictions,
            "total_entries": self.stats.total_entries,
            "max_entries": self.max_entries,
            "estimated_cost_saved_usd": round(self.stats.estimated_cost_saved, 4),
        }


__all__ = ["CacheEntry", "CacheStats", "LLMCache"]

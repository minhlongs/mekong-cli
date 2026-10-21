# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models for LLM Response Cache."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


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
        """Check if entry has exceeded its TTL."""
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
        """Calculate hit rate percentage."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

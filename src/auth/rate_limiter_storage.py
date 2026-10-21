# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate Limiter Storage — TokenBucket and InMemoryRateStorage."""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class RateLimitPreset(str, Enum):
    """Predefined rate limit presets for common use cases."""

    AUTH_LOGIN = "auth_login"
    AUTH_CALLBACK = "auth_callback"
    AUTH_REFRESH = "auth_refresh"
    AUTH_DEV_LOGIN = "auth_dev_login"

    API_DEFAULT = "api_default"
    API_WRITE = "api_write"
    API_READ = "api_read"


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit rule."""

    limit: int
    window: int

    @property
    def refill_rate(self) -> float:
        """Calculate tokens per second refill rate."""
        return self.limit / self.window


DEFAULT_RATE_LIMITS: Dict[RateLimitPreset, RateLimitConfig] = {
    RateLimitPreset.AUTH_LOGIN: RateLimitConfig(limit=5, window=60),
    RateLimitPreset.AUTH_CALLBACK: RateLimitConfig(limit=10, window=60),
    RateLimitPreset.AUTH_REFRESH: RateLimitConfig(limit=30, window=3600),
    RateLimitPreset.AUTH_DEV_LOGIN: RateLimitConfig(limit=10, window=60),
    RateLimitPreset.API_DEFAULT: RateLimitConfig(limit=100, window=60),
    RateLimitPreset.API_WRITE: RateLimitConfig(limit=20, window=60),
    RateLimitPreset.API_READ: RateLimitConfig(limit=200, window=60),
}


class TokenBucket:
    """Token bucket rate limiter for per-key throttling."""

    def __init__(self, capacity: float, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time since last update."""
        now = time.monotonic()
        elapsed = now - self.last_update
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_update = now

    def _refill_with_time(self, current_time: float) -> None:
        """Refill tokens using provided time (for testing)."""
        elapsed = current_time - self.last_update
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_update = current_time

    async def consume(self, tokens: float = 1) -> bool:
        """Try to consume tokens from the bucket."""
        async with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_time(self, tokens: float = 1) -> float:
        """Calculate seconds until requested tokens are available."""
        async with self._lock:
            self._refill()
            if self.tokens >= tokens:
                return 0.0
            tokens_needed = tokens - self.tokens
            return tokens_needed / self.refill_rate

    @property
    def remaining(self) -> int:
        """Get remaining tokens (rounded down)."""
        return int(self.tokens)

    def reset(self) -> None:
        """Reset bucket to full capacity."""
        self.tokens = self.capacity
        self.last_update = time.monotonic()


@dataclass
class BucketEntry:
    """Entry for storing a token bucket with metadata."""

    bucket: TokenBucket
    last_access: float = field(default_factory=time.time)
    key: str = ""


class InMemoryRateStorage:
    """Thread-safe in-memory storage for per-key rate limiting."""

    def __init__(
        self,
        ttl_seconds: float = 3600,
        cleanup_interval: float = 300,
    ) -> None:
        self._buckets: Dict[str, BucketEntry] = {}
        self._ttl_seconds = ttl_seconds
        self._cleanup_interval = cleanup_interval
        self._lock = asyncio.Lock()

    async def get_bucket(
        self,
        key: str,
        config: RateLimitConfig,
    ) -> TokenBucket:
        """Get or create a token bucket for a key."""
        async with self._lock:
            entry = self._buckets.get(key)
            if entry is None:
                bucket = TokenBucket(
                    capacity=config.limit,
                    refill_rate=config.refill_rate,
                )
                entry = BucketEntry(bucket=bucket, key=key)
                self._buckets[key] = entry
            else:
                entry.last_access = time.time()
            return entry.bucket

    async def cleanup(self, max_age: Optional[float] = None) -> int:
        """Remove stale bucket entries."""
        async with self._lock:
            now = time.time()
            ttl = max_age if max_age is not None else self._ttl_seconds
            stale_keys = [
                key for key, entry in self._buckets.items()
                if now - entry.last_access > ttl
            ]
            for key in stale_keys:
                del self._buckets[key]
            return len(stale_keys)

    async def get_stats(self) -> Dict:
        """Get storage statistics."""
        async with self._lock:
            now = time.time()
            ages = [
                now - entry.last_access
                for entry in self._buckets.values()
            ]
            return {
                "active_buckets": len(self._buckets),
                "oldest_entry_age": max(ages) if ages else 0,
                "total_capacity": sum(
                    entry.bucket.capacity
                    for entry in self._buckets.values()
                ),
            }

    async def clear(self) -> None:
        """Clear all stored buckets."""
        async with self._lock:
            self._buckets.clear()

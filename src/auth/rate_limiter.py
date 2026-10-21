# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate Limiter — Token bucket algorithm for per-IP rate limiting with persistence."""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.auth.rate_limiter_storage import (
    DEFAULT_RATE_LIMITS,
    BucketEntry,
    InMemoryRateStorage,
    RateLimitConfig,
    RateLimitPreset,
    TokenBucket,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Global rate limiter manager with per-key tracking."""

    def __init__(self, storage: Optional[InMemoryRateStorage] = None) -> None:
        self._storage = storage or InMemoryRateStorage()
        self._presets = DEFAULT_RATE_LIMITS.copy()

    async def check_limit(
        self,
        key: str,
        preset: RateLimitPreset = RateLimitPreset.API_DEFAULT,
        tokens: float = 1,
    ) -> Tuple[bool, Dict[str, str]]:
        """Check rate limit and consume token if allowed."""
        config = self._presets.get(preset, DEFAULT_RATE_LIMITS[RateLimitPreset.API_DEFAULT])
        bucket = await self._storage.get_bucket(key, config)
        allowed = await bucket.consume(tokens)
        headers = {
            "X-RateLimit-Limit": str(config.limit),
            "X-RateLimit-Remaining": str(max(0, bucket.remaining)),
            "X-RateLimit-Reset": str(int(time.time() + config.window)),
        }
        if not allowed:
            wait = await bucket.wait_time(tokens)
            headers["Retry-After"] = str(int(wait) + 1)
        return allowed, headers

    async def get_remaining(self, key: str, preset: RateLimitPreset) -> int:
        """Get remaining tokens for a key without consuming."""
        config = self._presets.get(preset, DEFAULT_RATE_LIMITS[RateLimitPreset.API_DEFAULT])
        bucket = await self._storage.get_bucket(key, config)
        return bucket.remaining

    async def get_reset_time(self, key: str, preset: RateLimitPreset) -> float:
        """Get reset timestamp for a key."""
        config = self._presets.get(preset, DEFAULT_RATE_LIMITS[RateLimitPreset.API_DEFAULT])
        bucket = await self._storage.get_bucket(key, config)
        tokens_needed = bucket.capacity - bucket.tokens
        if tokens_needed <= 0:
            return time.time()
        return time.time() + (tokens_needed / config.refill_rate)

    async def cleanup(self) -> int:
        """Remove stale rate limit entries."""
        return await self._storage.cleanup()

    async def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        stats = await self._storage.get_stats()
        stats["presets"] = {
            (preset.value if hasattr(preset, "value") else str(preset)): {
                "limit": cfg.limit,
                "window": cfg.window,
            }
            for preset, cfg in self._presets.items()
        }
        return stats

    def register_preset(self, name: str, limit: int, window: int) -> None:
        """Register a custom rate limit preset."""
        self._presets[name] = RateLimitConfig(limit=limit, window=window)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.message = message
        self.headers = headers or {}
        self.retry_after = int(self.headers.get("Retry-After", 60))
        super().__init__(self.message)


_PERSIST_PATH = Path.home() / ".mekong" / "rate_limiter_state.json"


def _load_persisted_state() -> Optional[InMemoryRateStorage]:
    """Load persisted rate limiter state from disk."""
    if not _PERSIST_PATH.exists():
        return None
    try:
        data = json.loads(_PERSIST_PATH.read_text())
        storage = InMemoryRateStorage()
        for entry_data in data.get("buckets", []):
            bucket = TokenBucket(
                capacity=entry_data["capacity"],
                refill_rate=entry_data["refill_rate"],
            )
            bucket.tokens = entry_data["tokens"]
            bucket.last_update = entry_data["last_update"]
            bucket_entry = BucketEntry(
                bucket=bucket,
                last_access=entry_data.get("last_access", time.time()),
                key=entry_data["key"],
            )
            storage._buckets[entry_data["key"]] = bucket_entry  # type: ignore[attr-defined]
        return storage
    except Exception as exc:
        logger.warning("Failed to load rate limiter state: %s", exc)
        return None


def _persist_state() -> None:
    """Persist current rate limiter state to disk for recovery after restart."""
    global _rate_limiter
    if _rate_limiter is None:
        return
    try:
        _PERSIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        buckets_data = [
            {
                "key": entry.key,
                "capacity": entry.bucket.capacity,
                "refill_rate": entry.bucket.refill_rate,
                "tokens": entry.bucket.tokens,
                "last_update": entry.bucket.last_update,
                "last_access": entry.last_access,
            }
            for entry in _rate_limiter._storage._buckets.values()  # type: ignore[attr-defined]
        ]
        _PERSIST_PATH.write_text(json.dumps({"buckets": buckets_data}, indent=2))
    except Exception as exc:
        logger.warning("Failed to persist rate limiter state: %s", exc)


_rate_limiter: Optional["RateLimiter"] = None


def get_rate_limiter() -> "RateLimiter":
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        storage = _load_persisted_state()
        _rate_limiter = RateLimiter(storage=storage)
        if storage is None:
            logger.warning("No persisted rate limiter state found.")
    return _rate_limiter


async def init_rate_limiter(
    storage: Optional[InMemoryRateStorage] = None,
) -> "RateLimiter":
    """Initialize global rate limiter with custom storage."""
    global _rate_limiter
    _rate_limiter = RateLimiter(storage=storage)
    return _rate_limiter

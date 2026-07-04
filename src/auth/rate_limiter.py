"""Rate Limiter — Token bucket algorithm for per-IP rate limiting with persistence.

Provides thread-safe rate limiting with configurable limits per endpoint.
State is persisted to disk so rate limit counters survive process restarts.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitPreset(str, Enum):
    """Predefined rate limit presets for common use cases."""

    # Auth endpoints — strict limits to prevent brute-force
    AUTH_LOGIN = "auth_login"
    AUTH_CALLBACK = "auth_callback"
    AUTH_REFRESH = "auth_refresh"
    AUTH_DEV_LOGIN = "auth_dev_login"

    # API endpoints
    API_DEFAULT = "api_default"
    API_WRITE = "api_write"
    API_READ = "api_read"


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit rule.

    Attributes:
        limit: Maximum number of requests allowed.
        window: Time window in seconds.
    """
    limit: int
    window: int

    @property
    def refill_rate(self) -> float:
        """Calculate tokens per second refill rate."""
        return self.limit / self.window


# Default rate limit configurations
DEFAULT_RATE_LIMITS: Dict[RateLimitPreset, RateLimitConfig] = {
    RateLimitPreset.AUTH_LOGIN: RateLimitConfig(limit=5, window=60),       # 5/min
    RateLimitPreset.AUTH_CALLBACK: RateLimitConfig(limit=10, window=60),   # 10/min
    RateLimitPreset.AUTH_REFRESH: RateLimitConfig(limit=30, window=3600),  # 30/hour
    RateLimitPreset.AUTH_DEV_LOGIN: RateLimitConfig(limit=10, window=60),  # 10/min
    RateLimitPreset.API_DEFAULT: RateLimitConfig(limit=100, window=60),    # 100/min
    RateLimitPreset.API_WRITE: RateLimitConfig(limit=20, window=60),       # 20/min
    RateLimitPreset.API_READ: RateLimitConfig(limit=200, window=60),       # 200/min
}


class TokenBucket:
    """Token bucket rate limiter for per-key throttling.

    The token bucket algorithm allows bursts up to capacity, then enforces
    a steady rate. Tokens are consumed on each request and refilled over time.

    Attributes:
        capacity: Maximum tokens (burst limit).
        refill_rate: Tokens added per second.
        tokens: Current available tokens.
        last_update: Last refill timestamp (monotonic time).

    Example:
        >>> bucket = TokenBucket(capacity=10, refill_rate=1.0)
        >>> bucket.consume()      # True, consumes 1 token
        >>> bucket.consume(5)     # True if 5+ tokens available
        >>> bucket.consume(100)   # False, not enough tokens
    """

    def __init__(self, capacity: float, refill_rate: float) -> None:
        """Initialize token bucket.

        Args:
            capacity: Maximum number of tokens (burst limit).
            refill_rate: Number of tokens added per second.
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity  # Start full
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
        """Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume (default: 1).

        Returns:
            True if tokens were consumed, False if insufficient tokens.
        """
        async with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_time(self, tokens: float = 1) -> float:
        """Calculate seconds until requested tokens are available.

        Args:
            tokens: Number of tokens needed (default: 1).

        Returns:
            Seconds to wait, or 0 if tokens already available.
        """
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
    """Entry for storing a token bucket with metadata.

    Attributes:
        bucket: The token bucket instance.
        last_access: Last access timestamp (unix time).
        key: The rate limit key.
    """
    bucket: TokenBucket
    last_access: float = field(default_factory=time.time)
    key: str = ""


class InMemoryRateStorage:
    """Thread-safe in-memory storage for per-key rate limiting.

    Features:
    - Stores TokenBucket per unique key (e.g., IP:endpoint).
    - Automatic cleanup of stale entries.
    - Thread-safe async operations.
    - Configurable TTL for stale buckets.

    Attributes:
        ttl_seconds: Time-to-live for inactive buckets (default: 1 hour).
        cleanup_interval: Seconds between cleanup runs (default: 300).

    Example:
        >>> storage = InMemoryRateStorage()
        >>> bucket = await storage.get_bucket("192.168.1.1:/auth/login", config)
        >>> allowed = await bucket.consume()
        >>> await storage.cleanup()  # Remove stale entries
    """

    def __init__(
        self,
        ttl_seconds: float = 3600,
        cleanup_interval: float = 300,
    ) -> None:
        """Initialize in-memory storage.

        Args:
            ttl_seconds: Time-to-live for inactive buckets.
            cleanup_interval: Recommended interval for cleanup calls.
        """
        self._buckets: Dict[str, BucketEntry] = {}
        self._ttl_seconds = ttl_seconds
        self._cleanup_interval = cleanup_interval
        self._lock = asyncio.Lock()

    async def get_bucket(
        self,
        key: str,
        config: RateLimitConfig,
    ) -> TokenBucket:
        """Get or create a token bucket for a key.

        Args:
            key: Unique identifier (e.g., "ip:endpoint").
            config: Rate limit configuration for new buckets.

        Returns:
            TokenBucket for the key (existing or newly created).
        """
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
        """Remove stale bucket entries.

        Args:
            max_age: Override TTL for this cleanup (default: use configured TTL).

        Returns:
            Number of entries removed.
        """
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


class RateLimiter:
    """Global rate limiter manager with per-key tracking.

    Provides a high-level interface for rate limiting with:
    - Per-key token buckets.
    - Automatic cleanup of stale entries.
    - Rate limit headers generation.
    - Configurable presets.

    Attributes:
        storage: InMemoryRateStorage instance.
        presets: Dict of rate limit presets.

    Example:
        >>> limiter = RateLimiter()
        >>> allowed, headers = await limiter.check_limit(
        ...     key="192.168.1.1:/auth/login",
        ...     preset=RateLimitPreset.AUTH_LOGIN,
        ... )
    """

    def __init__(
        self,
        storage: Optional[InMemoryRateStorage] = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            storage: Optional custom storage (default: create new InMemoryRateStorage).
                     Use a persistent storage backend to survive restarts.
        """
        self._storage = storage or InMemoryRateStorage()
        self._presets = DEFAULT_RATE_LIMITS.copy()

    async def check_limit(
        self,
        key: str,
        preset: RateLimitPreset = RateLimitPreset.API_DEFAULT,
        tokens: float = 1,
    ) -> Tuple[bool, Dict[str, str]]:
        """Check rate limit and consume token if allowed.

        Args:
            key: Unique identifier (e.g., "ip:endpoint").
            preset: Rate limit preset to use.
            tokens: Number of tokens to consume (default: 1).

        Returns:
            Tuple of (allowed: bool, headers: Dict) where headers contains
            X-RateLimit-* headers for the response.
        """
        config = self._presets.get(
            preset, DEFAULT_RATE_LIMITS[RateLimitPreset.API_DEFAULT]
        )
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

    async def get_remaining(
        self,
        key: str,
        preset: RateLimitPreset,
    ) -> int:
        """Get remaining tokens for a key without consuming.

        Args:
            key: Unique identifier.
            preset: Rate limit preset.

        Returns:
            Number of remaining tokens.
        """
        config = self._presets.get(
            preset, DEFAULT_RATE_LIMITS[RateLimitPreset.API_DEFAULT]
        )
        bucket = await self._storage.get_bucket(key, config)
        return bucket.remaining

    async def get_reset_time(
        self,
        key: str,
        preset: RateLimitPreset,
    ) -> float:
        """Get reset timestamp for a key.

        Args:
            key: Unique identifier.
            preset: Rate limit preset.

        Returns:
            Unix timestamp when bucket will be full again.
        """
        config = self._presets.get(
            preset, DEFAULT_RATE_LIMITS[RateLimitPreset.API_DEFAULT]
        )
        bucket = await self._storage.get_bucket(key, config)
        tokens_needed = bucket.capacity - bucket.tokens
        if tokens_needed <= 0:
            return time.time()
        return time.time() + (tokens_needed / config.refill_rate)

    async def cleanup(self) -> int:
        """Remove stale rate limit entries.

        Returns:
            Number of entries removed.
        """
        return await self._storage.cleanup()

    async def get_stats(self) -> Dict:
        """Get rate limiter statistics.

        Returns:
            Dict with storage stats and configured presets.
        """
        stats = await self._storage.get_stats()
        stats["presets"] = {
            preset.value: {"limit": cfg.limit, "window": cfg.window}
            for preset, cfg in self._presets.items()
        }
        return stats

    def register_preset(
        self,
        name: str,
        limit: int,
        window: int,
    ) -> None:
        """Register a custom rate limit preset.

        Args:
            name: Preset name.
            limit: Maximum requests.
            window: Time window in seconds.
        """
        self._presets[name] = RateLimitConfig(limit=limit, window=window)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded.

    Attributes:
        message: Error message.
        retry_after: Seconds until retry is allowed.
        headers: HTTP headers for 429 response.

    Example:
        >>> try:
        ...     allowed, headers = await limiter.check_limit(key, preset)
        ...     if not allowed:
        ...         raise RateLimitExceeded(headers=headers)
        ... except RateLimitExceeded as e:
        ...     return JSONResponse(status_code=429, headers=e.headers)
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.message = message
        self.headers = headers or {}
        self.retry_after = int(self.headers.get("Retry-After", 60))
        super().__init__(self.message)


# ── State Persistence ────────────────────────────────────────────────────────

_PERSIST_PATH = Path.home() / ".mekong" / "rate_limiter_state.json"


def _load_persisted_state() -> Optional[InMemoryRateStorage]:
    """Load persisted rate limiter state from disk.

    Reads bucket state from a JSON file written by _persist_state().
    Returns None if no state file exists or on error.

    Returns:
        InMemoryRateStorage with restored buckets, or None if unavailable.
    """
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
    """Persist current rate limiter state to disk for recovery after restart.

    Best-effort — failures are logged but never raised.
    """
    global _rate_limiter
    if _rate_limiter is None:
        return
    try:
        _PERSIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        buckets_data = []
        for key, entry in _rate_limiter._storage._buckets.items():  # type: ignore[attr-defined]
            buckets_data.append({
                "key": entry.key,
                "capacity": entry.bucket.capacity,
                "refill_rate": entry.bucket.refill_rate,
                "tokens": entry.bucket.tokens,
                "last_update": entry.bucket.last_update,
                "last_access": entry.last_access,
            })
        _PERSIST_PATH.write_text(
            json.dumps({"buckets": buckets_data}, indent=2)
        )
    except Exception as exc:
        logger.warning("Failed to persist rate limiter state: %s", exc)


# ── Global Instance ──────────────────────────────────────────────────────────

_rate_limiter: Optional["RateLimiter"] = None


def get_rate_limiter() -> "RateLimiter":
    """Get or create global rate limiter instance.

    On first call, attempts to restore previously persisted state from disk.
    If no persisted state exists, starts with a fresh limiter and logs a warning.

    Returns:
        Global RateLimiter instance.
    """
    global _rate_limiter
    if _rate_limiter is None:
        storage = _load_persisted_state()
        _rate_limiter = RateLimiter(storage=storage)
        if storage is None:
            logger.warning(
                "No persisted rate limiter state found — "
                "all rate limit counters reset on restart. "
                "Pass a persistent storage backend to init_rate_limiter() "
                "to avoid state loss across restarts."
            )
    return _rate_limiter


async def init_rate_limiter(
    storage: Optional[InMemoryRateStorage] = None,
) -> "RateLimiter":
    """Initialize global rate limiter with custom storage.

    Args:
        storage: Optional custom storage instance (use SQLite-backed storage
                 for persistence across process restarts).

    Returns:
        Initialized RateLimiter instance.
    """
    global _rate_limiter
    _rate_limiter = RateLimiter(storage=storage)
    return _rate_limiter

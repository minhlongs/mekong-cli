"""Zalo OA Rate Limiter with Cloudflare KV backend."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from .models import RateLimitInfo


@dataclass
class KVNamespace:
    """Cloudflare KV namespace interface (compatible with Workers KV)."""

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        raise NotImplementedError

    async def put(self, key: str, value: str, expiration_ttl: Optional[int] = None) -> None:
        """Set key-value pair with optional TTL."""
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        """Delete key."""
        raise NotImplementedError


class InMemoryKV(KVNamespace):
    """In-memory KV implementation for development/testing."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float]] = {}  # key -> (value, expiry)

    async def get(self, key: str) -> Optional[str]:
        if key in self._store:
            value, expiry = self._store[key]
            if expiry == 0 or time.time() < expiry:
                return value
            else:
                del self._store[key]
        return None

    async def put(self, key: str, value: str, expiration_ttl: Optional[int] = None) -> None:
        expiry = time.time() + expiration_ttl if expiration_ttl else 0
        self._store[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class ZaloRateLimiter:
    """Rate limiter for Zalo OA API calls using sliding window."""

    def __init__(
        self,
        kv: KVNamespace,
        default_limit: int = 100,
        default_window_seconds: int = 60,
        key_prefix: str = "zalo:ratelimit:",
    ):
        """Initialize rate limiter.

        Args:
            kv: KV namespace for distributed rate limiting
            default_limit: Default requests per window
            default_window_seconds: Default window in seconds
            key_prefix: Prefix for KV keys
        """
        self.kv = kv
        self.default_limit = default_limit
        self.default_window_seconds = default_window_seconds
        self.key_prefix = key_prefix

    def _make_key(self, oa_id: str, window_start: int) -> str:
        """Generate KV key for rate limit window."""
        return f"{self.key_prefix}{oa_id}:{window_start}"

    async def check_limit(
        self,
        oa_id: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> tuple[bool, RateLimitInfo]:
        """Check if request is within rate limit.

        Args:
            oa_id: Zalo OA ID
            limit: Custom limit (overrides default)
            window_seconds: Custom window (overrides default)

        Returns:
            Tuple of (allowed, RateLimitInfo)
        """
        limit = limit or self.default_limit
        window_seconds = window_seconds or self.default_window_seconds

        now = time.time()
        window_start = int(now // window_seconds) * window_seconds
        key = self._make_key(oa_id, window_start)

        # Get current count
        current_str = await self.kv.get(key)
        current = int(current_str) if current_str else 0

        if current >= limit:
            # Limit exceeded
            reset_at = window_start + window_seconds
            return False, RateLimitInfo(
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                exceeded=True,
            )

        # Increment counter
        new_count = current + 1
        ttl = window_seconds + 10  # Add buffer for TTL
        await self.kv.put(key, str(new_count), expiration_ttl=ttl)

        remaining = limit - new_count
        reset_at = window_start + window_seconds

        return True, RateLimitInfo(
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            exceeded=False,
        )

    async def get_status(self, oa_id: str) -> RateLimitInfo:
        """Get current rate limit status without incrementing."""
        now = time.time()
        window_start = int(now // self.default_window_seconds) * self.default_window_seconds
        key = self._make_key(oa_id, window_start)

        current_str = await self.kv.get(key)
        current = int(current_str) if current_str else 0

        remaining = max(0, self.default_limit - current)
        reset_at = window_start + self.default_window_seconds

        return RateLimitInfo(
            limit=self.default_limit,
            remaining=remaining,
            reset_at=reset_at,
            exceeded=current >= self.default_limit,
        )

    async def reset_limit(self, oa_id: str) -> None:
        """Reset rate limit for an OA (admin operation)."""
        now = time.time()
        window_start = int(now // self.default_window_seconds) * self.default_window_seconds
        key = self._make_key(oa_id, window_start)
        await self.kv.delete(key)

    async def set_custom_limit(self, oa_id: str, limit: int, window_seconds: int) -> None:
        """Set custom limit for specific OA (stored in KV)."""
        config_key = f"{self.key_prefix}config:{oa_id}"
        import json
        config = {"limit": limit, "window_seconds": window_seconds}
        await self.kv.put(config_key, json.dumps(config))

    async def get_custom_limit(self, oa_id: str) -> tuple[int, int] | None:
        """Get custom limit for OA."""
        config_key = f"{self.key_prefix}config:{oa_id}"
        config_str = await self.kv.get(config_key)
        if config_str:
            import json
            config = json.loads(config_str)
            return config["limit"], config["window_seconds"]
        return None


class SlidingWindowRateLimiter(ZaloRateLimiter):
    """More accurate sliding window rate limiter using multiple sub-windows."""

    def __init__(
        self,
        kv: KVNamespace,
        default_limit: int = 100,
        default_window_seconds: int = 60,
        sub_windows: int = 6,
        key_prefix: str = "zalo:ratelimit:sw:",
    ):
        """Initialize sliding window rate limiter.

        Args:
            kv: KV namespace
            default_limit: Requests per window
            default_window_seconds: Window size
            sub_windows: Number of sub-windows for sliding calculation
            key_prefix: KV key prefix
        """
        super().__init__(kv, default_limit, default_window_seconds, key_prefix)
        self.sub_windows = sub_windows
        self.sub_window_size = default_window_seconds // sub_windows

    def _make_sub_key(self, oa_id: str, sub_window: int) -> str:
        return f"{self.key_prefix}{oa_id}:{sub_window}"

    async def check_limit(
        self,
        oa_id: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> tuple[bool, RateLimitInfo]:
        """Check limit using sliding window algorithm."""
        limit = limit or self.default_limit
        window_seconds = window_seconds or self.default_window_seconds

        now = time.time()
        current_sub = int(now // self.sub_window_size)

        # Sum counts from recent sub-windows
        total = 0
        for i in range(self.sub_windows):
            sub_window = current_sub - i
            key = self._make_sub_key(oa_id, sub_window)
            count_str = await self.kv.get(key)
            if count_str:
                total += int(count_str)

        if total >= limit:
            reset_at = int(now) + window_seconds
            return False, RateLimitInfo(
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                exceeded=True,
            )

        # Increment current sub-window
        key = self._make_sub_key(oa_id, current_sub)
        current_str = await self.kv.get(key)
        current = int(current_str) if current_str else 0
        new_count = current + 1

        # TTL covers current + 1 sub-window
        ttl = self.sub_window_size * 2
        await self.kv.put(key, str(new_count), expiration_ttl=ttl)

        remaining = limit - total - 1
        reset_at = int(now) + window_seconds

        return True, RateLimitInfo(
            limit=limit,
            remaining=max(0, remaining),
            reset_at=reset_at,
            exceeded=False,
        )


# Factory function
def create_rate_limiter(
    kv: KVNamespace | None = None,
    default_limit: int = 100,
    default_window_seconds: int = 60,
    sliding: bool = False,
) -> ZaloRateLimiter:
    """Create rate limiter instance.

    Args:
        kv: KV namespace (uses InMemoryKV if None)
        default_limit: Default rate limit
        default_window_seconds: Default window
        sliding: Use sliding window algorithm

    Returns:
        ZaloRateLimiter instance
    """
    if kv is None:
        kv = InMemoryKV()

    if sliding:
        return SlidingWindowRateLimiter(kv, default_limit, default_window_seconds)
    return ZaloRateLimiter(kv, default_limit, default_window_seconds)
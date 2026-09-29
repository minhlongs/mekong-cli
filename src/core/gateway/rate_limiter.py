# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sliding-Window Token Bucket Rate Limiter and Telemetry Hub.

Provides thread-safe token bucket rate limiting with multi-tier tenant quotas,
sliding window accounting for burst/rate control, RFC-compliant response headers,
and an in-memory telemetry and health metrics hub for the Mekong Gateway.

100% Python Standard Library only (test_core_boundary.py compliant).
"""

from __future__ import annotations

import collections
from dataclasses import dataclass
from enum import Enum
import math
import threading
import time
from typing import Any, Optional


class TenantTier(str, Enum):
    """Tenant subscription tier determining rate limit quota."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Backward compatibility alias
RateLimitTier = TenantTier


@dataclass(frozen=True)
class TierQuota:
    """Rate limit configuration for a tenant tier."""

    tier: TenantTier
    requests_per_minute: int
    capacity: int
    refill_rate: float  # tokens per second


# Backward compatibility alias
RateLimitQuota = TierQuota

TIER_QUOTAS: dict[TenantTier, TierQuota] = {
    TenantTier.FREE: TierQuota(
        tier=TenantTier.FREE,
        requests_per_minute=60,
        capacity=60,
        refill_rate=1.0,
    ),
    TenantTier.PRO: TierQuota(
        tier=TenantTier.PRO,
        requests_per_minute=600,
        capacity=600,
        refill_rate=10.0,
    ),
    TenantTier.ENTERPRISE: TierQuota(
        tier=TenantTier.ENTERPRISE,
        requests_per_minute=3000,
        capacity=3000,
        refill_rate=50.0,
    ),
}


def _normalize_tier(tier: str | TenantTier) -> TenantTier:
    """Normalize input string or enum into TenantTier."""
    if isinstance(tier, TenantTier):
        return tier
    clean = str(tier).lower().strip()
    if clean in ("free", "default"):
        return TenantTier.FREE
    elif clean in ("pro", "professional"):
        return TenantTier.PRO
    elif clean in ("enterprise", "ent"):
        return TenantTier.ENTERPRISE
    else:
        return TenantTier.FREE


@dataclass
class RateLimitDecision:
    """Evaluation result for a rate limit check."""

    allowed: bool
    tier: str
    limit: int
    remaining: int
    reset_timestamp: int
    retry_after: int

    def to_headers(self) -> dict[str, str]:
        """Generate RFC-compliant HTTP rate limit headers."""
        headers: dict[str, str] = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset_timestamp),
        }
        if not self.allowed:
            headers["Retry-After"] = str(self.retry_after)
        return headers

    @property
    def reset(self) -> int:
        """Alias for reset_timestamp."""
        return self.reset_timestamp

    @property
    def headers(self) -> dict[str, str]:
        """Convenience property returning headers dictionary."""
        return self.to_headers()

    def to_dict(self) -> dict[str, Any]:
        """Convert decision to JSON-serializable dictionary."""
        return {
            "allowed": self.allowed,
            "tier": self.tier,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_timestamp": self.reset_timestamp,
            "retry_after": self.retry_after,
            "headers": self.to_headers(),
        }


# Backward compatibility alias
RateLimitResult = RateLimitDecision


class TenantBucket:
    """Per-tenant state combining token bucket with sliding window tracking."""

    def __init__(self, quota: TierQuota) -> None:
        self.quota = quota
        self.tokens = float(quota.capacity)
        self.last_refill = time.time()
        self.window_requests: collections.deque[float] = collections.deque()
        self.lock = threading.Lock()


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window token bucket rate limiter with multi-tier quotas."""

    def __init__(self, default_tier: TenantTier | str = TenantTier.FREE) -> None:
        self._lock = threading.RLock()
        self._default_tier = _normalize_tier(default_tier)
        self._buckets: dict[str, TenantBucket] = {}
        self._tenant_tiers: dict[str, TenantTier] = {}

    def set_tenant_tier(self, tenant_id: str, tier: str | TenantTier) -> None:
        """Assign or update a tenant's subscription tier."""
        norm_tier = _normalize_tier(tier)
        with self._lock:
            self._tenant_tiers[tenant_id] = norm_tier
            quota = TIER_QUOTAS[norm_tier]
            self._buckets[tenant_id] = TenantBucket(quota)

    def get_tenant_tier(self, tenant_id: str = "default") -> TenantTier:
        """Return the active tier for a tenant."""
        with self._lock:
            return self._tenant_tiers.get(tenant_id, self._default_tier)

    def check_rate_limit(
        self,
        tenant_id: str = "default",
        cost: int = 1,
        tier: Optional[str | TenantTier] = None,
    ) -> RateLimitDecision:
        """Check and consume rate limit quota for a tenant."""
        with self._lock:
            if tier is not None:
                norm_tier = _normalize_tier(tier)
            else:
                norm_tier = self._tenant_tiers.get(tenant_id, self._default_tier)

            quota = TIER_QUOTAS[norm_tier]
            if tenant_id not in self._buckets:
                self._buckets[tenant_id] = TenantBucket(quota)
            bucket = self._buckets[tenant_id]

        now = time.time()
        with bucket.lock:
            # 1. Refill tokens based on elapsed seconds
            elapsed = max(0.0, now - bucket.last_refill)
            bucket.tokens = min(float(quota.capacity), bucket.tokens + elapsed * quota.refill_rate)
            bucket.last_refill = now

            # 2. Slide window (evict entries older than 60.0 seconds)
            cutoff = now - 60.0
            while bucket.window_requests and bucket.window_requests[0] <= cutoff:
                bucket.window_requests.popleft()

            # 3. Quota check
            token_ok = bucket.tokens >= cost
            window_ok = (len(bucket.window_requests) + cost) <= quota.capacity

            if token_ok and window_ok:
                bucket.tokens -= cost
                for _ in range(cost):
                    bucket.window_requests.append(now)
                remaining = max(0, min(int(bucket.tokens), quota.capacity - len(bucket.window_requests)))
                if bucket.tokens < quota.capacity:
                    reset_timestamp = int(math.ceil(now + (quota.capacity - bucket.tokens) / quota.refill_rate))
                else:
                    reset_timestamp = int(now)
                retry_after = 0
                allowed = True
            else:
                allowed = False
                remaining = 0
                needed = cost - bucket.tokens
                retry_after_token = math.ceil(needed / quota.refill_rate) if needed > 0 else 1
                retry_after_window = 0
                if bucket.window_requests:
                    retry_after_window = math.ceil(bucket.window_requests[0] + 60.0 - now)
                retry_after = max(1, int(retry_after_token), int(retry_after_window))
                reset_timestamp = int(math.ceil(now + max(1.0, (quota.capacity - bucket.tokens) / quota.refill_rate)))

        return RateLimitDecision(
            allowed=allowed,
            tier=norm_tier.value,
            limit=quota.capacity,
            remaining=remaining,
            reset_timestamp=reset_timestamp,
            retry_after=retry_after,
        )

    # Convenience alias matching check(...)
    check = check_rate_limit

    def get_quota(self, tenant_id: str = "default") -> dict[str, Any]:
        """Return current quota, remaining tokens, tier, and reset timestamp without consuming."""
        with self._lock:
            tier = self._tenant_tiers.get(tenant_id, self._default_tier)
            quota = TIER_QUOTAS[tier]
            if tenant_id not in self._buckets:
                self._buckets[tenant_id] = TenantBucket(quota)
            bucket = self._buckets[tenant_id]

        now = time.time()
        with bucket.lock:
            elapsed = max(0.0, now - bucket.last_refill)
            current_tokens = min(float(quota.capacity), bucket.tokens + elapsed * quota.refill_rate)
            bucket.tokens = current_tokens
            bucket.last_refill = now

            cutoff = now - 60.0
            while bucket.window_requests and bucket.window_requests[0] <= cutoff:
                bucket.window_requests.popleft()

            remaining = max(0, min(int(current_tokens), quota.capacity - len(bucket.window_requests)))
            if current_tokens < quota.capacity:
                reset_timestamp = int(math.ceil(now + (quota.capacity - current_tokens) / quota.refill_rate))
            else:
                reset_timestamp = int(now)

        return {
            "tenant_id": tenant_id,
            "tier": tier.value,
            "limit": quota.capacity,
            "capacity": quota.capacity,
            "remaining": remaining,
            "refill_rate": quota.refill_rate,
            "reset_timestamp": reset_timestamp,
        }

    def reset(self) -> None:
        """Reset state for testing."""
        with self._lock:
            self._buckets.clear()
            self._tenant_tiers.clear()


_global_rate_limiter: Optional[SlidingWindowRateLimiter] = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Retrieve global singleton SlidingWindowRateLimiter."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        with _rate_limiter_lock:
            if _global_rate_limiter is None:
                _global_rate_limiter = SlidingWindowRateLimiter()
    return _global_rate_limiter


def set_rate_limiter(limiter: SlidingWindowRateLimiter) -> None:
    """Set global singleton SlidingWindowRateLimiter."""
    global _global_rate_limiter
    with _rate_limiter_lock:
        _global_rate_limiter = limiter


class GatewayTelemetryHub:
    """Thread-safe telemetry tracker and health metrics collector for Mekong Gateway."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()
        self._total_requests = 0
        self._rate_limit_rejections = 0
        self._total_streams_opened = 0
        self._active_streams = 0
        self._active_subscribers = 0
        self._latencies_ms: collections.deque[float] = collections.deque(maxlen=10000)
        self._path_counts: collections.defaultdict[str, int] = collections.defaultdict(int)
        self._status_counts: collections.defaultdict[int, int] = collections.defaultdict(int)
        self._tenant_counts: collections.defaultdict[str, int] = collections.defaultdict(int)
        self._tenant_rejections: collections.defaultdict[str, int] = collections.defaultdict(int)

    def record_request(
        self,
        path: str | float = "/",
        duration_ms: float = 0.0,
        status_code: int = 200,
        tenant_id: str = "default",
        **kwargs: Any,
    ) -> None:
        """Record request duration, status code, and path."""
        with self._lock:
            if isinstance(path, (int, float)):
                actual_duration = float(path)
                actual_path = str(kwargs.get("path", "/"))
                actual_status = int(duration_ms) if duration_ms else 200
                actual_tenant = str(status_code) if isinstance(status_code, str) else str(tenant_id)
            else:
                actual_path = str(path) if path else "/"
                actual_duration = float(duration_ms)
                actual_status = int(status_code)
                actual_tenant = str(tenant_id)

            self._total_requests += 1
            self._latencies_ms.append(actual_duration)
            self._path_counts[actual_path] += 1
            self._status_counts[actual_status] += 1
            self._tenant_counts[actual_tenant] += 1
            if actual_status == 429:
                self._rate_limit_rejections += 1
                self._tenant_rejections[actual_tenant] += 1

    def record_rate_limit_rejection(self, tenant_id: str = "default") -> None:
        """Increment rate limit rejection counter."""
        with self._lock:
            self._rate_limit_rejections += 1
            self._tenant_rejections[tenant_id] += 1

    def record_stream_opened(self) -> None:
        """Track opened stream."""
        with self._lock:
            self._total_streams_opened += 1
            self._active_streams += 1

    def record_stream_closed(self) -> None:
        """Track closed stream."""
        with self._lock:
            self._active_streams = max(0, self._active_streams - 1)

    record_stream_open = record_stream_opened
    record_stream_close = record_stream_closed

    def record_subscriber_joined(self) -> None:
        """Track new active subscriber."""
        with self._lock:
            self._active_subscribers += 1

    def record_subscriber_left(self) -> None:
        """Track disconnected subscriber."""
        with self._lock:
            self._active_subscribers = max(0, self._active_subscribers - 1)

    def set_active_subscribers(self, count: int) -> None:
        """Explicitly set current active subscriber count."""
        with self._lock:
            self._active_subscribers = max(0, count)

    def get_latency_percentiles(self) -> dict[str, float]:
        """Compute p50, p90, and p99 percentiles from recent request latencies in ms."""
        with self._lock:
            arr = sorted(self._latencies_ms)
        if not arr:
            return {
                "p50_ms": 0.0,
                "p90_ms": 0.0,
                "p99_ms": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            }
        n = len(arr)

        def _pct(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return round(arr[int(k)], 2)
            d0 = arr[int(f)] * (c - k)
            d1 = arr[int(c)] * (k - f)
            return round(d0 + d1, 2)

        p50 = _pct(0.50)
        p90 = _pct(0.90)
        p99 = _pct(0.99)
        return {
            "p50_ms": p50,
            "p90_ms": p90,
            "p99_ms": p99,
            "p50": p50,
            "p90": p90,
            "p99": p99,
        }

    def get_health(self) -> dict[str, Any]:
        """Return basic liveness and uptime status."""
        now = time.time()
        uptime = round(now - self._start_time, 2)
        with self._lock:
            return {
                "status": "healthy",
                "uptime_seconds": uptime,
                "version": "0.1.0",
                "timestamp": int(now),
                "active_streams": self._active_streams,
            }

    get_health_status = get_health

    def get_metrics(self) -> dict[str, Any]:
        """Return aggregated stream count, active subscribers, total requests, rejections, and latency percentiles."""
        now = time.time()
        uptime = round(now - self._start_time, 2)
        pcts = self.get_latency_percentiles()
        with self._lock:
            return {
                "status": "healthy",
                "uptime_seconds": uptime,
                "version": "0.1.0",
                "timestamp": int(now),
                "stream_count": self._total_streams_opened,
                "total_streams_opened": self._total_streams_opened,
                "active_streams": self._active_streams,
                "active_subscribers": self._active_subscribers,
                "total_requests": self._total_requests,
                "rate_limit_rejections": self._rate_limit_rejections,
                "latency_percentiles": pcts,
                "p50_ms": pcts["p50_ms"],
                "p90_ms": pcts["p90_ms"],
                "p99_ms": pcts["p99_ms"],
                "tier_quotas": {
                    "free": 60,
                    "pro": 600,
                    "enterprise": 3000,
                },
                "active_tenants_count": len(self._tenant_counts),
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._start_time = time.time()
            self._total_requests = 0
            self._rate_limit_rejections = 0
            self._total_streams_opened = 0
            self._active_streams = 0
            self._active_subscribers = 0
            self._latencies_ms.clear()
            self._path_counts.clear()
            self._status_counts.clear()
            self._tenant_counts.clear()
            self._tenant_rejections.clear()


_global_telemetry_hub: Optional[GatewayTelemetryHub] = None
_telemetry_hub_lock = threading.Lock()


def get_telemetry_hub() -> GatewayTelemetryHub:
    """Retrieve global singleton GatewayTelemetryHub."""
    global _global_telemetry_hub
    if _global_telemetry_hub is None:
        with _telemetry_hub_lock:
            if _global_telemetry_hub is None:
                _global_telemetry_hub = GatewayTelemetryHub()
    return _global_telemetry_hub


def set_telemetry_hub(hub: GatewayTelemetryHub) -> None:
    """Set global singleton GatewayTelemetryHub."""
    global _global_telemetry_hub
    with _telemetry_hub_lock:
        _global_telemetry_hub = hub


__all__ = [
    "TenantTier",
    "RateLimitTier",
    "TierQuota",
    "RateLimitQuota",
    "TIER_QUOTAS",
    "RateLimitDecision",
    "RateLimitResult",
    "TenantBucket",
    "SlidingWindowRateLimiter",
    "get_rate_limiter",
    "set_rate_limiter",
    "GatewayTelemetryHub",
    "get_telemetry_hub",
    "set_telemetry_hub",
]

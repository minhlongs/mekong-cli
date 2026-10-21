# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sliding-Window Token Bucket Rate Limiter and Telemetry Hub facade."""

from __future__ import annotations

import math
import threading
import time
from typing import Any, Optional

from .rate_limiter_telemetry import (
    GatewayTelemetryHub, get_telemetry_hub, set_telemetry_hub,
)
from .rate_limiter_types import (
    TIER_QUOTAS, RateLimitDecision, RateLimitQuota, RateLimitResult,
    RateLimitTier, TenantBucket, TenantTier, TierQuota, normalize_tier,
)


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window token bucket rate limiter with multi-tier quotas."""

    def __init__(self, default_tier: TenantTier | str = TenantTier.FREE) -> None:
        self._lock = threading.RLock()
        self._default_tier = normalize_tier(default_tier)
        self._buckets: dict[str, TenantBucket] = {}
        self._tenant_tiers: dict[str, TenantTier] = {}

    def set_tenant_tier(self, tenant_id: str, tier: str | TenantTier) -> None:
        norm_tier = normalize_tier(tier)
        with self._lock:
            self._tenant_tiers[tenant_id] = norm_tier
            quota = TIER_QUOTAS[norm_tier]
            self._buckets[tenant_id] = TenantBucket(quota)

    def get_tenant_tier(self, tenant_id: str = "default") -> TenantTier:
        with self._lock:
            return self._tenant_tiers.get(tenant_id, self._default_tier)

    def check_rate_limit(
        self,
        tenant_id: str = "default",
        cost: int = 1,
        tier: Optional[str | TenantTier] = None,
    ) -> RateLimitDecision:
        with self._lock:
            if tier is not None:
                norm_tier = normalize_tier(tier)
            else:
                norm_tier = self._tenant_tiers.get(tenant_id, self._default_tier)
            quota = TIER_QUOTAS[norm_tier]
            if tenant_id not in self._buckets:
                self._buckets[tenant_id] = TenantBucket(quota)
            bucket = self._buckets[tenant_id]

        now = time.time()
        with bucket.lock:
            elapsed = max(0.0, now - bucket.last_refill)
            bucket.tokens = min(float(quota.capacity), bucket.tokens + elapsed * quota.refill_rate)
            bucket.last_refill = now

            cutoff = now - 60.0
            while bucket.window_requests and bucket.window_requests[0] <= cutoff:
                bucket.window_requests.popleft()

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

    check = check_rate_limit

    def get_quota(self, tenant_id: str = "default") -> dict[str, Any]:
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
        with self._lock:
            self._buckets.clear()
            self._tenant_tiers.clear()


_global_rate_limiter: Optional[SlidingWindowRateLimiter] = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter() -> SlidingWindowRateLimiter:
    global _global_rate_limiter
    if _global_rate_limiter is None:
        with _rate_limiter_lock:
            if _global_rate_limiter is None:
                _global_rate_limiter = SlidingWindowRateLimiter()
    return _global_rate_limiter


def set_rate_limiter(limiter: SlidingWindowRateLimiter) -> None:
    global _global_rate_limiter
    with _rate_limiter_lock:
        _global_rate_limiter = limiter


__all__ = [
    "GatewayTelemetryHub", "RateLimitDecision", "RateLimitQuota", "RateLimitResult",
    "RateLimitTier", "SlidingWindowRateLimiter", "TIER_QUOTAS", "TenantBucket",
    "TenantTier", "TierQuota", "get_rate_limiter", "get_telemetry_hub",
    "set_rate_limiter", "set_telemetry_hub",
]

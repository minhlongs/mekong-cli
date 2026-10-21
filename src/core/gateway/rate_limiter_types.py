# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate limiter domain types and tenant quotas."""

from __future__ import annotations

import collections
from dataclasses import dataclass
from enum import Enum
import threading
import time
from typing import Any


class TenantTier(str, Enum):
    """Tenant subscription tier determining rate limit quota."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


RateLimitTier = TenantTier


@dataclass(frozen=True)
class TierQuota:
    """Rate limit configuration for a tenant tier."""

    tier: TenantTier
    requests_per_minute: int
    capacity: int
    refill_rate: float  # tokens per second


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


def normalize_tier(tier: str | TenantTier) -> TenantTier:
    """Normalize input string or enum into TenantTier."""
    if isinstance(tier, TenantTier):
        return tier
    clean = str(tier).lower().strip()
    if clean in ("free", "default"):
        return TenantTier.FREE
    if clean in ("pro", "professional"):
        return TenantTier.PRO
    if clean in ("enterprise", "ent"):
        return TenantTier.ENTERPRISE
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
        return self.reset_timestamp

    @property
    def headers(self) -> dict[str, str]:
        return self.to_headers()

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "tier": self.tier,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_timestamp": self.reset_timestamp,
            "retry_after": self.retry_after,
            "headers": self.to_headers(),
        }


RateLimitResult = RateLimitDecision


class TenantBucket:
    """Per-tenant state combining token bucket with sliding window tracking."""

    def __init__(self, quota: TierQuota) -> None:
        self.quota = quota
        self.tokens = float(quota.capacity)
        self.last_refill = time.time()
        self.window_requests: collections.deque[float] = collections.deque()
        self.lock = threading.Lock()


__all__ = [
    "RateLimitDecision",
    "RateLimitQuota",
    "RateLimitResult",
    "RateLimitTier",
    "TIER_QUOTAS",
    "TenantBucket",
    "TenantTier",
    "TierQuota",
    "normalize_tier",
]

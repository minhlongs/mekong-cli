# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Quota State Cache — ROIaaS Phase 6b

Local SQLite cache for quota state to reduce API calls.
TTL: 5 minutes default.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from src.raas.quota_cache_models import (
    _DDL,
    DB_PATH,
    DEFAULT_TTL_SECONDS,
    GRACE_PERIOD_SECONDS,
    QuotaState,
)
from src.raas.quota_cache_store import QuotaCache

# Singleton instance
_cache: Optional[QuotaCache] = None


def get_cache(ttl_seconds: int = DEFAULT_TTL_SECONDS) -> QuotaCache:
    """Get global cache instance."""
    global _cache
    if _cache is None or _cache.ttl_seconds != ttl_seconds:
        _cache = QuotaCache(ttl_seconds=ttl_seconds)
    return _cache


def get_cached_quota(key_id: str) -> Optional[QuotaState]:
    """Get cached quota for key."""
    return get_cache().get(key_id)


def cache_quota(
    key_id: str,
    daily_used: int,
    daily_limit: int,
    tier: str = "free",
    status: str = "active",
    expires_at_ts: int = 0,
    monthly_used: int = 0,
    monthly_limit: int = 0,
    is_offline_mode: bool = False,
    grace_period_remaining: int = GRACE_PERIOD_SECONDS,
    last_reset_date: Optional[str] = None,
) -> QuotaState:
    """Cache quota state for key with grace period support."""
    now = datetime.now(timezone.utc)
    if last_reset_date is None:
        last_reset_date = now.strftime("%Y-%m-%d")

    state = QuotaState(
        key_id=key_id,
        daily_used=daily_used,
        daily_limit=daily_limit,
        tier=tier,
        status=status,
        expires_at_ts=expires_at_ts,
        monthly_used=monthly_used,
        monthly_limit=monthly_limit,
        cached_at=now.isoformat(),
        expires_at=(now + timedelta(seconds=DEFAULT_TTL_SECONDS)).isoformat(),
        last_online_validation=now.isoformat() if not is_offline_mode else "",
        grace_period_remaining=grace_period_remaining,
        is_offline_mode=is_offline_mode,
        last_reset_date=last_reset_date,
    )
    return get_cache().set(
        key_id,
        daily_used,
        daily_limit,
        tier,
        status,
        expires_at_ts,
        monthly_used,
        monthly_limit,
        grace_period_remaining=grace_period_remaining,
        last_online_validation=state.last_online_validation,
        is_offline_mode=is_offline_mode,
        last_reset_date=state.last_reset_date,
    )


def invalidate_cache(key_id: str) -> bool:
    """Invalidate cache for key."""
    return get_cache().invalidate(key_id)


__all__ = [
    "DB_PATH",
    "DEFAULT_TTL_SECONDS",
    "GRACE_PERIOD_SECONDS",
    "QuotaCache",
    "QuotaState",
    "_DDL",
    "cache_quota",
    "get_cache",
    "get_cached_quota",
    "invalidate_cache",
]

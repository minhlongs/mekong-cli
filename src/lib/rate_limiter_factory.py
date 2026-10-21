# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate Limiter Factory — ROIaaS Phase 6."""

import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional

from engine.billing.tier_config import RateLimitConfig, Tier, get_preset_config


@dataclass
class CachedConfig:
    """Cached configuration with TTL."""
    config: RateLimitConfig
    expires_at: float


class RateLimiterFactory:
    """Factory for creating and caching tier-based rate limiters."""

    DEFAULT_CACHE_TTL_SECONDS = 300

    def __init__(self, cache_ttl: Optional[int] = None):
        self._cache: Dict[str, CachedConfig] = {}
        self._cache_lock = Lock()
        self._cache_ttl = cache_ttl or self.DEFAULT_CACHE_TTL_SECONDS

    def _get_cache_key(self, tier: str, preset: str) -> str:
        return f"{tier.lower()}:{preset.lower()}"

    def _is_cached(self, key: str) -> bool:
        if key not in self._cache:
            return False
        if time.time() > self._cache[key].expires_at:
            del self._cache[key]
            return False
        return True

    def get_config_for_tier(self, tier: str, preset: str) -> RateLimitConfig:
        """Get rate limit config for tier and preset with TTL caching."""
        cache_key = self._get_cache_key(tier, preset)
        with self._cache_lock:
            if self._is_cached(cache_key):
                return self._cache[cache_key].config
            config = get_preset_config(tier, preset)
            self._cache[cache_key] = CachedConfig(
                config=config, expires_at=time.time() + self._cache_ttl
            )
            return config

    def invalidate_cache(self, tier: Optional[str] = None) -> None:
        """Invalidate cache entries for a specific tier or entire cache."""
        with self._cache_lock:
            if tier is None:
                self._cache.clear()
            else:
                prefix = f"{tier.lower()}:"
                for key in [k for k in self._cache if k.startswith(prefix)]:
                    del self._cache[key]

    def get_rate_limiter(self, tier: str, preset: str = "api_default") -> "TierRateLimiter":
        """Get a configured rate limiter for a tier."""
        return TierRateLimiter(self.get_config_for_tier(tier, preset))

    def get_all_tier_configs(self) -> Dict[str, Dict[str, RateLimitConfig]]:
        """Get all configurations for all tiers."""
        result = {}
        for tier in Tier:
            t_name = tier.value
            result[t_name] = {
                "auth_login": get_preset_config(t_name, "auth_login"),
                "auth_callback": get_preset_config(t_name, "auth_callback"),
                "auth_refresh": get_preset_config(t_name, "auth_refresh"),
                "api_default": get_preset_config(t_name, "api_default"),
            }
        return result


class TierRateLimiter:
    """Token bucket rate limiter for a specific tier/preset."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._tokens = float(config.burst_size)
        self._last_update = time.time()
        self._lock = Lock()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self._last_update
        tokens_to_add = elapsed * (self.config.requests_per_minute / 60.0)
        self._tokens = min(self._tokens + tokens_to_add, self.config.burst_size)
        self._last_update = now

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens."""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait until tokens are available."""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                return 0.0
            tokens_needed = tokens - self._tokens
            return tokens_needed / (self.config.requests_per_minute / 60.0)

    def reset(self) -> None:
        """Reset the rate limiter to full capacity."""
        with self._lock:
            self._tokens = float(self.config.burst_size)
            self._last_update = time.time()


_factory: Optional[RateLimiterFactory] = None
_factory_lock = Lock()


def get_factory(cache_ttl: Optional[int] = None) -> RateLimiterFactory:
    """Get or create the global rate limiter factory."""
    global _factory
    with _factory_lock:
        if _factory is None:
            _factory = RateLimiterFactory(cache_ttl)
        return _factory


def get_rate_limiter(tier: str, preset: str = "api_default") -> TierRateLimiter:
    """Convenience function to get a rate limiter."""
    return get_factory().get_rate_limiter(tier, preset)


def invalidate_cache(tier: Optional[str] = None) -> None:
    """Invalidate the global factory cache."""
    get_factory().invalidate_cache(tier)


__all__ = [
    "RateLimiterFactory", "TierRateLimiter", "CachedConfig",
    "get_factory", "get_rate_limiter", "invalidate_cache",
]

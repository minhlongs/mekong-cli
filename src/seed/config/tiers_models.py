# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Canonical TierKey enum, TierConfig, TierQuotas, and RateLimitConfig dataclasses."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TierKey(Enum):
    """Unique identifier for each pricing tier.

    These are the canonical keys. All other tier names are aliases.
    """

    FREE = "free"
    TRIAL = "trial"
    STARTER = "starter"
    GROWTH = "growth"
    PRO = "pro"
    ENTERPRISE = "enterprise"

    @classmethod
    def values(cls) -> list[str]:
        return [t.value for t in cls]

    @classmethod
    def aliases(cls) -> dict[str, str]:
        """Return every historical tier name → canonical key mapping."""
        return {
            "free": "free",
            "FREE": "free",
            "trial": "trial",
            "trial_vn": "trial",
            "TRIAL": "trial",
            "starter": "starter",
            "starter_vn": "starter",
            "basic": "starter",
            "BASIC": "starter",
            "STARTER": "starter",
            "growth": "growth",
            "growth_vn": "growth",
            "PREMIUM": "growth",
            "premium": "growth",
            "GROWTH": "growth",
            "team": "growth",
            "TEAM": "growth",
            "pro": "pro",
            "pro_vn": "pro",
            "enterprise": "pro",
            "ENTERPRISE": "pro",
            "PRO": "pro",
            "MASTER": "pro",
            "master": "pro",
            "enterprise_plus": "enterprise",
        }

    @classmethod
    def _missing_(cls, value: object):
        """Resolve case-insensitive names and legacy aliases on instantiation."""
        if isinstance(value, str):
            val_lower = value.lower()
            for member in cls:
                if member.value == val_lower:
                    return member
            canonical = cls.aliases().get(value) or cls.aliases().get(val_lower)
            if canonical:
                for member in cls:
                    if member.value == canonical:
                        return member
        return None


Tier = TierKey


@dataclass(frozen=True)
class TierConfig:
    """Immutable definition of a pricing tier."""

    key: str
    display_name: str = ""
    display_name_vi: str = ""
    monthly_credits: int = 0
    monthly_price_usd: float = 0.0
    monthly_price_vnd: int = 0
    mcu_cost_simple: int = 1
    mcu_cost_standard: int = 3
    mcu_cost_complex: int = 5
    daily_command_limit: int = 0
    daily_agent_limit: int = 0
    daily_pipeline_limit: int = 0
    trial_days: int = 0
    grace_days: int = 0
    features: tuple[str, ...] = ()


@dataclass(frozen=True)
class TierQuotas:
    """Daily quotas for a tier."""

    commands: int = 0
    agents: int = 0
    pipelines: int = 0


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a single endpoint."""

    requests_per_minute: int
    burst_size: Optional[int] = None
    window_seconds: Optional[int] = None

    def __post_init__(self) -> None:
        if self.burst_size is None:
            self.burst_size = self.requests_per_minute
        if self.window_seconds is None:
            self.window_seconds = 60


@dataclass
class TierRateLimitConfig:
    """Complete rate limit configuration for a tier."""

    tier: TierKey
    auth_login: RateLimitConfig
    auth_callback: RateLimitConfig
    auth_refresh: RateLimitConfig
    api_default: RateLimitConfig


__all__ = [
    "TierKey",
    "Tier",
    "TierConfig",
    "TierQuotas",
    "RateLimitConfig",
    "TierRateLimitConfig",
]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tier lookup helpers, backward-compatible dict builders, and rate-limit preset resolvers."""
from __future__ import annotations

from typing import Union

from src.seed.config.tiers_definitions import DEFAULT_TIER_CONFIGS, _TIERS
from src.seed.config.tiers_models import (
    RateLimitConfig,
    TierConfig,
    TierKey,
    TierQuotas,
    TierRateLimitConfig,
)


def _resolve(key_or_alias: str) -> str | None:
    """Resolve any tier name (canonical or alias) to canonical key."""
    if not key_or_alias:
        return None
    aliases = TierKey.aliases()
    canonical = aliases.get(key_or_alias.lower())
    if canonical:
        return canonical
    if key_or_alias in _TIERS:
        return key_or_alias
    return None


def get_tier(key_or_alias: str) -> TierConfig | None:
    """Return TierConfig for any tier name (canonical or alias)."""
    resolved = _resolve(key_or_alias)
    return _TIERS.get(resolved) if resolved else None


def tier_credits(key_or_alias: str, default: int = 0) -> int:
    """Return monthly_credits for any tier name (canonical or alias)."""
    tier = get_tier(key_or_alias)
    return tier.monthly_credits if tier else default


def tier_features(key_or_alias: str) -> tuple[str, ...]:
    """Return enabled feature IDs for a tier."""
    tier = get_tier(key_or_alias)
    return tier.features if tier else ()


def mcu_cost(key_or_alias: str, complexity: str) -> int:
    """Return MCU cost for a given complexity level under a tier."""
    tier = get_tier(key_or_alias)
    if not tier:
        return 1
    cost_map = {
        "simple": tier.mcu_cost_simple,
        "standard": tier.mcu_cost_standard,
        "complex": tier.mcu_cost_complex,
    }
    return cost_map.get(complexity, 1)


def tier_credits_dict() -> dict[str, int]:
    """Return TIER_CREDITS dict keyed by canonical tier key."""
    return {
        k: v.monthly_credits
        for k, v in _TIERS.items()
        if k not in ("free", "enterprise")
    }


def mcu_costs_dict() -> dict[str, int]:
    """Return MCU_COSTS dict — backward-compatible with mcu_billing.MCU_COSTS."""
    t = _TIERS["starter"]
    return {
        "simple": t.mcu_cost_simple,
        "standard": t.mcu_cost_standard,
        "complex": t.mcu_cost_complex,
    }


def tier_quotas(key_or_alias: str) -> TierQuotas:
    """Return daily quotas for a tier."""
    tier = get_tier(key_or_alias)
    if not tier:
        return TierQuotas()
    return TierQuotas(
        commands=tier.daily_command_limit,
        agents=tier.daily_agent_limit,
        pipelines=tier.daily_pipeline_limit,
    )


def vn_tier_for_pricing_file(key_or_alias: str) -> str | None:
    """Map canonical tier key to pricing.json vn_products key."""
    tier = get_tier(key_or_alias)
    if not tier:
        return None
    mapping = {
        "free": None,
        "trial": None,
        "starter": "starter_vn",
        "growth": "growth_vn",
        "pro": "pro_vn",
        "enterprise": None,
    }
    return mapping.get(tier.key)


def trial_config(key_or_alias: str) -> tuple[int, int] | None:
    """Return (trial_days, grace_days) if tier has a trial."""
    tier = get_tier(key_or_alias)
    if not tier or tier.trial_days == 0:
        return None
    return (tier.trial_days, tier.grace_days)


def get_tier_config(tier: Union[str, TierKey]) -> TierRateLimitConfig:
    """Get rate limit configuration for a tier."""
    if isinstance(tier, str):
        try:
            tier_enum = TierKey(tier)
        except ValueError:
            raise ValueError(
                f"Invalid tier: {tier}. Must be one of: {[t.value for t in TierKey]}"
            )
    elif isinstance(tier, TierKey):
        tier_enum = tier
    else:
        raise ValueError(
            f"Invalid tier: {tier}. Must be one of: {[t.value for t in TierKey]}"
        )

    if tier_enum not in DEFAULT_TIER_CONFIGS:
        raise ValueError(
            f"Invalid tier: {tier}. Must be one of: {[t.value for t in TierKey]}"
        )

    return DEFAULT_TIER_CONFIGS[tier_enum]


def get_preset_config(tier: Union[str, TierKey], preset: str) -> RateLimitConfig:
    """Get rate limit config for a specific preset endpoint."""
    tier_config = get_tier_config(tier)
    preset_map = {
        "auth_login": tier_config.auth_login,
        "auth_callback": tier_config.auth_callback,
        "auth_refresh": tier_config.auth_refresh,
        "api_default": tier_config.api_default,
    }
    if preset not in preset_map:
        raise ValueError(
            f"Invalid preset: {preset}. Must be one of: {list(preset_map.keys())}"
        )
    return preset_map[preset]


__all__ = [
    "_resolve",
    "get_tier",
    "tier_credits",
    "tier_features",
    "mcu_cost",
    "tier_credits_dict",
    "mcu_costs_dict",
    "tier_quotas",
    "vn_tier_for_pricing_file",
    "trial_config",
    "get_tier_config",
    "get_preset_config",
]

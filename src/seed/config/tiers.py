# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unified Tier Config — single source of truth for all tier/pricing/credit data.

This module consolidates the three previously-divergent tier vocabularies:
1. MCU billing tiers   : starter / growth / premium (mcu_billing.py)
2. VN product tiers    : starter_vn / growth_vn / pro_vn (pricing.json)
3. Documentation tiers : Starter / Growth / Pro (CLAUDE.md)
"""
from __future__ import annotations

from src.seed.config.tiers_definitions import DEFAULT_TIER_CONFIGS, _TIERS
from src.seed.config.tiers_helpers import (
    _resolve,
    get_preset_config,
    get_tier,
    get_tier_config,
    mcu_cost,
    mcu_costs_dict,
    tier_credits,
    tier_credits_dict,
    tier_features,
    tier_quotas,
    trial_config,
    vn_tier_for_pricing_file,
)
from src.seed.config.tiers_models import (
    RateLimitConfig,
    Tier,
    TierConfig,
    TierKey,
    TierQuotas,
    TierRateLimitConfig,
)

__all__ = [
    "Tier",
    "TierKey",
    "TierConfig",
    "TierQuotas",
    "RateLimitConfig",
    "TierRateLimitConfig",
    "DEFAULT_TIER_CONFIGS",
    "_TIERS",
    "_resolve",
    "get_tier",
    "tier_credits",
    "tier_features",
    "mcu_cost",
    "tier_quotas",
    "trial_config",
    "get_tier_config",
    "get_preset_config",
    "tier_credits_dict",
    "mcu_costs_dict",
    "vn_tier_for_pricing_file",
]


def _demo() -> None:
    """Quick sanity check — run this module directly."""
    print(f"Tier config loaded. {len(_TIERS)} tiers defined.")
    for key, config in _TIERS.items():
        aliases = [a for a, k in TierKey.aliases().items() if k == key and a != key]
        print(
            f"  {key:12s} — {config.display_name:12s} {config.monthly_credits:6d} credits"
            f"   (aliases: {', '.join(sorted(set(aliases))) or 'none'})"
        )


if __name__ == "__main__":
    _demo()

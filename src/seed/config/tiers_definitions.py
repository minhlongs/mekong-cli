# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Canonical tier definitions (_TIERS) and default rate limit configurations (DEFAULT_TIER_CONFIGS)."""
from __future__ import annotations

from src.seed.config.tiers_models import (
    RateLimitConfig,
    TierConfig,
    TierKey,
    TierRateLimitConfig,
)

_TIERS: dict[str, TierConfig] = {
    "free": TierConfig(
        key="free",
        display_name="Free",
        display_name_vi="Miễn phí",
        monthly_credits=10,
        monthly_price_usd=0,
        monthly_price_vnd=0,
        daily_command_limit=10,
        daily_agent_limit=5,
        daily_pipeline_limit=3,
        features=("cli_commands",),
    ),
    "trial": TierConfig(
        key="trial",
        display_name="Trial",
        display_name_vi="Dùng thử",
        monthly_credits=50,
        monthly_price_usd=0,
        monthly_price_vnd=0,
        trial_days=14,
        grace_days=3,
        features=("cli_commands", "basic_agents"),
    ),
    "starter": TierConfig(
        key="starter",
        display_name="Starter",
        display_name_vi="Starter",
        monthly_credits=200,
        monthly_price_usd=49,
        monthly_price_vnd=199_000,
        features=("cli_commands", "advanced_agents", "gateway_integration"),
    ),
    "growth": TierConfig(
        key="growth",
        display_name="Growth",
        display_name_vi="Tăng trưởng",
        monthly_credits=1000,
        monthly_price_usd=149,
        monthly_price_vnd=299_000,
        features=("cli_commands", "advanced_agents", "gateway_integration", "kv_store_sync"),
    ),
    "pro": TierConfig(
        key="pro",
        display_name="Pro",
        display_name_vi="Professional",
        monthly_credits=5000,
        monthly_price_usd=499,
        monthly_price_vnd=499_000,
        features=(
            "cli_commands",
            "advanced_agents",
            "gateway_integration",
            "kv_store_sync",
            "real_time_entitlements",
            "enterprise_features",
        ),
    ),
    "enterprise": TierConfig(
        key="enterprise",
        display_name="Enterprise",
        display_name_vi="Doanh nghiệp",
        monthly_credits=20_000,
        monthly_price_usd=0,
        monthly_price_vnd=0,
        features=(
            "cli_commands",
            "advanced_agents",
            "gateway_integration",
            "kv_store_sync",
            "real_time_entitlements",
            "enterprise_features",
        ),
    ),
    "master": TierConfig(
        key="master",
        display_name="Master",
        display_name_vi="Master",
        monthly_credits=50_000,
        monthly_price_usd=4_999,
        monthly_price_vnd=4_999_000,
        features=(
            "cli_commands",
            "advanced_agents",
            "gateway_integration",
            "kv_store_sync",
            "real_time_entitlements",
            "enterprise_features",
            "dedicated_workers",
            "custom_sla",
            "white_label",
        ),
    ),
}

DEFAULT_TIER_CONFIGS: dict[TierKey, TierRateLimitConfig] = {
    TierKey.FREE: TierRateLimitConfig(
        tier=TierKey.FREE,
        auth_login=RateLimitConfig(requests_per_minute=5, burst_size=5),
        auth_callback=RateLimitConfig(requests_per_minute=10, burst_size=10),
        auth_refresh=RateLimitConfig(requests_per_minute=10, burst_size=10),
        api_default=RateLimitConfig(requests_per_minute=20, burst_size=30),
    ),
    TierKey.TRIAL: TierRateLimitConfig(
        tier=TierKey.TRIAL,
        auth_login=RateLimitConfig(requests_per_minute=10, burst_size=10),
        auth_callback=RateLimitConfig(requests_per_minute=20, burst_size=20),
        auth_refresh=RateLimitConfig(requests_per_minute=20, burst_size=20),
        api_default=RateLimitConfig(requests_per_minute=40, burst_size=60),
    ),
    TierKey.STARTER: TierRateLimitConfig(
        tier=TierKey.STARTER,
        auth_login=RateLimitConfig(requests_per_minute=15, burst_size=15),
        auth_callback=RateLimitConfig(requests_per_minute=30, burst_size=30),
        auth_refresh=RateLimitConfig(requests_per_minute=30, burst_size=30),
        api_default=RateLimitConfig(requests_per_minute=50, burst_size=75),
    ),
    TierKey.GROWTH: TierRateLimitConfig(
        tier=TierKey.GROWTH,
        auth_login=RateLimitConfig(requests_per_minute=20, burst_size=20),
        auth_callback=RateLimitConfig(requests_per_minute=45, burst_size=45),
        auth_refresh=RateLimitConfig(requests_per_minute=45, burst_size=45),
        api_default=RateLimitConfig(requests_per_minute=80, burst_size=120),
    ),
    TierKey.PRO: TierRateLimitConfig(
        tier=TierKey.PRO,
        auth_login=RateLimitConfig(requests_per_minute=30, burst_size=30),
        auth_callback=RateLimitConfig(requests_per_minute=60, burst_size=60),
        auth_refresh=RateLimitConfig(requests_per_minute=60, burst_size=60),
        api_default=RateLimitConfig(requests_per_minute=100, burst_size=150),
    ),
    TierKey.ENTERPRISE: TierRateLimitConfig(
        tier=TierKey.ENTERPRISE,
        auth_login=RateLimitConfig(requests_per_minute=100, burst_size=100),
        auth_callback=RateLimitConfig(requests_per_minute=200, burst_size=200),
        auth_refresh=RateLimitConfig(requests_per_minute=200, burst_size=200),
        api_default=RateLimitConfig(requests_per_minute=500, burst_size=750),
    ),
    TierKey.MASTER: TierRateLimitConfig(
        tier=TierKey.MASTER,
        auth_login=RateLimitConfig(requests_per_minute=200, burst_size=200),
        auth_callback=RateLimitConfig(requests_per_minute=400, burst_size=400),
        auth_refresh=RateLimitConfig(requests_per_minute=400, burst_size=400),
        api_default=RateLimitConfig(requests_per_minute=1_000, burst_size=1_500),
    ),
}

__all__ = ["_TIERS", "DEFAULT_TIER_CONFIGS"]

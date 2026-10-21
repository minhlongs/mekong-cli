# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate-limit models, tier limits, and overage configurations for RaaS."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"

TIER_LIMITS: dict[str, dict[str, int]] = {
    "free":       {"daily": 10,  "monthly": 100},
    "starter":    {"daily": 50,  "monthly": 500},
    "growth":     {"daily": 200, "monthly": 2000},
    "pro":        {"daily": 500, "monthly": 5000},
    "enterprise": {"daily": 0,   "monthly": 0},   # 0 = unlimited
}


@dataclass
class OverageConfig:
    """Per-tier overage billing configuration."""

    allow_overage: bool
    overage_rate_per_credit: float
    warning_threshold_pct: int
    max_overage_credits: int  # 0 = no cap for enterprise


OVERAGE_TIERS: dict[str, OverageConfig] = {
    "free": OverageConfig(
        allow_overage=False, overage_rate_per_credit=0.0, warning_threshold_pct=80, max_overage_credits=0
    ),
    "starter": OverageConfig(
        allow_overage=False, overage_rate_per_credit=0.0, warning_threshold_pct=80, max_overage_credits=0
    ),
    "growth": OverageConfig(
        allow_overage=True, overage_rate_per_credit=0.02, warning_threshold_pct=80, max_overage_credits=500
    ),
    "pro": OverageConfig(
        allow_overage=True, overage_rate_per_credit=0.01, warning_threshold_pct=80, max_overage_credits=2000
    ),
    "enterprise": OverageConfig(
        allow_overage=True, overage_rate_per_credit=0.005, warning_threshold_pct=90, max_overage_credits=0
    ),
}


def get_overage_config(tier: str) -> OverageConfig:
    """Get overage config for tier. Defaults to free (no overage)."""
    return OVERAGE_TIERS.get(tier.lower(), OVERAGE_TIERS["free"])


_DDL = """
CREATE TABLE IF NOT EXISTS rate_limit_events (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    credits_used INTEGER NOT NULL,
    timestamp   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rle_tenant_ts
    ON rate_limit_events (tenant_id, timestamp);
"""


@dataclass
class RateLimitStatus:
    """Result of a rate-limit check."""

    allowed: bool
    daily_used: int
    daily_limit: int
    monthly_used: int
    monthly_limit: int
    retry_after_seconds: Optional[int] = field(default=None)
    overage_used: int = 0
    overage_charges_usd: float = 0.0

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SDK models and tier definitions for CashClaw."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Tier(Enum):
    """Subscription tiers with feature gating."""
    STARTER = "starter"
    PRO = "pro"
    ELITE = "elite"


@dataclass
class TierLimits:
    """Feature limits per tier."""
    signals_per_day: int
    ensemble_n: int
    dark_edge: bool
    custom_strategies: bool

    @classmethod
    def for_tier(cls, tier: Tier) -> TierLimits:
        limits = {
            Tier.STARTER: cls(signals_per_day=5, ensemble_n=1, dark_edge=False, custom_strategies=False),
            Tier.PRO: cls(signals_per_day=20, ensemble_n=3, dark_edge=True, custom_strategies=False),
            Tier.ELITE: cls(signals_per_day=999, ensemble_n=5, dark_edge=True, custom_strategies=True),
        }
        return limits.get(tier, limits[Tier.STARTER])


@dataclass
class SDKSignal:
    """A trading signal returned by the SDK."""
    market_id: str
    question: str
    direction: str
    predicted_probability: float
    market_price: float
    edge: float
    confidence: float
    kelly_fraction: float
    position_size_pct: float
    rank: int


@dataclass
class SDKMarket:
    """A market opportunity returned by the SDK."""
    market_id: str
    question: str
    volume_24h: float
    days_to_resolution: float
    yes_price: float
    no_price: float


@dataclass
class PaperStatus:
    """Paper trading status."""
    running: bool
    trades: int
    pnl: float
    win_rate: float
    capital: float
    brier_score: float

"""Mekong CLI - RaaS Pricing Engine.

Defines plan tiers, revenue projections, and unit economics
for the Recipe-as-a-Service business model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class PlanTier(str, Enum):
    """Subscription plan tiers."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class Plan:
    """Subscription plan definition."""

    tier: PlanTier
    name: str
    price_monthly: int  # USD
    credits: int  # MCU credits per month
    features: list[str]

    def credits_to_dollars(self, credits_used: int) -> float:
        """Calculate dollar value of credits consumed.

        Args:
            credits_used: Number of credits consumed.

        Returns:
            Dollar value based on per-credit rate.
        """
        if self.credits == 0:
            return 0.0
        rate = self.price_monthly / self.credits
        return round(rate * credits_used, 2)


# Plan catalog
_PLANS: Dict[PlanTier, Plan] = {
    PlanTier.FREE: Plan(
        tier=PlanTier.FREE,
        name="Free",
        price_monthly=0,
        credits=50,
        features=["5 recipes/day", "Community support", "Basic skills"],
    ),
    PlanTier.STARTER: Plan(
        tier=PlanTier.STARTER,
        name="Starter",
        price_monthly=29,
        credits=500,
        features=["50 recipes/day", "Email support", "All skills", "CI healer"],
    ),
    PlanTier.PRO: Plan(
        tier=PlanTier.PRO,
        name="Pro",
        price_monthly=99,
        credits=2500,
        features=[
            "Unlimited recipes", "Priority support",
            "Parallel review", "Custom skills", "AGI dashboard",
        ],
    ),
    PlanTier.TEAM: Plan(
        tier=PlanTier.TEAM,
        name="Team",
        price_monthly=249,
        credits=10000,
        features=[
            "Everything in Pro", "Team workspace",
            "SSO", "Audit logs", "Dedicated support",
        ],
    ),
    PlanTier.ENTERPRISE: Plan(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        price_monthly=0,  # Custom pricing
        credits=0,  # Unlimited
        features=[
            "Everything in Team", "Custom credits",
            "SLA", "On-prem option", "Dedicated CSM",
        ],
    ),
}


def get_plan(tier: PlanTier) -> Plan:
    """Get plan by tier.

    Args:
        tier: The plan tier to look up.

    Returns:
        Plan definition for the given tier.
    """
    return _PLANS[tier]


def list_plans() -> List[Plan]:
    """Return all available plans.

    Returns:
        List of all Plan objects.
    """
    return list(_PLANS.values())


@dataclass(frozen=True)
class UnitEconomics:
    """Key unit economics metrics."""

    cac: int = 50  # Customer Acquisition Cost
    ltv: int = 1188  # Lifetime Value (avg 36 months * $33 ARPU)
    ltv_cac_ratio: float = 23.8
    gross_margin: float = 0.85
    churn_monthly: float = 0.03


@dataclass(frozen=True)
class RevenueProjection:
    """Monthly revenue projection."""

    month: int
    mrr: int  # Monthly Recurring Revenue in USD
    paid_users: int
    free_users: int


def get_projections() -> List[RevenueProjection]:
    """Return 18-month revenue projections.

    Returns:
        List of monthly revenue projections.
    """
    return [
        RevenueProjection(month=3, mrr=2_000, paid_users=40, free_users=500),
        RevenueProjection(month=6, mrr=13_000, paid_users=200, free_users=3_000),
        RevenueProjection(month=12, mrr=47_000, paid_users=700, free_users=12_000),
        RevenueProjection(month=18, mrr=103_000, paid_users=1_500, free_users=30_000),
    ]


def get_unit_economics() -> UnitEconomics:
    """Return unit economics metrics.

    Returns:
        UnitEconomics dataclass with key metrics.
    """
    return UnitEconomics()


__all__ = [
    "Plan",
    "PlanTier",
    "RevenueProjection",
    "UnitEconomics",
    "get_plan",
    "get_projections",
    "get_unit_economics",
    "list_plans",
]

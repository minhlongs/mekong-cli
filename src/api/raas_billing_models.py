# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS API — MCU billing models and plan constants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List

PLAN_LIMITS: dict[str, int] = {
    "free": 100,
    "starter": 500,
    "growth": 2000,
    "pro": 5000,
    "enterprise": 50000,
}
KNOWN_PLANS = frozenset(PLAN_LIMITS.keys())

MCU_COSTS: dict[str, int] = {
    "simple": 1,
    "standard": 3,
    "complex": 5,
}
DEFAULT_MCU_COST = 1


@dataclass
class UsageEntry:
    """Single MCU usage record."""

    entry_id: str
    task_id: str
    mcu_cost: int
    balance_after: int
    timestamp: str


@dataclass
class TenantLedger:
    """Per-tenant MCU ledger."""

    tenant_id: str
    plan: str = "free"
    mcu_used: int = 0
    mcu_limit: int = PLAN_LIMITS["free"]
    history: List[UsageEntry] = field(default_factory=list)
    overage_credits: int = 0
    overage_charges_usd: Decimal = Decimal(0)

    @property
    def mcu_remaining(self) -> int:
        """Units remaining in current period."""
        return max(0, self.mcu_limit - self.mcu_used)

    @property
    def quota_exceeded(self) -> bool:
        """True when mcu_used >= mcu_limit."""
        return self.mcu_used >= self.mcu_limit

    @property
    def in_overage(self) -> bool:
        """True when usage exceeds plan limit."""
        return self.mcu_used > self.mcu_limit


__all__ = [
    "PLAN_LIMITS",
    "KNOWN_PLANS",
    "MCU_COSTS",
    "DEFAULT_MCU_COST",
    "UsageEntry",
    "TenantLedger",
]

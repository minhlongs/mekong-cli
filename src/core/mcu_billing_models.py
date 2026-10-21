# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and tier costs for MCU Billing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from src.seed.config.tiers import (
    mcu_costs_dict,
    tier_credits_dict,
)

# Backward-compatible aliases -- sourced from tiers.py
MCU_COSTS: dict[str, int] = mcu_costs_dict()
TIER_CREDITS: dict[str, int] = tier_credits_dict()

LOW_BALANCE_THRESHOLD = 10  # billing-specific threshold


@dataclass
class MCUTransaction:
    """Single MCU transaction record."""

    tenant_id: str
    amount: int
    balance_after: int
    transaction_type: Literal["credit", "debit", "refund"]
    description: str = ""
    mission_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "transaction_type": self.transaction_type,
            "description": self.description,
            "mission_id": self.mission_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TenantBalance:
    """Tenant MCU balance snapshot."""

    tenant_id: str
    balance: int = 0
    total_credited: int = 0
    total_debited: int = 0
    total_refunded: int = 0
    transactions: list[MCUTransaction] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "balance": self.balance,
            "total_credited": self.total_credited,
            "total_debited": self.total_debited,
            "total_refunded": self.total_refunded,
            "transaction_count": len(self.transactions),
        }


@dataclass
class DeductionResult:
    """Result of an MCU deduction attempt."""

    success: bool
    balance_before: int
    balance_after: int
    amount_deducted: int
    low_balance: bool = False
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "amount_deducted": self.amount_deducted,
            "low_balance": self.low_balance,
            "error": self.error,
        }


@dataclass
class PaymentResult:
    """Result of an x402/MPP payment settlement attempt.

    Stub type for future payment protocol (x402/MPP) integration.
    """

    pending: bool = True
    transaction_id: str = ""
    amount: float = 0.0
    currency: str = ""
    recipient: str = ""
    note: str = "x402/MPP settlement not yet implemented"

    def to_dict(self) -> dict:
        return {
            "pending": self.pending,
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "currency": self.currency,
            "recipient": self.recipient,
            "note": self.note,
        }


__all__ = [
    "MCU_COSTS",
    "TIER_CREDITS",
    "LOW_BALANCE_THRESHOLD",
    "MCUTransaction",
    "TenantBalance",
    "DeductionResult",
    "PaymentResult",
]

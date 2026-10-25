# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and constants for RaaS Billing Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

VALID_PLANS = {"free", "starter", "growth", "pro", "enterprise"}


@dataclass
class RateCard:
    """Rate card definition for pricing."""

    plan_tier: str
    event_type: str
    model_name: Optional[str]
    unit: str
    unit_price: Decimal
    included_quantity: Decimal
    overage_rate: Optional[Decimal]
    overage_threshold: Optional[Decimal]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_charge(
        self,
        quantity: Decimal,
        included_remaining: Optional[Decimal] = None,
    ) -> tuple[Decimal, Decimal]:
        """Calculate charge for a given quantity."""
        if included_remaining is None:
            included_remaining = self.included_quantity

        if quantity <= included_remaining:
            return Decimal(0), Decimal(0)

        overage = quantity - included_remaining
        rate = self.overage_rate if self.overage_rate is not None else self.unit_price
        charge = overage * rate
        return charge, overage


@dataclass
class LineItem:
    """Billing line item."""

    event_type: str
    model_name: Optional[str]
    quantity: Decimal
    unit: str
    unit_price: Decimal
    subtotal: Decimal
    discount: Decimal = Decimal(0)
    final_amount: Decimal = Decimal(0)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.final_amount == Decimal(0):
            self.final_amount = self.subtotal - self.discount

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_type": self.event_type,
            "model_name": self.model_name,
            "quantity": str(self.quantity),
            "unit": self.unit,
            "unit_price": str(self.unit_price),
            "subtotal": str(self.subtotal),
            "discount": str(self.discount),
            "final_amount": str(self.final_amount),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class BillingResult:
    """Result of billing calculation."""

    license_key: str
    key_id: str
    period_start: datetime
    period_end: datetime
    line_items: List[LineItem] = field(default_factory=list)
    subtotal: Decimal = Decimal(0)
    discount: Decimal = Decimal(0)
    total: Decimal = Decimal(0)
    currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "license_key": self.license_key,
            "key_id": self.key_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "line_items": [item.to_dict() for item in self.line_items],
            "subtotal": str(self.subtotal),
            "discount": str(self.discount),
            "total": str(self.total),
            "currency": self.currency,
            "metadata": self.metadata,
        }


__all__ = [
    "BillingResult",
    "LineItem",
    "RateCard",
    "VALID_PLANS",
]

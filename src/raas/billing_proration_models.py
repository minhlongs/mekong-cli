# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and overage tracker for RaaS Billing Proration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class ProrationResult:
    """Result of proration calculation."""

    license_key: str
    period_start: date
    period_end: date
    days_in_period: int
    days_elapsed: int
    days_remaining: int
    original_plan: str
    new_plan: Optional[str]
    prorated_base_fee: Decimal
    prorated_included_quantity: Dict[str, Decimal]
    overage_charges: Decimal
    total_charge: Decimal
    breakdown: Dict[str, Any]
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "license_key": self.license_key,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "days_in_period": self.days_in_period,
            "days_elapsed": self.days_elapsed,
            "days_remaining": self.days_remaining,
            "original_plan": self.original_plan,
            "new_plan": self.new_plan,
            "prorated_base_fee": str(self.prorated_base_fee),
            "prorated_included_quantity": {
                k: str(v) for k, v in self.prorated_included_quantity.items()
            },
            "overage_charges": str(self.overage_charges),
            "total_charge": str(self.total_charge),
            "breakdown": self.breakdown,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
        }


@dataclass
class OverageCalculation:
    """Overage charge calculation."""

    event_type: str
    model_name: Optional[str]
    total_usage: Decimal
    included_quantity: Decimal
    overage_quantity: Decimal
    unit_price: Decimal
    overage_rate: Decimal
    charge: Decimal
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_type": self.event_type,
            "model_name": self.model_name,
            "total_usage": str(self.total_usage),
            "included_quantity": str(self.included_quantity),
            "overage_quantity": str(self.overage_quantity),
            "unit_price": str(self.unit_price),
            "overage_rate": str(self.overage_rate),
            "charge": str(self.charge),
            "metadata": self.metadata,
        }


class OverageTracker:
    """Track and accumulate overage charges throughout a billing period."""

    def __init__(self) -> None:
        self._overage_by_type: Dict[str, OverageCalculation] = {}
        self._total_overage = Decimal(0)

    def add_overage(self, calculation: OverageCalculation) -> None:
        """Add or update an overage calculation."""
        event_type = calculation.event_type
        if event_type in self._overage_by_type:
            existing = self._overage_by_type[event_type]
            existing.overage_quantity += calculation.overage_quantity
            existing.total_usage = calculation.total_usage
            existing.charge += calculation.charge
        else:
            self._overage_by_type[event_type] = calculation

        self._total_overage += calculation.charge

    def get_total(self) -> Decimal:
        """Get total accumulated overage."""
        return self._total_overage

    def get_breakdown(self) -> List[Dict[str, Any]]:
        """Get breakdown of overage by type."""
        return [calc.to_dict() for calc in self._overage_by_type.values()]

    def reset(self) -> None:
        """Reset all tracking."""
        self._overage_by_type.clear()
        self._total_overage = Decimal(0)


__all__ = [
    "OverageCalculation",
    "OverageTracker",
    "ProrationResult",
]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Proration Calculator for mid-cycle plan changes and usage exceedances."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

from src.raas.billing_proration_models import (
    OverageCalculation,
    OverageTracker,
    ProrationResult,
)

logger = logging.getLogger(__name__)


class ProrationCalculator:
    """Calculate prorated charges for mid-cycle changes."""

    def calculate_proration(
        self,
        license_key: str,
        period_start: date,
        period_end: date,
        change_date: date,
        original_plan: str,
        new_plan: str,
        original_base_fee: Decimal,
        new_base_fee: Decimal,
        original_included: Dict[str, Decimal],
        new_included: Dict[str, Decimal],
    ) -> ProrationResult:
        days_in_period = max(1, (period_end - period_start).days)
        days_elapsed = max(0, (change_date - period_start).days)
        days_remaining = max(0, (period_end - change_date).days)

        orig_portion = Decimal(days_elapsed) / Decimal(days_in_period)
        new_portion = Decimal(days_remaining) / Decimal(days_in_period)
        prorated_base_fee = original_base_fee * orig_portion + new_base_fee * new_portion

        all_event_types = set(original_included.keys()) | set(new_included.keys())
        prorated_included = {
            et: original_included.get(et, Decimal(0)) * orig_portion
            + new_included.get(et, Decimal(0)) * new_portion
            for et in all_event_types
        }

        return ProrationResult(
            license_key=license_key, period_start=period_start, period_end=period_end,
            days_in_period=days_in_period, days_elapsed=days_elapsed, days_remaining=days_remaining,
            original_plan=original_plan, new_plan=new_plan,
            prorated_base_fee=round(prorated_base_fee, 2),
            prorated_included_quantity=prorated_included,
            overage_charges=Decimal(0), total_charge=round(prorated_base_fee, 2),
            breakdown={
                "original_portion": float(orig_portion),
                "new_portion": float(new_portion),
                "original_base_portion": str(original_base_fee * orig_portion),
                "new_base_portion": str(new_base_fee * new_portion),
            },
        )

    def calculate_overage(
        self,
        usage: Dict[str, Decimal],
        included_quantities: Dict[str, Decimal],
        rate_cards: Dict[str, Dict[str, Any]],
    ) -> tuple[Decimal, List[OverageCalculation]]:
        calculations: List[OverageCalculation] = []
        total_overage = Decimal(0)

        for event_type, used in usage.items():
            included = included_quantities.get(event_type, Decimal(0))
            if used <= included:
                continue

            overage_qty = used - included
            rate_info = rate_cards.get(event_type, {})
            unit_price = Decimal(str(rate_info.get("unit_price", 0)))
            overage_rate = Decimal(str(rate_info.get("overage_rate", unit_price)))
            charge = overage_qty * overage_rate
            total_overage += charge

            calculations.append(
                OverageCalculation(
                    event_type=event_type,
                    model_name=rate_info.get("model_name"),
                    total_usage=used, included_quantity=included, overage_quantity=overage_qty,
                    unit_price=unit_price, overage_rate=overage_rate, charge=round(charge, 4),
                    metadata={"overage_percentage": float((overage_qty / used * 100) if used > 0 else 0)},
                )
            )

        return total_overage, calculations

    def calculate_partial_day_overage(
        self,
        usage: Dict[str, Decimal],
        included_monthly: Dict[str, Decimal],
        days_in_period: int,
        days_remaining: int,
        rate_cards: Dict[str, Dict[str, Any]],
    ) -> tuple[Decimal, List[OverageCalculation]]:
        days_elapsed = days_in_period - days_remaining
        effective_allowance = {
            et: monthly * Decimal(days_elapsed) / Decimal(days_in_period)
            for et, monthly in included_monthly.items()
        }
        return self.calculate_overage(dict(usage), effective_allowance, rate_cards)

    def handle_plan_downgrade_credit(
        self,
        license_key: str,
        period_start: date,
        period_end: date,
        downgrade_date: date,
        original_fee: Decimal,
        new_fee: Decimal,
        already_charged: Decimal,
    ) -> tuple[Decimal, str]:
        days_in_period = max(1, (period_end - period_start).days)
        days_remaining = max(0, (period_end - downgrade_date).days)
        unused_portion = Decimal(days_remaining) / Decimal(days_in_period)
        credit = original_fee * unused_portion - new_fee * unused_portion
        if credit < 0:
            return Decimal(0), "No credit due (new plan exceeds unused original)"
        return round(credit, 2), f"Credit for {days_remaining} days remaining at {new_fee - original_fee} difference"


_calculator: Optional[ProrationCalculator] = None


def get_calculator() -> ProrationCalculator:
    global _calculator
    if _calculator is None:
        _calculator = ProrationCalculator()
    return _calculator


def reset_calculator() -> None:
    global _calculator
    _calculator = None


__all__ = [
    "ProrationResult", "OverageCalculation", "ProrationCalculator",
    "OverageTracker", "get_calculator", "reset_calculator",
]

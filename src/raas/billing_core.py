# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Billing Engine Core

Shim module — imports dataclasses and BillingEngine from billing_engine.py
and adds calculate_charge method to RateCard via mixin injection.
"""

from __future__ import annotations

from src.raas.billing_engine import (
  BillingEngine,
  BillingResult,
  LineItem,
  RateCard,
  RateCardResolver,
  get_engine,
)

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def _calculate_charge(
  self: RateCard,
  quantity: Decimal,
  included_remaining: "Decimal | None" = None,
) -> "tuple[Decimal, Decimal]":
  """Calculate charge for a given quantity.

  Args:
    quantity: Usage quantity
    included_remaining: Remaining included quantity
      (defaults to full included_quantity if None)

  Returns:
    Tuple of (charge_amount, overage_amount)
  """
  if included_remaining is None:
    included_remaining = self.included_quantity

  if quantity <= included_remaining:
    return Decimal(0), Decimal(0)

  overage = quantity - included_remaining
  rate = self.overage_rate if self.overage_rate is not None else self.unit_price
  charge = overage * rate
  return charge, overage


# Inject calculate_charge as a method on the imported RateCard dataclass.
# This avoids duplicating the dataclass definition while keeping the
# method close to the rate-card domain logic.
RateCard.calculate_charge = _calculate_charge  # type: ignore[attr-defined]

__all__ = [
  "RateCard",
  "LineItem",
  "BillingResult",
  "RateCardResolver",
  "BillingEngine",
  "get_engine",
]

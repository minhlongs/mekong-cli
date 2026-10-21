# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Provider-agnostic billing tier definitions and credit mapping.

Extracted from the former revenue_router so that NOWPayments and VietQR
rails share one tier→credit table independent of any payment provider.
"""

from __future__ import annotations

CREDIT_MAP = {
    "free": 50,
    "starter": 300,
    "growth": 1200,
    "scale": 3500,
    "pro": 7000,
}


def tier_from_reference(reference: str) -> str:
    """Derive billing tier from a payment reference string.

    Provider-neutral: shared by all payment rails (NOWPayments, VietQR,
    and any future rail) so that tier resolution never depends on a
    specific provider's session or invoice ID convention.
    """
    for tier in CREDIT_MAP:
        if tier in reference.lower():
            return tier
    return "starter"


__all__ = ["CREDIT_MAP", "tier_from_reference"]

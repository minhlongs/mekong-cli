# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS API — MCU billing middleware helpers (402 error builders and CreditStore deduction).
"""

from __future__ import annotations

import logging
import time

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _raise_402_no_credits(tenant_id: str) -> None:
    """Raise 402 when credit balance is zero."""
    now = int(time.time())
    midnight = now - (now % 86400) + 86400
    raise HTTPException(
        status_code=402,
        detail=(
            f"MCU credits exhausted for tenant {tenant_id}. "
            "Add credits at https://polar.sh/mekong."
        ),
        headers={
            "X-MCU-Remaining": "0",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(midnight),
            "Retry-After": str(midnight - now),
        },
    )


def _raise_402_quota_exceeded(tenant_id: str, balance: dict) -> None:
    """Raise 402 when quota is exceeded."""
    now = int(time.time())
    midnight = now - (now % 86400) + 86400
    raise HTTPException(
        status_code=402,
        detail=(
            f"MCU quota exceeded. Used {balance['mcu_used']} / "
            f"{balance['mcu_limit']} units. "
            "Upgrade your plan at https://polar.sh/mekong."
        ),
        headers={
            "X-RateLimit-Limit": str(balance["mcu_limit"]),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(midnight),
            "Retry-After": str(midnight - now),
        },
    )


def _deduct_credit_store(tenant_id: str, mcu_cost: int, reason: str) -> int:
    """Deduct from CreditStore for credit balance tracking, returning updated balance."""
    try:
        from src.raas.credits import CreditStore

        credit_store = CreditStore()
        credit_store.deduct(
            tenant_id=tenant_id,
            amount=mcu_cost,
            reason=reason,
        )
        return credit_store.get_balance(tenant_id)
    except Exception as e:
        logger.warning("billing.creditstore_deduct_failed: %s", e)
        return 0


__all__ = [
    "_raise_402_no_credits",
    "_raise_402_quota_exceeded",
    "_deduct_credit_store",
]

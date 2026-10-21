# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS API — MCU billing middleware: quota check before task execution.

FastAPI dependency that enforces MCU limits per tenant.
Raises 402 if quota exceeded OR credit balance is zero.
Records usage after task completes.
"""

from __future__ import annotations

import logging
import time

from fastapi import Depends

from src.api.raas_auth_middleware import require_tenant
from src.api.raas_billing_middleware_helpers import (
    _deduct_credit_store,
    _raise_402_no_credits,
    _raise_402_quota_exceeded,
)
from src.api.raas_billing_service import DEFAULT_MCU_COST, get_billing_service
from src.raas.auth import TenantContext

logger = logging.getLogger(__name__)


def require_billing(
    tenant: TenantContext = Depends(require_tenant),
) -> TenantContext:
    """FastAPI dependency — checks MCU quota AND credit balance before task execution."""
    service = get_billing_service()

    # Check 1: CreditStore balance (primary gate — zero balance = hard block)
    try:
        from src.raas.credits import CreditStore

        credit_store = CreditStore()
        balance = credit_store.get_balance(tenant.tenant_id)
        if balance <= 0:
            _raise_402_no_credits(tenant.tenant_id)
    except Exception as e:
        logger.warning("billing.creditstore_unavailable: %s", e)

    # Check 2: Quota-based check (BillingService)
    if not service.check_quota(tenant.tenant_id):
        balance_info = service.get_balance(tenant.tenant_id)
        _raise_402_quota_exceeded(tenant.tenant_id, balance_info)

    return tenant


def build_mcu_headers(tenant_id: str, mcu_cost: int) -> dict[str, str]:
    """Build MCU + standard rate-limit response headers."""
    service = get_billing_service()
    remaining = service.record_usage(
        tenant_id=tenant_id,
        mcu_cost=mcu_cost,
        task_id="",
    )
    balance = service.get_balance(tenant_id)
    credit_balance = _deduct_credit_store(tenant_id, mcu_cost, f"api_usage_{mcu_cost}mcu")

    now = int(time.time())
    midnight = now - (now % 86400) + 86400

    headers = {
        "X-MCU-Cost": str(mcu_cost),
        "X-MCU-Remaining": str(remaining),
        "X-MCU-Limit": str(balance["mcu_limit"]),
        "X-MCU-Credit-Balance": str(credit_balance),
        "X-RateLimit-Limit": str(balance["mcu_limit"]),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(midnight),
    }

    if balance.get("in_overage"):
        headers["X-Overage-Credits"] = str(balance["overage_credits"])
        headers["X-Overage-Charges-USD"] = str(balance["overage_charges_usd"])

    return headers


def record_task_usage(
    tenant_id: str,
    task_id: str,
    mcu_cost: int = DEFAULT_MCU_COST,
) -> dict[str, str]:
    """Record MCU usage for a completed task and return headers."""
    service = get_billing_service()
    remaining = service.record_usage(
        tenant_id=tenant_id,
        mcu_cost=mcu_cost,
        task_id=task_id,
    )
    balance = service.get_balance(tenant_id)
    credit_balance = _deduct_credit_store(
        tenant_id, mcu_cost, f"task_{task_id}_{mcu_cost}mcu"
    )

    return {
        "X-MCU-Cost": str(mcu_cost),
        "X-MCU-Remaining": str(remaining),
        "X-MCU-Limit": str(balance["mcu_limit"]),
        "X-MCU-Credit-Balance": str(credit_balance),
    }


__all__ = [
    "require_billing",
    "build_mcu_headers",
    "record_task_usage",
    "_raise_402_no_credits",
    "_raise_402_quota_exceeded",
]

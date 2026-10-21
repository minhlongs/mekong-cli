# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS API — MCU billing service: quota management and usage ledger per tenant."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional

from src.api.raas_billing_models import (
    DEFAULT_MCU_COST,
    KNOWN_PLANS,
    MCU_COSTS,
    PLAN_LIMITS,
    TenantLedger,
    UsageEntry,
)


class BillingService:
    """Thread-safe in-memory MCU billing ledger."""

    def __init__(self) -> None:
        self._ledgers: Dict[str, TenantLedger] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _get_or_create(self, tenant_id: str) -> TenantLedger:
        if tenant_id not in self._ledgers:
            self._ledgers[tenant_id] = TenantLedger(tenant_id=tenant_id)
        return self._ledgers[tenant_id]

    def _get_or_create_ledger(self, tenant_id: str) -> TenantLedger:
        return self._get_or_create(tenant_id)

    def charge_mcu(
        self,
        tenant_id: str,
        task_id: str,
        complexity: str = "simple",
        cost: Optional[int] = None,
    ) -> int:
        mcu_cost = cost if cost is not None else MCU_COSTS.get(complexity, DEFAULT_MCU_COST)
        return self.record_usage(tenant_id=tenant_id, mcu_cost=mcu_cost, task_id=task_id)

    def check_quota(self, tenant_id: str) -> bool:
        with self._lock:
            ledger = self._get_or_create(tenant_id)
            if not ledger.quota_exceeded:
                return True
            from src.raas.credit_rate_limiter import get_overage_config

            overage_cfg = get_overage_config(ledger.plan)
            if overage_cfg.allow_overage:
                current_overage = ledger.mcu_used - ledger.mcu_limit
                if (
                    overage_cfg.max_overage_credits > 0
                    and current_overage >= overage_cfg.max_overage_credits
                ):
                    return False
                return True
            return False

    def record_usage(self, tenant_id: str, mcu_cost: int, task_id: str) -> int:
        if mcu_cost < 0:
            raise ValueError(f"mcu_cost must be non-negative, got {mcu_cost}")
        with self._lock:
            ledger = self._get_or_create(tenant_id)
            ledger.mcu_used += mcu_cost
            if ledger.mcu_used > ledger.mcu_limit:
                from src.raas.credit_rate_limiter import get_overage_config

                overage_cfg = get_overage_config(ledger.plan)
                if overage_cfg.allow_overage:
                    new_overage = ledger.mcu_used - ledger.mcu_limit
                    ledger.overage_credits = new_overage
                    ledger.overage_charges_usd = Decimal(str(new_overage)) * Decimal(
                        str(overage_cfg.overage_rate_per_credit)
                    )
            entry = UsageEntry(
                entry_id=uuid.uuid4().hex,
                task_id=task_id,
                mcu_cost=mcu_cost,
                balance_after=ledger.mcu_remaining,
                timestamp=self._now_iso(),
            )
            ledger.history.append(entry)
            return ledger.mcu_remaining

    def get_balance(self, tenant_id: str) -> dict:
        with self._lock:
            ledger = self._get_or_create(tenant_id)
            return {
                "tenant_id": tenant_id,
                "plan": ledger.plan,
                "mcu_used": ledger.mcu_used,
                "mcu_limit": ledger.mcu_limit,
                "mcu_remaining": ledger.mcu_remaining,
                "overage_credits": ledger.overage_credits,
                "overage_charges_usd": ledger.overage_charges_usd,
                "in_overage": ledger.in_overage,
            }

    def get_history(self, tenant_id: str, limit: int = 50) -> list:
        with self._lock:
            ledger = self._get_or_create(tenant_id)
            entries = ledger.history[-limit:][::-1]
            return [
                {
                    "entry_id": e.entry_id,
                    "task_id": e.task_id,
                    "mcu_cost": e.mcu_cost,
                    "balance_after": e.balance_after,
                    "timestamp": e.timestamp,
                }
                for e in entries
            ]

    def update_plan(
        self,
        tenant_id: str,
        plan: str,
        mcu_limit: Optional[int] = None,
    ) -> dict:
        if plan not in PLAN_LIMITS:
            raise ValueError(
                f"Unknown plan {plan!r}. Valid plans: {sorted(PLAN_LIMITS.keys())}"
            )
        with self._lock:
            ledger = self._get_or_create(tenant_id)
            ledger.plan = plan
            ledger.mcu_limit = mcu_limit or PLAN_LIMITS[plan]
            return {
                "tenant_id": tenant_id,
                "plan": ledger.plan,
                "mcu_limit": ledger.mcu_limit,
            }


_service: Optional[BillingService] = None


def get_billing_service() -> BillingService:
    """Return the module-level BillingService singleton."""
    global _service
    if _service is None:
        _service = BillingService()
    return _service


__all__ = [
    "BillingService",
    "UsageEntry",
    "TenantLedger",
    "PLAN_LIMITS",
    "KNOWN_PLANS",
    "MCU_COSTS",
    "DEFAULT_MCU_COST",
    "get_billing_service",
]

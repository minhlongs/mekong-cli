# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong MCU Billing — Mission Credit Unit accounting system facade."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from src.core.mcu_billing_models import (
    LOW_BALANCE_THRESHOLD,
    MCU_COSTS,
    TIER_CREDITS,
    DeductionResult,
    MCUTransaction,
    PaymentResult,
    TenantBalance,
)
from src.core.mcu_billing_store import (
    build_tenant_from_store,
    count_tenants_in_store,
    deduct_from_store,
    extract_mission_id,
    has_account_record,
    trigger_low_balance_webhook,
)
from src.core.protocols import QuotaStatus

logger = logging.getLogger(__name__)


class MCUBilling:
    """MCU billing engine backed by SQLite WAL (CreditStore)."""

    def __init__(
        self,
        low_threshold: int = LOW_BALANCE_THRESHOLD,
        webhook_handler: Optional[Callable[[str, dict], None]] = None,
        db_path: Optional[str] = None,
    ) -> None:
        from src.raas.credits import CreditStore

        kwargs = {"db_path": Path(db_path)} if db_path else {}
        self._store = CreditStore(**kwargs)
        self.low_threshold = low_threshold
        self._webhook_handler = webhook_handler
        self._notified_tenants: set[str] = set()

    def _build_tenant(self, tenant_id: str) -> TenantBalance | None:
        return build_tenant_from_store(self._store, tenant_id)

    @staticmethod
    def _extract_mission_id(reason: str) -> str:
        return extract_mission_id(reason)

    def add_credits(
        self, tenant_id: str, amount: int, description: str = ""
    ) -> TenantBalance:
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        self._store.add_credits(
            tenant_id, amount, description or f"Added {amount} MCU"
        )
        return self._build_tenant(tenant_id)  # type: ignore[return-value]

    def deduct(
        self,
        tenant_id: str,
        complexity: str = "simple",
        mission_id: str = "",
    ) -> DeductionResult:
        result = deduct_from_store(
            self._store, tenant_id, complexity, mission_id, self.low_threshold
        )
        if result.low_balance and tenant_id not in self._notified_tenants:
            self._trigger_low_balance_webhook(tenant_id, result.balance_after)
            self._notified_tenants.add(tenant_id)
        return result

    def refund(
        self,
        tenant_id: str,
        amount: int,
        mission_id: str = "",
    ) -> TenantBalance | None:
        if amount <= 0:
            raise ValueError("Refund amount must be positive")
        existing = self._store.get_balance(tenant_id)
        if not has_account_record(self._store, tenant_id) and existing == 0:
            return None
        reason = f"Refund {amount} MCU"
        if mission_id:
            reason += f" {mission_id}"
        self._store.add_credits(tenant_id, amount, reason)
        return self._build_tenant(tenant_id)  # type: ignore[return-value]

    def get_balance(self, tenant_id: str) -> int:
        return self._store.get_balance(tenant_id)

    def check_quota(self, tenant_id: str) -> QuotaStatus:
        balance = self.get_balance(tenant_id)
        tier = "basic"
        if hasattr(self, "_get_tier_for_org"):
            try:
                tier = self._get_tier_for_org(tenant_id)
            except Exception:
                pass
        return QuotaStatus(
            remaining_mcu=balance,
            total_mcu=balance,
            tier=tier,
            reset_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_tenant(self, tenant_id: str) -> TenantBalance | None:
        return self._build_tenant(tenant_id)

    def is_low_balance(self, tenant_id: str) -> bool:
        return self.get_balance(tenant_id) < self.low_threshold

    def settle_payment(
        self, amount: float, currency: str, recipient: str
    ) -> PaymentResult:
        return PaymentResult(
            pending=True,
            amount=amount,
            currency=currency,
            recipient=recipient,
            note="x402/MPP settlement not yet implemented",
        )

    def record_usage(
        self, agent: str, tokens: int, model: str, operation: str
    ) -> None:
        if tokens < 0:
            raise ValueError("Token count must be non-negative")
        logger.info(
            "Usage recorded: agent=%s tokens=%d model=%s operation=%s",
            agent, tokens, model, operation,
        )

    def _trigger_low_balance_webhook(self, tenant_id: str, balance: int) -> None:
        trigger_low_balance_webhook(
            self._webhook_handler, tenant_id, balance, self.low_threshold
        )

    def reset_low_balance_notification(self, tenant_id: str) -> None:
        self._notified_tenants.discard(tenant_id)

    @property
    def tenant_count(self) -> int:
        return count_tenants_in_store(self._store)


__all__ = [
    "MCUBilling",
    "MCUTransaction",
    "TenantBalance",
    "DeductionResult",
    "PaymentResult",
    "MCU_COSTS",
    "TIER_CREDITS",
    "LOW_BALANCE_THRESHOLD",
]

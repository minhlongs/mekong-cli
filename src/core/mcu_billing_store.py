# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Store helpers and extraction logic for MCU Billing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Literal

from src.core.mcu_billing_models import (
    MCU_COSTS,
    DeductionResult,
    MCUTransaction,
    TenantBalance,
)

logger = logging.getLogger(__name__)


def extract_mission_id(reason: str) -> str:
    """Extract mission id string from transaction reason."""
    for part in reason.split():
        if part.startswith("m-") or part.startswith("m_"):
            return part
    return ""


def build_tenant_from_store(store: Any, tenant_id: str) -> TenantBalance | None:
    """Build TenantBalance from DB store state."""
    conn = store._connect()
    try:
        row = conn.execute(
            "SELECT balance, total_earned, total_spent "
            "FROM credit_accounts WHERE tenant_id = ?",
            (tenant_id,),
        ).fetchone()
        if not row:
            return None
        txs = conn.execute(
            "SELECT amount, reason, timestamp "
            "FROM credit_transactions WHERE tenant_id = ? ORDER BY timestamp",
            (tenant_id,),
        ).fetchall()
    finally:
        conn.close()

    total_refunded = 0
    transactions: list[MCUTransaction] = []
    for tx in txs:
        amt = int(tx["amount"])
        reason = tx["reason"]
        is_refund = "refund" in reason.lower()
        if is_refund:
            tx_type: Literal["credit", "debit", "refund"] = "refund"
            total_refunded += amt
        elif amt >= 0:
            tx_type = "credit"
        else:
            tx_type = "debit"
        transactions.append(
            MCUTransaction(
                tenant_id=tenant_id,
                amount=amt,
                balance_after=0,
                transaction_type=tx_type,
                description=reason,
                mission_id=extract_mission_id(reason),
            )
        )

    return TenantBalance(
        tenant_id=tenant_id,
        balance=int(row["balance"]),
        total_credited=int(row["total_earned"]),
        total_debited=int(row["total_spent"]),
        total_refunded=total_refunded,
        transactions=transactions,
    )


def deduct_from_store(
    store: Any,
    tenant_id: str,
    complexity: str,
    mission_id: str,
    low_threshold: int,
) -> DeductionResult:
    """Execute credit deduction in CreditStore."""
    cost = MCU_COSTS.get(complexity, MCU_COSTS["simple"])
    balance_before = store.get_balance(tenant_id)
    if balance_before < cost:
        return DeductionResult(
            success=False,
            balance_before=balance_before,
            balance_after=balance_before,
            amount_deducted=0,
            error=f"Insufficient MCU: need {cost}, have {balance_before}",
        )
    reason = f"Mission {complexity} ({cost} MCU)"
    if mission_id:
        reason += f" {mission_id}"
    success = store.deduct(tenant_id, cost, reason)
    balance_after = store.get_balance(tenant_id)
    return DeductionResult(
        success=success,
        balance_before=balance_before,
        balance_after=balance_after,
        amount_deducted=cost if success else 0,
        low_balance=balance_after < low_threshold,
    )


def count_tenants_in_store(store: Any) -> int:
    """Count number of registered credit accounts."""
    try:
        conn = store._connect()
        try:
            row = conn.execute("SELECT COUNT(*) FROM credit_accounts").fetchone()
            return int(row[0]) if row else 0
        finally:
            conn.close()
    except Exception:
        return 0


def has_account_record(store: Any, tenant_id: str) -> bool:
    """Check if account record exists in store."""
    conn = store._connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM credit_accounts WHERE tenant_id = ?",
            (tenant_id,),
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


def trigger_low_balance_webhook(
    handler: Callable[[str, dict], None] | None,
    tenant_id: str,
    balance: int,
    low_threshold: int,
) -> None:
    """Dispatch credits.low webhook notification safely."""
    if not handler:
        return
    payload = {
        "event_type": "credits.low",
        "tenant_id": tenant_id,
        "current_balance": balance,
        "threshold": low_threshold,
        "currency": "MCU",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        handler("credits.low", payload)
    except Exception as e:
        logger.warning("MCU billing error: %s", e)


__all__ = [
    "extract_mission_id",
    "build_tenant_from_store",
    "deduct_from_store",
    "count_tenants_in_store",
    "has_account_record",
    "trigger_low_balance_webhook",
]

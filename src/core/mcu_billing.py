# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong MCU Billing — Mission Credit Unit accounting system.

Backed by SQLite WAL via CreditStore for atomic, persistent operations.
The in-memory dict store is gone; all state lives in ~/.mekong/credits.db.

Usage:
from src.core.mcu_billing import MCUBilling, MCU_COSTS
billing = MCUBilling()
billing.add_credits("tenant-123", 100)
result = billing.deduct("tenant-123", "standard")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Literal, Optional

from src.seed.config.tiers import (
    mcu_costs_dict,
    tier_credits_dict,
)

logger = logging.getLogger(__name__)

# Backward-compatible aliases -- sourced from tiers.py
MCU_COSTS: dict[str, int] = mcu_costs_dict()
TIER_CREDITS: dict[str, int] = tier_credits_dict()

LOW_BALANCE_THRESHOLD = 10  # billing-specific threshold


@dataclass
class MCUTransaction:
    """Single MCU transaction record."""

    tenant_id: str
    amount: int
    balance_after: int
    transaction_type: Literal["credit", "debit", "refund"]
    description: str = ""
    mission_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "transaction_type": self.transaction_type,
            "description": self.description,
            "mission_id": self.mission_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TenantBalance:
    """Tenant MCU balance snapshot."""

    tenant_id: str
    balance: int = 0
    total_credited: int = 0
    total_debited: int = 0
    total_refunded: int = 0
    transactions: list[MCUTransaction] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "balance": self.balance,
            "total_credited": self.total_credited,
            "total_debited": self.total_debited,
            "total_refunded": self.total_refunded,
            "transaction_count": len(self.transactions),
        }


@dataclass
class DeductionResult:
    """Result of an MCU deduction attempt."""

    success: bool
    balance_before: int
    balance_after: int
    amount_deducted: int
    low_balance: bool = False
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "amount_deducted": self.amount_deducted,
            "low_balance": self.low_balance,
            "error": self.error,
        }


@dataclass
class PaymentResult:
    """Result of an x402/MPP payment settlement attempt.

    Stub type for future payment protocol (x402/MPP) integration.
    """

    pending: bool = True
    transaction_id: str = ""
    amount: float = 0.0
    currency: str = ""
    recipient: str = ""
    note: str = "x402/MPP settlement not yet implemented"

    def to_dict(self) -> dict:
        return {
            "pending": self.pending,
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "currency": self.currency,
            "recipient": self.recipient,
            "note": self.note,
        }


class MCUBilling:
    """MCU billing engine backed by SQLite WAL (CreditStore).

    All balance mutations are atomic via BEGIN EXCLUSIVE transactions.
    State survives process restarts and is consistent across instances
    sharing the same database file.

    Protocol compliance: designed to satisfy the BillingMeter protocol
    (src/core/protocols.py once available). Implements settle_payment
    and record_usage as x402/MPP extension points.
    """

    def __init__(
        self,
        low_threshold: int = LOW_BALANCE_THRESHOLD,
        webhook_handler: Optional[Callable[[str, dict], None]] = None,
        db_path: Optional[str] = None,
    ) -> None:
        from pathlib import Path
        from src.raas.credits import CreditStore

        kwargs = {"db_path": Path(db_path)} if db_path else {}
        self._store = CreditStore(**kwargs)
        self.low_threshold = low_threshold
        self._webhook_handler = webhook_handler
        self._notified_tenants: set[str] = set()

    def _build_tenant(self, tenant_id: str) -> TenantBalance | None:
        """Build TenantBalance from DB state."""
        conn = self._store._connect()
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
                    mission_id=self._extract_mission_id(reason),
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

    @staticmethod
    def _extract_mission_id(reason: str) -> str:
        for part in reason.split():
            if part.startswith("m-") or part.startswith("m_"):
                return part
        return ""

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
        cost = MCU_COSTS.get(complexity, MCU_COSTS["simple"])
        balance_before = self._store.get_balance(tenant_id)

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
        success = self._store.deduct(tenant_id, cost, reason)
        balance_after = self._store.get_balance(tenant_id)

        result = DeductionResult(
            success=success,
            balance_before=balance_before,
            balance_after=balance_after,
            amount_deducted=cost if success else 0,
            low_balance=balance_after < self.low_threshold,
        )

        if result.low_balance and tenant_id not in self._notified_tenants:
            self._trigger_low_balance_webhook(tenant_id, balance_after)
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
        conn = self._store._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM credit_accounts WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        if not row and existing == 0:
            return None

        reason = f"Refund {amount} MCU"
        if mission_id:
            reason += f" {mission_id}"
        self._store.add_credits(tenant_id, amount, reason)
        return self._build_tenant(tenant_id)  # type: ignore[return-value]

    def get_balance(self, tenant_id: str) -> int:
        return self._store.get_balance(tenant_id)

    def get_tenant(self, tenant_id: str) -> TenantBalance | None:
        return self._build_tenant(tenant_id)

    def is_low_balance(self, tenant_id: str) -> bool:
        return self.get_balance(tenant_id) < self.low_threshold

    def settle_payment(
        self,
        amount: float,
        currency: str,
        recipient: str,
    ) -> PaymentResult:
        """x402/MPP settlement stub.

        TODO: Implement real payment protocol (x402 or MPP) integration
        when payment providers are available. Currently returns a pending
        result to preserve the API contract for callers.

        Args:
            amount: Payment amount in the given currency.
            currency: ISO 4217 currency code (e.g. "USD", "VND").
            recipient: Payment recipient identifier.

        Returns:
            PaymentResult with pending=True and a descriptive note.
        """
        # TODO(x402): Replace with real payment protocol implementation.
        return PaymentResult(
            pending=True,
            amount=amount,
            currency=currency,
            recipient=recipient,
            note="x402/MPP settlement not yet implemented",
        )

    def record_usage(
        self,
        agent: str,
        tokens: int,
        model: str,
        operation: str,
    ) -> None:
        """Record per-operation usage for an agent.

        Args:
            agent: Agent identifier (tenant or agent name).
            tokens: Number of tokens consumed.
            model: LLM model identifier used.
            operation: Operation type (e.g. "chat", "embedding", "video").

        Raises:
            ValueError: If tokens is negative.
        """
        if tokens < 0:
            raise ValueError("Token count must be non-negative")

        logger.info(
            "Usage recorded: agent=%s tokens=%d model=%s operation=%s",
            agent,
            tokens,
            model,
            operation,
        )

    def _trigger_low_balance_webhook(self, tenant_id: str, balance: int) -> None:
        if not self._webhook_handler:
            return
        payload = {
            "event_type": "credits.low",
            "tenant_id": tenant_id,
            "current_balance": balance,
            "threshold": self.low_threshold,
            "currency": "MCU",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self._webhook_handler("credits.low", payload)
        except Exception as e:
            logger.warning("MCU billing error: %s", e)

    def reset_low_balance_notification(self, tenant_id: str) -> None:
        self._notified_tenants.discard(tenant_id)

    @property
    def tenant_count(self) -> int:
        try:
            conn = self._store._connect()
            try:
                row = conn.execute(
                    "SELECT COUNT(*) FROM credit_accounts"
                ).fetchone()
                return int(row[0]) if row else 0
            finally:
                conn.close()
        except Exception:
            return 0


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

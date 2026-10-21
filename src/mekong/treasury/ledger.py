# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""treasury/ledger.py — Append-only transaction log for ZenOS Commons Treasury."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.mekong.treasury.ledger_queries import TreasuryLedgerQueriesMixin
from src.mekong.treasury.models import (
    DEFAULT_ALLOCATIONS,
    Currency,
    DuplicateTxError,
    InsufficientFundsError,
    Transaction,
    TransactionKind,
    TransactionStatus,
    TreasuryError,
    TreasurySnapshot,
    WithdrawalRequest,
    new_tx_id,
)


@dataclass
class TreasuryLedger(TreasuryLedgerQueriesMixin):
    """Append-only transaction log."""

    currency: Currency = Currency.USD
    allocations: list = field(default_factory=lambda: list(DEFAULT_ALLOCATIONS))
    _seq: int = 0
    _rows: list[Transaction] = field(default_factory=list)
    _by_id: dict[str, Transaction] = field(default_factory=dict)
    _snapshots: list = field(default_factory=list)

    def record_income(
        self,
        amount: float,
        *,
        source: str,
        bucket: Optional[str] = None,
        metadata: Optional[dict] = None,
        at: Optional[datetime] = None,
    ) -> Transaction:
        if amount <= 0:
            raise TreasuryError(f"Income amount must be positive, got {amount}")
        tx = self._make_tx(
            kind="INCOME",
            amount=abs(amount),
            bucket=bucket,
            source=source,
            destination=None,
            metadata=metadata,
            at=at,
        )
        self._append(tx)
        return tx

    def initiate_withdrawal(
        self,
        amount: float,
        *,
        destination: str,
        bucket: Optional[str] = None,
        purpose: str = "",
        requested_by: str = "unknown",
        at: Optional[datetime] = None,
    ) -> WithdrawalRequest:
        return WithdrawalRequest(
            request_id=new_tx_id("wd"),
            amount=abs(amount),
            currency=self.currency,
            destination=destination,
            purpose=purpose,
            requested_by=requested_by,
        )

    def execute_withdrawal(
        self,
        req: WithdrawalRequest,
        approver: str,
        *,
        approved_bypass_all: bool = False,
        at: Optional[datetime] = None,
    ) -> Transaction:
        if req.amount <= 0:
            raise TreasuryError("Withdrawal amount must be positive")
        total = self.balance()
        if req.amount > total:
            raise InsufficientFundsError(
                f"Withdrawal {req.amount} {req.currency.value} exceeds total balance {total:.2f}"
            )
        tx = self._make_tx(
            kind="WITHDRAWAL",
            amount=-abs(req.amount),
            bucket=req.destination,
            source=None,
            destination=req.destination,
            metadata={},
            at=at,
        )
        tx.executed_by = approver
        tx.approval_tx_id = req.request_id
        tx.status = TransactionStatus.APPROVED if approved_bypass_all else TransactionStatus.PENDING
        self._append(tx)
        return tx

    def reverse(
        self,
        tx_id: str,
        *,
        by: str,
        reason: str = "",
        at: Optional[datetime] = None,
    ) -> Transaction:
        original = self._by_id.get(tx_id)
        if original is None:
            raise TreasuryError(f"Transaction not found: {tx_id}")
        if not original.is_reversible():
            raise TreasuryError(f"Transaction {tx_id} is not reversible (status={original.status.value})")
        reversal = Transaction(
            tx_id=new_tx_id("rev"),
            kind=TransactionKind.REVERSAL,
            currency=original.currency,
            amount=-original.amount,
            bucket=original.bucket,
            source=original.destination,
            destination=original.source,
            status=TransactionStatus.EXECUTED,
            executed_by=by,
            metadata={"reverses_tx_id": tx_id, "reason": reason or "reversal"},
        )
        self._append(reversal)
        return reversal

    def _make_tx(
        self,
        *,
        kind: str,
        amount: float,
        bucket: Optional[str],
        source: Optional[str],
        destination: Optional[str],
        metadata: Optional[dict],
        at: Optional[datetime],
    ) -> Transaction:
        self._seq += 1
        return Transaction(
            tx_id=new_tx_id(),
            kind=TransactionKind(kind.upper()),
            currency=self.currency,
            amount=float(amount),
            bucket=bucket,
            source=source,
            destination=destination,
            status=TransactionStatus.EXECUTED,
            created_at=at or datetime.now(timezone.utc),
            executed_at=at or datetime.now(timezone.utc),
            metadata=metadata or {},
        )

    def _append(self, tx: Transaction) -> None:
        if tx.tx_id in self._by_id:
            raise DuplicateTxError(f"Duplicate transaction id: {tx.tx_id}")
        self._rows.append(tx)
        self._by_id[tx.tx_id] = tx


__all__ = [
    "Currency", "DEFAULT_ALLOCATIONS", "DuplicateTxError", "InsufficientFundsError",
    "Transaction", "TransactionKind", "TransactionStatus", "TreasuryError",
    "TreasuryLedger", "TreasurySnapshot", "WithdrawalRequest", "new_tx_id",
]

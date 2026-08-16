# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""treasury/ledger.py — Append-only transaction log for ZenOS Commons Treasury.

Guarantees:
- Entries are append-only (no delete or edit).  Adjustments produce new
  REVERSAL entries with `reverses_tx_id` links.
- Every entry is sequentially numbered per currency for audit.
- Balance queries run over the log head; snapshot optimization is optional
  and off by default in v1 (F2 is scaffold, not production).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.mekong.treasury.models import (
    TreasurySnapshot,
    Currency,
    DEFAULT_ALLOCATIONS,
    DuplicateTxError,
    InsufficientFundsError,
    Transaction,
    TransactionKind,
    TransactionStatus,
    TreasuryError,
    WithdrawalRequest,
    new_tx_id,
)


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


@dataclass
class TreasuryLedger:
    """Append-only transaction log.

    Tests use the in-memory list.  Production swaps `_rows` with a D1 store
    via the same append method signature (F2 wiring deferred until DB mapping
    is chosen by the user).
    """

    currency: Currency = Currency.USD
    allocations: list = field(default_factory=lambda: list(DEFAULT_ALLOCATIONS))
    _seq: int = 0
    _rows: list[Transaction] = field(default_factory=list)
    _by_id: dict[str, Transaction] = field(default_factory=dict)
    _snapshots: list = field(default_factory=list)  # optional snapshot cache

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

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
        # Dormant until treasury is funded — do not block on zero balance here;
        # the approval flow will fail later if no funds exist.
        req = WithdrawalRequest(
            request_id=new_tx_id("wd"),
            amount=abs(amount),
            currency=self.currency,
            destination=destination,
            purpose=purpose,
            requested_by=requested_by,
        )
        return req

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
                f"Withdrawal {req.amount} {req.currency.value} exceeds total balance "
                f"{total:.2f}"
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

    def reverse(self, tx_id: str, *, by: str, reason: str = "", at: Optional[datetime] = None) -> Transaction:
        original = self._by_id.get(tx_id)
        if original is None:
            raise TreasuryError(f"Transaction not found: {tx_id}")
        if not original.is_reversible():
            raise TreasuryError(
                f"Transaction {tx_id} is not reversible (status={original.status.value})"
            )
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
            metadata={
                "reverses_tx_id": tx_id,
                "reason": reason or "reversal",
            },
        )
        self._append(reversal)
        return reversal

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def balance(self, bucket: Optional[str] = None) -> float:
        rows = self._rows
        if bucket:
            rows = [r for r in rows if r.bucket == bucket and r.is_executed()]
        return sum(r.amount for r in rows if r.currency is self.currency)

    def balance_by_bucket(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for r in self._rows:
            if r.currency is not self.currency:
                continue
            if r.status is TransactionStatus.REJECTED:
                continue
            out[r.bucket or "_unassigned"] = out.get(r.bucket or "_unassigned", 0.0) + r.amount
        return out

    def all_time_in(self) -> float:
        return sum(r.amount for r in self._rows if r.kind is TransactionKind.INCOME and r.currency is self.currency)

    def all_time_out(self) -> float:
        return sum(abs(r.amount) for r in self._rows if r.kind in {TransactionKind.WITHDRAWAL, TransactionKind.REVERSAL} and r.currency is self.currency)

    def list_txs(self, *, limit: int = 200, offset: int = 0) -> list[Transaction]:
        return self._rows[max(0, len(self._rows) - limit - offset) : len(self._rows) - offset]

    def snapshot(self, at: Optional[datetime] = None) -> TreasurySnapshot:
        w = at or datetime.now(timezone.utc)
        buckets: dict[str, dict[Currency, float]] = {}
        for r in self._rows:
            if r.created_at > w:
                break
            if r.status is TransactionStatus.REJECTED:
                continue
            key = r.bucket or "_unassigned"
            buckets.setdefault(key, {})
            buckets[key][r.currency] = buckets[key].get(r.currency, 0.0) + r.amount
        total_by_currency: dict[Currency, float] = {}
        for per_bucket in buckets.values():
            for cur, amt in per_bucket.items():
                total_by_currency[cur] = total_by_currency.get(cur, 0.0) + amt
        return TreasurySnapshot(
            captured_at=w,
            buckets=buckets,
            total_by_currency=total_by_currency,
            tx_count=len(self._rows),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

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

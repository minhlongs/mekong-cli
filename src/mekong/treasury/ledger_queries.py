# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Read-only query and snapshot helpers for TreasuryLedger."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from src.mekong.treasury.models import (
    Currency,
    Transaction,
    TransactionKind,
    TransactionStatus,
    TreasurySnapshot,
)


class TreasuryLedgerQueriesMixin:
    """Query and snapshot methods mixed into TreasuryLedger."""

    currency: Currency
    _rows: list[Transaction]

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
        return sum(
            r.amount
            for r in self._rows
            if r.kind is TransactionKind.INCOME and r.currency is self.currency
        )

    def all_time_out(self) -> float:
        return sum(
            abs(r.amount)
            for r in self._rows
            if r.kind in {TransactionKind.WITHDRAWAL, TransactionKind.REVERSAL}
            and r.currency is self.currency
        )

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

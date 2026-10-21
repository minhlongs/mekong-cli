# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""treasury/service.py — Treasury service for ZenOS Commons."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.mekong.treasury.allocation import AllocationResult, AllocationService
from src.mekong.treasury.ledger import TreasuryLedger
from src.mekong.treasury.models import (
    DEFAULT_ALLOCATIONS, ApprovalRequiredError, Currency,
    Transaction, TreasuryError, WithdrawalRequest,
)


@dataclass
class TreasuryService:
    """Top-level treasury façade orchestrating ledger and bucket allocations."""

    ledger: TreasuryLedger = field(default_factory=lambda: TreasuryLedger(currency=Currency.USD))
    allocation_service: AllocationService = field(
        default_factory=lambda: AllocationService(allocations=list(DEFAULT_ALLOCATIONS), currency=Currency.USD)
    )
    treasury_threshold: float = 5000.0
    member_count: int = 0

    def record_income(
        self, amount: float, *, currency: Currency = Currency.USD, source: str,
        bucket: Optional[str] = None, metadata: Optional[dict] = None, at: Optional[datetime] = None,
    ) -> tuple[Transaction, Optional[AllocationResult]]:
        """Record incoming funds and split per allocation rules."""
        if currency is not self.ledger.currency:
            raise TreasuryError(f"Currency mismatch: ledger={self.ledger.currency.value}, requested={currency.value}")
        income_tx = self.ledger.record_income(amount=amount, source=source, bucket=bucket, metadata=metadata, at=at)
        alloc = self.allocation_service.apply(income_tx, allocation_tx_factory=self._allocation_tx_factory(currency), at=at)
        return income_tx, alloc

    def balance(self) -> float:
        return self.ledger.balance()

    def balance_by_bucket(self) -> dict[str, float]:
        return self.ledger.balance_by_bucket()

    def snapshot(self, at: Optional[datetime] = None) -> object:
        return self.ledger.snapshot(at=at)

    def propose_withdrawal(
        self, amount: float, *, destination: str, purpose: str = "",
        requested_by: str = "unknown", at: Optional[datetime] = None,
    ) -> tuple[WithdrawalRequest, str]:
        """Initiate a withdrawal request and return (request, route)."""
        if amount <= 0:
            raise TreasuryError("Withdrawal amount must be positive")
        req = self.ledger.initiate_withdrawal(
            amount=amount, destination=destination, purpose=purpose, requested_by=requested_by, at=at
        )
        route = "quorum" if (amount > self.treasury_threshold and self.member_count >= 3) else ("founder_gate" if self.member_count < 3 else "direct")
        return req, route

    def approve_withdrawal(
        self,
        req: WithdrawalRequest,
        approver: str,
        *,
        approved_bypass_all: bool = False,
        at: Optional[datetime] = None,
    ) -> Transaction:
        if req.amount > self.treasury_threshold and not approved_bypass_all and self.member_count >= 3:
            raise ApprovalRequiredError(
                f"Withdrawal {req.amount} exceeds treasury_threshold={self.treasury_threshold} "
                f"and requires L2 supermajority"
            )
        tx = self.ledger.execute_withdrawal(
            req, approver=approver, approved_bypass_all=approved_bypass_all, at=at
        )
        return tx

    def list_transactions(self, *, limit: int = 200, offset: int = 0) -> list[Transaction]:
        return self.ledger.list_txs(limit=limit, offset=offset)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _allocation_tx_factory(self, currency: Currency):  # returns a callable
        def _factory(
            kind: str,
            amount: float,
            bucket: Optional[str],
            metadata: Optional[dict],
            at: Optional[object],
        ) -> Transaction:
            return self.ledger._make_tx(
                kind=kind,
                amount=amount,
                bucket=bucket,
                source=metadata.get("source_tx_id") if metadata else None,
                destination=bucket,
                metadata=metadata,
                at=at,  # type: ignore[arg-type]
            )
        return _factory

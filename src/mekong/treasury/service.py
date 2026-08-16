# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""treasury/service.py — Treasury service for ZenOS Commons.

Orchestrates ledger + allocation.  All public methods raise `TreasuryError`
(and subclasses) on invalid state; no silent failures.

Runtime gate: withdrawal > `treasury_threshold` requires L2 supermajority when
`commons_member_count >= 3`.  Below that threshold the service accepts but
marks the request `FOUNDER_REVIEW` — real approval paths land in F2 when the
vote engine wires into it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.mekong.treasury.allocation import AllocationResult, AllocationService
from src.mekong.treasury.ledger import TreasuryLedger
from src.mekong.treasury.models import (
    ApprovalRequiredError,
    Currency,
    Transaction,
    TreasuryError,
    WithdrawalRequest,
)
from src.mekong.treasury.models import DEFAULT_ALLOCATIONS  # re-export for CLI


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


@dataclass
class TreasuryService:
    """Top-level treasury façade.

    Parameters
    ----------
    ledger:
        Append-only transaction store.  Defaults to USD; override via factory.
    allocation_service:
        Splits income across buckets.  Defaults to ZENOS-COMMONS Art 5 split.
    treasury_threshold:
        Withdrawals above this amount in the service currency require L2
        supermajority approval.  Default $5,000 per the plan.
    member_count:
        Updated by the registry; used to gate the founder override path.
    """

    ledger: TreasuryLedger = field(default_factory=lambda: TreasuryLedger(currency=Currency.USD))
    allocation_service: AllocationService = field(
        default_factory=lambda: AllocationService(allocations=list(DEFAULT_ALLOCATIONS), currency=Currency.USD)
    )
    treasury_threshold: float = 5000.0
    member_count: int = 0

    # ------------------------------------------------------------------
    # Income
    # ------------------------------------------------------------------

    def record_income(
        self,
        amount: float,
        *,
        currency: Currency = Currency.USD,
        source: str,
        bucket: Optional[str] = None,
        metadata: Optional[dict] = None,
        at: Optional[datetime] = None,
    ) -> tuple[Transaction, Optional[AllocationResult]]:
        """Record incoming funds and split per allocation rules.

        Returns (income_tx, allocation_result_or_None).
        """
        if currency is not self.ledger.currency:
            raise TreasuryError(
                f"Currency mismatch: ledger={self.ledger.currency.value}, "
                f"requested={currency.value}"
            )
        income_tx = self.ledger.record_income(
            amount=amount, source=source, bucket=bucket, metadata=metadata, at=at
        )
        alloc = self.allocation_service.apply(
            income_tx,
            allocation_tx_factory=self._allocation_tx_factory(currency),
            at=at,
        )
        return income_tx, alloc

    def balance(self) -> float:
        return self.ledger.balance()

    def balance_by_bucket(self) -> dict[str, float]:
        return self.ledger.balance_by_bucket()

    def snapshot(self, at: Optional[datetime] = None) -> object:  # TreasurySnapshot — returned via ledger
        return self.ledger.snapshot(at=at)

    # ------------------------------------------------------------------
    # Withdrawal
    # ------------------------------------------------------------------

    def propose_withdrawal(
        self,
        amount: float,
        *,
        destination: str,
        purpose: str = "",
        requested_by: str = "unknown",
        at: Optional[datetime] = None,
    ) -> tuple[WithdrawalRequest, str]:
        """Initiate a withdrawal request.

        Returns (request, route) where `route` is one of:
        - ``"direct"`` — member_count >= 3 and amount <= threshold
        - ``"quorum"`` — member_count >= 3 and amount > threshold
        - ``"founder_gate"`` — member_count < 3; must be approved by founder
        """
        if amount <= 0:
            raise TreasuryError("Withdrawal amount must be positive")
        req = self.ledger.initiate_withdrawal(
            amount=amount,
            destination=destination,
            purpose=purpose,
            requested_by=requested_by,
            at=at,
        )
        needs_quorum = amount > self.treasury_threshold and self.member_count >= 3
        if needs_quorum:
            route = "quorum"
        elif self.member_count < 3:
            route = "founder_gate"
        else:
            route = "direct"
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

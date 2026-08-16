# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""treasury/allocation.py — Allocation rules for ZenOS Commons Treasury.

Applies the per-transaction split from ZENOS-COMMONS Art 5:

| Bucket | Share |
|--------|-------|
| operating_reserve | 30 % |
| tax_reserve | 25 % |
| reinvestment | 30 % |
| founder_draw | 15 % |

Rules:
- Splits are applied on **every incoming transaction** in the order above.
- Founder draw is locked by default (requires L1/L2 amendment to change).
- The split is persisted as allocation transactions on the ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.mekong.treasury.models import (
    AllocationBucket,
    Currency,
    DEFAULT_ALLOCATIONS,
    Transaction,
    TransactionKind,
)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


@dataclass
class AllocationResult:
    source_tx_id: str
    currency: Currency
    source_amount: float
    splits: dict[str, float]  # bucket -> amount
    allocation_tx_ids: list[str]
    warnings: list[str] = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


class AllocationError(Exception):
    pass


class AllocationService:
    """Split incoming treasury transactions across buckets."""

    def __init__(
        self,
        allocations: Optional[list[AllocationBucket]] = None,
        currency: Currency = Currency.USD,
    ) -> None:
        self.allocations = allocations or list(DEFAULT_ALLOCATIONS)
        self.currency = currency
        total = sum(a.fraction for a in self.allocations)
        if abs(total - 1.0) > 1e-9:
            raise AllocationError(
                f"Allocation fractions must sum to 1.0, got {total:.4f}"
            )

    def apply(
        self,
        source_tx: Transaction,
        *,
        allocation_tx_factory: Optional[callable] = None,
        at: Optional[object] = None,  # datetime — left as Any-ish to avoid circular dataclass import
    ) -> AllocationResult:
        """Split *source_tx* across allocation buckets.

        Parameters
        ----------
        source_tx:
            The INCOME transaction being allocated.  Must belong to
            ``self.currency``.
        allocation_tx_factory:
            Optional callable ``(kind, amount, bucket, metadata, at) -> Transaction``
            used to persist allocation entries on the ledger.  If ``None``,
            no rows are created and the result carries no ``allocation_tx_ids``.
        """
        if source_tx.kind is not TransactionKind.INCOME:
            raise AllocationError(
                f"Allocation applies to INCOME only, got {source_tx.kind.value}"
            )
        if source_tx.currency is not self.currency:
            raise AllocationError(
                f"Allocation currency mismatch: tx={source_tx.currency.value}, "
                f"service={self.currency.value}"
            )
        amount = source_tx.amount
        if amount <= 0:
            raise AllocationError("Cannot allocate non-positive amount")

        splits: dict[str, float] = {}
        tx_ids: list[str] = []
        warnings: list[str] = []
        for alloc in self.allocations:
            share = amount * alloc.fraction
            # Round to 2 decimal places to avoid float drift; the residual is
            # absorbed by the last non-locked bucket.
            splits[alloc.name] = share
            if allocation_tx_factory is not None:
                when = at or source_tx.created_at
                tx = allocation_tx_factory(
                    kind="ALLOCATION",
                    amount=share,
                    bucket=alloc.name,
                    metadata={
                        "source_tx_id": source_tx.tx_id,
                        "fraction": alloc.fraction,
                    },
                    at=when,
                )
                tx_ids.append(tx.tx_id)
        return AllocationResult(
            source_tx_id=source_tx.tx_id,
            currency=source_tx.currency,
            source_amount=amount,
            splits=splits,
            allocation_tx_ids=tx_ids,
            warnings=warnings,
        )

    def split_amount(self, amount: float) -> dict[str, float]:
        """Pure function — return split without touching the ledger."""
        result: dict[str, float] = {}
        for alloc in self.allocations:
            result[alloc.name] = amount * alloc.fraction
        return result

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""treasury/models.py — Domain types for the ZenOS Commons Treasury."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Currency(str, Enum):
    USD = "USD"
    VND = "VND"
    USDT = "USDT"


class TransactionKind(str, Enum):
    INCOME = "INCOME"
    WITHDRAWAL = "WITHDRAWAL"
    ALLOCATION = "ALLOCATION"
    ADJUSTMENT = "ADJUSTMENT"
    REVERSAL = "REVERSAL"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TreasuryError(Exception):
    pass


class DuplicateTxError(TreasuryError):
    pass


class InsufficientFundsError(TreasuryError):
    pass


class ApprovalRequiredError(TreasuryError):
    pass


@dataclass(frozen=True)
class AllocationBucket:
    name: str
    fraction: float  # 0..1
    locked: bool = False  # immutable without L1/L2 amendment

    def __post_init__(self) -> None:
        if not 0.0 <= self.fraction <= 1.0:
            raise TreasuryError(
                f"Allocation fraction must be in [0,1], got {self.fraction}"
            )


DEFAULT_ALLOCATIONS: list[AllocationBucket] = [
    AllocationBucket("operating_reserve", 0.30),
    AllocationBucket("tax_reserve", 0.25),
    AllocationBucket("reinvestment", 0.30),
    AllocationBucket("founder_draw", 0.15, locked=True),
]


@dataclass
class Transaction:
    tx_id: str
    kind: TransactionKind
    currency: Currency
    amount: float  # signed: positive = in, negative = out
    bucket: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None
    approval_tx_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def is_executed(self) -> bool:
        return self.status is TransactionStatus.EXECUTED

    def is_reversible(self) -> bool:
        return self.status in {
            TransactionStatus.EXECUTED,
            TransactionStatus.APPROVED,
        }


@dataclass
class TreasurySnapshot:
    """Point-in-time balance per bucket and currency."""

    captured_at: datetime
    buckets: dict[str, dict[Currency, float]]  # bucket -> currency -> amount
    total_by_currency: dict[Currency, float] = field(default_factory=dict)
    tx_count: int = 0


@dataclass
class WithdrawalRequest:
    request_id: str
    amount: float
    currency: Currency
    destination: str
    purpose: str
    requested_by: str
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def new_tx_id(prefix: str = "tx") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand = secrets.token_hex(4)
    return f"{prefix}_{ts}_{rand}"


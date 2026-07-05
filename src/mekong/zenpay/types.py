"""Data types for the ZenPay Treasury module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Transaction:
    """A single financial transaction in the ZenOS treasury.

    Attributes:
        id: UUID string identifying this transaction.
        particle_id: The particle that owns/receives this transaction.
        tx_type: Transaction category — ``"income"`` | ``"expense"`` | ``"transfer"``.
        amount: Numeric value of the transaction.
        currency: ISO 4217 code — ``"USD"`` | ``"VND"`` | ``"USDT"``.
        description: Human-readable explanation.
        category: Business category — ``"revenue"`` | ``"ops"`` | ``"investment"``
            | ``"tax"`` | ``"dividend"``.
        constitutional_review: Status of constitutional compliance review —
            ``"passed"`` | ``"pending"`` | ``"failed"``.
        counterparty: Other particle or external entity involved, or ``None``.
        timestamp: ISO-8601 UTC timestamp.
        evidence: Arbitrary JSON-serialisable evidence attached to this
            transaction (receipt hash, invoice link, etc.), or ``None``.
    """

    id: str
    particle_id: str
    tx_type: str
    amount: float
    currency: str
    description: str
    category: str
    constitutional_review: str = "passed"
    counterparty: str | None = None
    timestamp: str = ""
    evidence: dict[str, Any] | None = None


@dataclass
class TreasuryBalance:
    """Aggregated treasury balance for a particle.

    Attributes:
        particle_id: The particle whose balance is aggregated.
        total_income: Sum of all income transactions.
        total_expense: Sum of all expense transactions.
        net_balance: ``total_income - total_expense``.
        transaction_count: Total number of treasury transactions recorded.
    """

    particle_id: str
    total_income: float = 0.0
    total_expense: float = 0.0
    net_balance: float = 0.0
    transaction_count: int = 0


@dataclass
class BudgetConfig:
    """Budget limits and approval rules for a particle.

    Attributes:
        max_monthly_expense: Maximum allowed expenses per calendar month.
        max_per_transaction: Maximum value for a single transaction.
        requires_approval_above: Amounts above this threshold trigger a
            mandatory constitutional review.
        allowed_categories: List of approved transaction categories. An empty
            list means all categories are permitted.
    """

    max_monthly_expense: float = 0.0
    max_per_transaction: float = 0.0
    requires_approval_above: float = 0.0
    allowed_categories: list[str] = field(default_factory=list)

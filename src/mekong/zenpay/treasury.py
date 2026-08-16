"""Treasury bridge — thin, dispatch-only translation between CLI submittable arguments and TreasuryService."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.mekong.treasury.models import (
    Currency,
    TransactionKind,
    TransactionStatus,
)
from src.mekong.treasury.service import TreasuryService

logger = logging.getLogger(__name__)
_service = TreasuryService()


@dataclass(frozen=True)
class BalanceView:
    particle_id: str
    total_income: float
    total_expense: float
    net_balance: float
    transaction_count: int
    buckets: dict[str, float]


@dataclass(frozen=True)
class TxView:
    id: str
    tx_type: str
    amount: float
    currency: str
    description: str
    category: str
    constitutional_review: str
    timestamp: str


def _currency(value: Optional[str]) -> Currency:
    if not value:
        return Currency.USD
    return Currency(value.strip().upper())


def _bridge_tx_type(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.lower()
    return {
        "income": "income",
        "expense": "expense",
        "transfer": "transfer",
        "INCOME": "income",
        "EXPENSE": "expense",
        "TRANSFER": "transfer",
    }.get(v, v)


def _normalize_kind(kind: TransactionKind) -> TransactionKind:
    try:
        return TransactionKind(kind.value)
    except Exception:
        return kind


def record_transaction(tx, *, requested_by: Optional[str] = None) -> dict:
    kind = _normalize_kind(tx.kind)
    if kind is TransactionKind.INCOME:
        return _record_income(tx, requested_by)
    # WITHDRAWAL covers expense + transfer from CLI mapping
    return _record_outgoing(tx, kind, requested_by)


def _record_income(tx, requested_by: Optional[str] = None) -> dict:
    currency = _currency(getattr(tx, "currency", None))
    amount = float(getattr(tx, "amount", 0) or 0)
    currency = _currency(getattr(tx, "currency", None))
    bucket = getattr(tx, "category", None) or "general"
    source = getattr(tx, "description", None) or getattr(tx, "source", None) or tx.tx_id or ""
    meta = {
        "cli_tx_id": tx.tx_id,
        "requested_by": requested_by or getattr(tx, "particle_id", None) or "unknown",
    }
    income_tx, _ = _service.record_income(
        amount=abs(amount),
        currency=currency,
        source=source,
        bucket=bucket,
        metadata=meta,
    )
    real_id = income_tx.tx_id
    return {
        "transaction_id": real_id,
        "behavior_id": f"beh_{real_id[:8]}",
        "review_status": "passed",
    }


def _record_outgoing(tx, kind, requested_by=None) -> dict:
    amount = float(getattr(tx, "amount", 0) or 0)
    currency = _currency(getattr(tx, "currency", None))
    bucket = getattr(tx, "category", None) or "general"
    counterparty = getattr(tx, "counterparty", None) or bucket
    purpose = getattr(tx, "description", None) or getattr(tx, "source", None) or ""
    actor = requested_by or getattr(tx, "particle_id", None) or "unknown"
    req, route = _service.propose_withdrawal(
        amount=abs(amount),
        destination=counterparty,
        purpose=purpose,
        requested_by=actor,
    )
    if route == "quorum":
        from src.mekong.treasury.models import ApprovalRequiredError
        raise ApprovalRequiredError(
            f"Withdrawal {abs(amount)} {currency.value} exceeds "
            f"treasury threshold and requires L2 supermajority (quorum). "
            f"Route: vote_engine.propose -> cooling period -> tally."
        )
    approved = _service.approve_withdrawal(
        req,
        approver=actor,
        approved_bypass_all=(route == "founder_gate"),
    )
    return {
        "transaction_id": approved.tx_id,
        "behavior_id": f"beh_{approved.tx_id[:8]}",
        "review_status": _status_label(approved.status),
        "route": route,
    }


def get_balance(particle: str) -> BalanceView:
    bal = _service.balance()
    bucket_map = _service.balance_by_bucket()
    txs = _service.list_transactions()
    total_out = sum(
        abs(t.amount)
        for t in txs
        if t.kind.value in {"WITHDRAWAL", "REVERSAL"}
        and t.currency is _service.ledger.currency
    )
    return BalanceView(
        particle_id=particle,
        total_income=_service.ledger.all_time_in(),
        total_expense=total_out,
        net_balance=bal,
        transaction_count=len(txs),
        buckets=bucket_map,
    )


def get_history(particle: str, limit: int = 20) -> list[TxView]:
    txs = _service.list_transactions(limit=limit)
    default_currency = _service.ledger.currency
    views = []
    for tx in txs:
        views.append(_TxView_from_tx(tx, default_currency))
    return views


def _TxView_from_tx(tx, default_currency) -> TxView:
    status = getattr(tx, "status", TransactionStatus.PENDING)
    return TxView(
        id=tx.tx_id,
        tx_type=tx.kind.value,
        amount=float(tx.amount),
        currency=(tx.currency.value if tx.currency else default_currency.value),
        description=tx.source or tx.destination or "",
        category=tx.bucket or "general",
        constitutional_review=_status_label(status),
        timestamp=tx.created_at.isoformat() if tx.created_at else "",
    )


def _status_label(status: TransactionStatus) -> str:
    return {
        TransactionStatus.PENDING: "pending",
        TransactionStatus.EXECUTED: "passed",
        TransactionStatus.REJECTED: "rejected",
        TransactionStatus.EXPIRED: "expired",
    }.get(status, "pending")

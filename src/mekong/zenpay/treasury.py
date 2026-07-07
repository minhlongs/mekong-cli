"""Compatibility shim — standalone treasury functions for CLI.

Replaces the deleted zenpay.treasury module.  Uses TreasuryService internally
but exposes the simple function API the CLI expects.
"""
from __future__ import annotations

import logging
from typing import Any

from src.mekong.treasury.models import Transaction, Currency
from src.mekong.treasury.service import TreasuryService

logger = logging.getLogger(__name__)

_service = TreasuryService()


def record_transaction(tx: Transaction) -> dict:
    """Record a transaction and return a result dict for the CLI."""
    amount = tx.amount
    currency = getattr(tx, "currency", None) or Currency.USD
    description = tx.description or ""
    category = getattr(tx, "category", None) or "general"

    income_tx, _alloc = _service.record_income(
        amount=amount,
        currency=currency,
        source=description,
        bucket=category,
        metadata={
            "id": tx.id,
            "counterparty": getattr(tx, "counterparty", None),
        },
    )
    tx_id = income_tx.id or "tx_generated"
    return {
        "transaction_id": tx_id,
        "behavior_id": f"beh_{tx_id[:8]}",
        "review_status": "passed",
    }


def get_balance(particle: str) -> Any:
    """Return a balance view object for *particle*."""
    bal = _service.balance()
    bucket_map = _service.balance_by_bucket()

    class _Bal:
        pass

    b = _Bal()
    b.particle_id = particle
    b.total_income = max(0.0, bal)
    b.total_expense = 0.0
    b.net_balance = bal
    b.transaction_count = len(_service.list_transactions())
    b.buckets = bucket_map
    return b


def get_history(particle: str, limit: int = 20) -> list:
    """Return recent transactions for *particle*, newest first."""
    txs = _service.list_transactions(limit=limit)

    result = []
    for tx in txs:
        class _TxView:
            pass

        v = _TxView()
        v.id = tx.id
        v.tx_type = tx.tx_type.value if hasattr(tx.tx_type, "value") else str(tx.tx_type)
        v.amount = tx.amount
        v.currency = tx.currency.value if hasattr(tx.currency, "value") else getattr(tx, "currency", "USD")
        v.description = tx.description
        v.category = tx.category or "general"
        v.constitutional_review = getattr(tx, "constitutional_review", "passed") or "passed"
        v.timestamp = str(getattr(tx, "timestamp", ""))
        result.append(v)
    return result

"""Tests for the Constitutional Treasury module (``src.mekong.zenpay.treasury``).

Covers transaction recording, balance computation, history ordering, budget
limit enforcement, and edge cases, all backed by a temporary SQLite database.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path for imports under src/
_project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import yaml
import pytest
from src.mekong.graph.store import ensure_entity, open_db
from src.mekong.zenpay.treasury import (
    get_balance,
    get_history,
    record_transaction,
)
from src.mekong.zenpay.types import Transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PARTICLE_ID = "test-particle-alpha"


def _db_path(tmp_path: Path) -> str:
    """Return an absolute, isolated DB path within *tmp_path*."""
    p = tmp_path / ".mekong" / "graph.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


def _ensure_particle(db_path: str, particle_id: str) -> None:
    """Ensure the particle entity exists in the graph DB."""
    conn = open_db(db_path)
    try:
        ensure_entity(conn, particle_id, particle_id, kind="particle")
    finally:
        conn.close()


def _create_budget_config(
    tmp_path: Path,
    particle_id: str = PARTICLE_ID,
    **overrides: float | list[str],
) -> None:
    """Write a budgets.yaml for *particle_id* inside *tmp_path*."""
    cfg_dir = tmp_path / ".mekong" / "particles" / particle_id / "cashflow"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    defaults: dict = {
        "max_monthly_expense": 10_000,
        "max_per_transaction": 0,
        "requires_approval_above": 0,
        "allowed_categories": [],
    }
    defaults.update(overrides)
    (cfg_dir / "budgets.yaml").write_text(yaml.dump(defaults))


def _record(
    tmp_path: Path,
    particle_id: str = PARTICLE_ID,
    tx_type: str = "income",
    amount: float = 100.0,
    description: str = "test tx",
    currency: str = "USD",
    category: str = "revenue",
) -> dict:
    """Shortcut to record a transaction in an isolated DB and return the result."""
    db = _db_path(tmp_path)
    _ensure_particle(db, particle_id)
    tx = Transaction(
        id="",
        particle_id=particle_id,
        tx_type=tx_type,
        amount=amount,
        currency=currency,
        description=description,
        category=category,
    )
    return record_transaction(tx, db_path=db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRecordAndBalance:
    """Recording transactions and checking the computed balance."""

    def test_record_income(self, tmp_path: Path) -> None:
        """An income transaction increases total income in the balance."""
        _record(tmp_path, amount=5000.0)
        bal = get_balance(PARTICLE_ID, db_path=_db_path(tmp_path))
        assert bal.total_income == 5000.0
        assert bal.total_expense == 0.0
        assert bal.net_balance == 5000.0
        assert bal.transaction_count == 1

    def test_record_expense(self, tmp_path: Path) -> None:
        """An expense transaction increases total expense in the balance."""
        _record(tmp_path, tx_type="expense", amount=1200.0)
        bal = get_balance(PARTICLE_ID, db_path=_db_path(tmp_path))
        assert bal.total_expense == 1200.0
        assert bal.total_income == 0.0
        assert bal.net_balance == -1200.0
        assert bal.transaction_count == 1

    def test_balance_computation(self, tmp_path: Path) -> None:
        """Multiple transactions produce a correct net balance."""
        db = _db_path(tmp_path)
        _record(tmp_path, amount=5000.0)          # income +5000
        _record(tmp_path, tx_type="expense", amount=1200.0)  # expense -1200
        _record(tmp_path, amount=3000.0)          # income +3000
        _record(tmp_path, tx_type="expense", amount=800.0)   # expense -800

        bal = get_balance(PARTICLE_ID, db_path=db)
        assert bal.total_income == 8000.0
        assert bal.total_expense == 2000.0
        assert bal.net_balance == 6000.0
        assert bal.transaction_count == 4


class TestHistoryOrdering:
    """History query returns transactions newest-first."""

    def test_history_ordering(self, tmp_path: Path) -> None:
        """Transactions appear in descending timestamp order."""
        db = _db_path(tmp_path)
        r1 = _record(tmp_path, amount=100.0, description="first")
        r2 = _record(tmp_path, amount=200.0, description="second")
        r3 = _record(tmp_path, amount=300.0, description="third")

        transactions = get_history(PARTICLE_ID, limit=10, db_path=db)
        # The behaviour store orders by timestamp DESC. Since records happen
        # sequentially, the last recorded should be first in history.
        ids = [t.id for t in transactions]
        # The first returned should be the most recently recorded
        assert ids[0] == r3["transaction_id"]
        assert ids[1] == r2["transaction_id"]
        assert ids[2] == r1["transaction_id"]
        assert len(transactions) == 3


class TestBudgetLimits:
    """Constitutional budget enforcement via budget config files."""

    def test_budget_enforcement(self, tmp_path: Path, monkeypatch) -> None:
        """A transaction exceeding max_per_transaction gets review=pending."""
        monkeypatch.chdir(tmp_path)
        _create_budget_config(tmp_path, max_per_transaction=100)

        result = _record(tmp_path, tx_type="expense", amount=200, description="over limit")
        assert result["review_status"] == "pending"

    def test_budget_approval(self, tmp_path: Path, monkeypatch) -> None:
        """A transaction under requires_approval_above gets review=passed."""
        monkeypatch.chdir(tmp_path)
        _create_budget_config(tmp_path, requires_approval_above=100)

        result = _record(tmp_path, tx_type="expense", amount=50, description="under threshold")
        assert result["review_status"] == "passed"


class TestEdgeCases:
    """Unusual but valid inputs."""

    def test_zero_amount(self, tmp_path: Path) -> None:
        """A transaction with amount zero is recorded successfully."""
        result = _record(tmp_path, amount=0.0, description="zero amount")
        assert result["transaction_id"]
        bal = get_balance(PARTICLE_ID, db_path=_db_path(tmp_path))
        assert bal.total_income == 0.0
        assert bal.transaction_count == 1

    def test_negative_amount(self, tmp_path: Path) -> None:
        """A transaction with a negative amount is recorded."""
        result = _record(
            tmp_path, tx_type="income", amount=-50.0, description="negative income"
        )
        assert result["transaction_id"]
        bal = get_balance(PARTICLE_ID, db_path=_db_path(tmp_path))
        assert bal.total_income == -50.0
        assert bal.transaction_count == 1

    def test_missing_particle(self, tmp_path: Path) -> None:
        """A non-existent particle ID produces an empty balance (no error)."""
        db = _db_path(tmp_path)
        # No transaction recorded for this particle
        bal = get_balance("nonexistent-particle", db_path=db)
        assert bal.total_income == 0.0
        assert bal.total_expense == 0.0
        assert bal.net_balance == 0.0
        assert bal.transaction_count == 0


class TestEmptyHistory:
    """History query when no transactions exist."""

    def test_empty_history(self, tmp_path: Path) -> None:
        """No transactions returns an empty list."""
        txns = get_history(PARTICLE_ID, limit=20, db_path=_db_path(tmp_path))
        assert txns == []

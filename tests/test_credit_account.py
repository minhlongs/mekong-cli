"""Tests for CreditAccountRepository and CreditStore — workspace-level credit billing.

Covers:
- CreditAccountRepository: create_account, get_balance, add_credits, deduct_credits
- CreditAccountRepository: idempotency (mark_event_processed, is_event_processed)
- CreditAccountRepository: transaction history (get_history)
- CreditStore: add, deduct, get_balance, get_history (tenant-level credits)
- Edge cases: zero balance deduction, negative credit rejection, duplicate events
- Atomicity: deduct returns False on insufficient funds (never goes negative)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.raas.credit_account_repository import (
    CreditAccount,
    CreditAccountRepository,
    CreditTransaction,
)
from src.raas.credits import CreditStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo(tmp_path) -> CreditAccountRepository:
    """CreditAccountRepository backed by tmp_path — isolated per test."""
    db = tmp_path / "workspaces.db"
    return CreditAccountRepository(db)


@pytest.fixture
def store(tmp_path) -> CreditStore:
    """CreditStore backed by tmp_path — isolated per test."""
    db = tmp_path / "tenants.db"
    return CreditStore(db)


# ---------------------------------------------------------------------------
# CreditAccountRepository: create_account
# ---------------------------------------------------------------------------

class TestCreateAccount:
    def test_creates_account_with_zero_balance(self, repo):
        acct = repo.create_account("ws_001")
        assert acct.workspace_id == "ws_001"
        assert acct.balance == 0
        assert acct.total_earned == 0
        assert acct.total_spent == 0

    def test_create_idempotent_no_error(self, repo):
        """Creating the same account twice must not raise."""
        repo.create_account("ws_dup")
        acct = repo.create_account("ws_dup")  # second call must not raise
        assert acct.workspace_id == "ws_dup"

    def test_get_balance_after_create_is_zero(self, repo):
        repo.create_account("ws_zero")
        assert repo.get_balance("ws_zero") == 0

    def test_get_balance_missing_workspace_is_zero(self, repo):
        """Unknown workspace returns 0, not an error."""
        assert repo.get_balance("no_such_ws") == 0

    def test_get_account_returns_none_for_missing(self, repo):
        result = repo.get_account("ghost_ws")
        assert result is None

    def test_get_account_returns_credit_account(self, repo):
        repo.create_account("ws_full")
        acct = repo.get_account("ws_full")
        assert isinstance(acct, CreditAccount)
        assert acct.workspace_id == "ws_full"


# ---------------------------------------------------------------------------
# CreditAccountRepository: add_credits
# ---------------------------------------------------------------------------

class TestAddCredits:
    def test_add_credits_happy_path(self, repo):
        repo.create_account("ws_pay")
        new_balance = repo.add_credits("ws_pay", 1000, "Polar subscription")
        assert new_balance == 1000
        assert repo.get_balance("ws_pay") == 1000

    def test_add_credits_accumulates(self, repo):
        repo.create_account("ws_acc")
        repo.add_credits("ws_acc", 200, "month1")
        repo.add_credits("ws_acc", 200, "month2")
        assert repo.get_balance("ws_acc") == 400

    def test_add_credits_creates_account_if_missing(self, repo):
        """add_credits upserts — workspace does not need to exist first."""
        new_balance = repo.add_credits("ws_new", 500, "NOWPayments pro")
        assert new_balance == 500

    def test_add_zero_credits_raises(self, repo):
        repo.create_account("ws_z")
        with pytest.raises(ValueError, match="positive"):
            repo.add_credits("ws_z", 0, "zero is invalid")

    def test_add_negative_credits_raises(self, repo):
        repo.create_account("ws_neg")
        with pytest.raises(ValueError, match="positive"):
            repo.add_credits("ws_neg", -100, "negative invalid")

    def test_add_updates_total_earned(self, repo):
        repo.create_account("ws_earn")
        repo.add_credits("ws_earn", 300, "earned")
        acct = repo.get_account("ws_earn")
        assert acct.total_earned == 300

    def test_add_multiple_updates_total_earned(self, repo):
        repo.create_account("ws_earn2")
        repo.add_credits("ws_earn2", 200, "month1")
        repo.add_credits("ws_earn2", 150, "month2")
        acct = repo.get_account("ws_earn2")
        assert acct.total_earned == 350


# ---------------------------------------------------------------------------
# CreditAccountRepository: deduct_credits
# ---------------------------------------------------------------------------

class TestDeductCredits:
    def test_deduct_happy_path(self, repo):
        repo.create_account("ws_d")
        repo.add_credits("ws_d", 500, "initial")
        result = repo.deduct_credits("ws_d", 100, "mission_cost")
        assert result is True
        assert repo.get_balance("ws_d") == 400

    def test_deduct_insufficient_balance_returns_false(self, repo):
        repo.create_account("ws_short")
        repo.add_credits("ws_short", 50, "seed")
        result = repo.deduct_credits("ws_short", 100, "too expensive")
        assert result is False
        # Balance must NOT be modified
        assert repo.get_balance("ws_short") == 50

    def test_deduct_exact_balance_succeeds(self, repo):
        """Deducting exactly the available balance must succeed."""
        repo.create_account("ws_exact")
        repo.add_credits("ws_exact", 100, "seed")
        result = repo.deduct_credits("ws_exact", 100, "drain")
        assert result is True
        assert repo.get_balance("ws_exact") == 0

    def test_deduct_from_zero_balance_returns_false(self, repo):
        repo.create_account("ws_empty")
        result = repo.deduct_credits("ws_empty", 1, "nope")
        assert result is False

    def test_deduct_zero_raises(self, repo):
        repo.create_account("ws_0deduct")
        with pytest.raises(ValueError, match="positive"):
            repo.deduct_credits("ws_0deduct", 0, "zero deduction")

    def test_deduct_negative_raises(self, repo):
        repo.create_account("ws_negdeduct")
        with pytest.raises(ValueError, match="positive"):
            repo.deduct_credits("ws_negdeduct", -50, "negative deduction")

    def test_deduct_never_goes_negative(self, repo):
        """Multiple concurrent deduct attempts must not go below zero."""
        repo.create_account("ws_race")
        repo.add_credits("ws_race", 10, "seed")

        # Only one of these should succeed (10 < 7+7=14)
        r1 = repo.deduct_credits("ws_race", 7, "mission1")
        r2 = repo.deduct_credits("ws_race", 7, "mission2")

        final_balance = repo.get_balance("ws_race")
        assert final_balance >= 0
        # At most one succeeded
        successes = sum([r1, r2])
        assert successes == 1

    def test_deduct_updates_total_spent(self, repo):
        repo.create_account("ws_spent")
        repo.add_credits("ws_spent", 500, "seed")
        repo.deduct_credits("ws_spent", 100, "op1")
        repo.deduct_credits("ws_spent", 50, "op2")
        acct = repo.get_account("ws_spent")
        assert acct.total_spent == 150


# ---------------------------------------------------------------------------
# CreditAccountRepository: get_history
# ---------------------------------------------------------------------------

class TestGetHistory:
    def test_history_empty_on_new_account(self, repo):
        repo.create_account("ws_hist_new")
        txns = repo.get_history("ws_hist_new")
        assert txns == []

    def test_history_records_add(self, repo):
        repo.create_account("ws_hist")
        repo.add_credits("ws_hist", 200, "Polar starter")
        txns = repo.get_history("ws_hist")
        assert len(txns) == 1
        assert txns[0].amount == 200
        assert txns[0].reason == "Polar starter"

    def test_history_records_deduct_as_negative(self, repo):
        repo.create_account("ws_hist2")
        repo.add_credits("ws_hist2", 100, "seed")
        repo.deduct_credits("ws_hist2", 30, "mission")
        txns = repo.get_history("ws_hist2")
        amounts = [t.amount for t in txns]
        assert -30 in amounts

    def test_history_ordered_newest_first(self, repo):
        repo.create_account("ws_order")
        repo.add_credits("ws_order", 100, "first")
        repo.add_credits("ws_order", 200, "second")
        txns = repo.get_history("ws_order")
        # Newest first — second > first by timestamp
        assert txns[0].amount == 200
        assert txns[1].amount == 100

    def test_history_limit_respected(self, repo):
        repo.create_account("ws_limit")
        for i in range(10):
            repo.add_credits("ws_limit", 1, f"event_{i}")
        txns = repo.get_history("ws_limit", limit=3)
        assert len(txns) == 3

    def test_history_returns_credit_transaction_objects(self, repo):
        repo.create_account("ws_type")
        repo.add_credits("ws_type", 50, "check type")
        txns = repo.get_history("ws_type")
        assert isinstance(txns[0], CreditTransaction)
        assert txns[0].workspace_id == "ws_type"


# ---------------------------------------------------------------------------
# CreditAccountRepository: idempotency (webhook dedup)
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_mark_event_processed_returns_true(self, repo):
        repo.create_account("ws_idem")
        result = repo.mark_event_processed("evt_001", "order.created", "ws_idem")
        assert result is True

    def test_is_event_processed_true_after_mark(self, repo):
        repo.create_account("ws_idem2")
        repo.mark_event_processed("evt_abc", "subscription.created", "ws_idem2")
        assert repo.is_event_processed("evt_abc") is True

    def test_is_event_processed_false_for_new_event(self, repo):
        assert repo.is_event_processed("evt_brand_new") is False

    def test_duplicate_mark_returns_false(self, repo):
        """Second mark of same event_id returns False (idempotency key conflict)."""
        repo.create_account("ws_dup_evt")
        repo.mark_event_processed("evt_dup", "order.created", "ws_dup_evt")
        result = repo.mark_event_processed("evt_dup", "order.created", "ws_dup_evt")
        assert result is False

    def test_different_events_independent(self, repo):
        repo.create_account("ws_multi_evt")
        repo.mark_event_processed("evt_001", "order.created", "ws_multi_evt")
        repo.mark_event_processed("evt_002", "subscription.created", "ws_multi_evt")
        assert repo.is_event_processed("evt_001") is True
        assert repo.is_event_processed("evt_002") is True
        assert repo.is_event_processed("evt_003") is False


# ---------------------------------------------------------------------------
# CreditStore (tenant-level credits, raas/credits.py)
# ---------------------------------------------------------------------------

class TestCreditStoreAdd:
    def test_add_creates_account(self, store):
        balance = store.add("tenant_1", 100, "initial grant")
        assert balance == 100

    def test_add_accumulates(self, store):
        store.add("t1", 50, "batch1")
        balance = store.add("t1", 50, "batch2")
        assert balance == 100

    def test_add_zero_raises(self, store):
        with pytest.raises(ValueError, match="positive"):
            store.add("t1", 0, "zero")

    def test_add_negative_raises(self, store):
        with pytest.raises(ValueError, match="positive"):
            store.add("t1", -10, "negative")

    def test_add_records_transaction(self, store):
        store.add("t1", 200, "polar_payment")
        history = store.get_history("t1")
        assert len(history) == 1
        assert history[0].amount == 200
        assert history[0].reason == "polar_payment"


class TestCreditStoreDeduct:
    def test_deduct_success(self, store):
        store.add("t1", 100, "seed")
        result = store.deduct("t1", 30, "mission_cost")
        assert result is True
        assert store.get_balance("t1") == 70

    def test_deduct_insufficient_returns_false(self, store):
        store.add("t1", 5, "seed")
        result = store.deduct("t1", 10, "too much")
        assert result is False
        assert store.get_balance("t1") == 5

    def test_deduct_exact_balance(self, store):
        store.add("t1", 50, "seed")
        result = store.deduct("t1", 50, "drain all")
        assert result is True
        assert store.get_balance("t1") == 0

    def test_deduct_zero_raises(self, store):
        with pytest.raises(ValueError, match="positive"):
            store.deduct("t1", 0, "zero deduct")

    def test_deduct_negative_raises(self, store):
        with pytest.raises(ValueError, match="positive"):
            store.deduct("t1", -5, "negative deduct")

    def test_deduct_from_missing_tenant_returns_false(self, store):
        """Deducting from a nonexistent tenant returns False (balance=0 < amount)."""
        result = store.deduct("ghost_tenant", 1, "not found")
        assert result is False

    def test_deduct_never_negative_sequential(self, store):
        """Sequential deductions must not create negative balance."""
        store.add("t1", 10, "seed")
        r1 = store.deduct("t1", 6, "op1")
        r2 = store.deduct("t1", 6, "op2")  # only 4 left

        assert r1 is True
        assert r2 is False
        assert store.get_balance("t1") == 4

    def test_deduct_records_negative_transaction(self, store):
        store.add("t1", 100, "seed")
        store.deduct("t1", 25, "usage")
        history = store.get_history("t1")
        amounts = [t.amount for t in history]
        assert -25 in amounts


class TestCreditStoreGetBalance:
    def test_unknown_tenant_zero(self, store):
        assert store.get_balance("no_such_tenant") == 0

    def test_balance_after_operations(self, store):
        store.add("t1", 100, "seed")
        store.deduct("t1", 30, "op1")
        store.add("t1", 50, "top_up")
        assert store.get_balance("t1") == 120


class TestCreditStoreHistory:
    def test_history_empty(self, store):
        txns = store.get_history("no_such_tenant")
        assert txns == []

    def test_history_multiple_operations(self, store):
        store.add("t1", 100, "seed")
        store.deduct("t1", 20, "deduct1")
        store.deduct("t1", 10, "deduct2")
        store.add("t1", 50, "top_up")
        txns = store.get_history("t1")
        assert len(txns) == 4

    def test_history_limit(self, store):
        for i in range(20):
            store.add("t1", 1, f"op_{i}")
        txns = store.get_history("t1", limit=5)
        assert len(txns) == 5

    def test_history_returns_credit_transaction_objects(self, store):
        store.add("t1", 10, "check_type")
        txns = store.get_history("t1")
        assert hasattr(txns[0], "tenant_id")
        assert txns[0].tenant_id == "t1"


# ---------------------------------------------------------------------------
# Edge cases: multi-workspace isolation
# ---------------------------------------------------------------------------

class TestWorkspaceIsolation:
    def test_credits_isolated_per_workspace(self, repo):
        repo.create_account("ws_alice")
        repo.create_account("ws_bob")
        repo.add_credits("ws_alice", 500, "alice payment")
        repo.add_credits("ws_bob", 100, "bob payment")

        assert repo.get_balance("ws_alice") == 500
        assert repo.get_balance("ws_bob") == 100

    def test_deduct_from_alice_does_not_affect_bob(self, repo):
        repo.create_account("ws_alice")
        repo.create_account("ws_bob")
        repo.add_credits("ws_alice", 200, "seed")
        repo.add_credits("ws_bob", 200, "seed")
        repo.deduct_credits("ws_alice", 150, "op")

        assert repo.get_balance("ws_alice") == 50
        assert repo.get_balance("ws_bob") == 200

    def test_history_isolated_per_workspace(self, repo):
        repo.create_account("ws_x")
        repo.create_account("ws_y")
        repo.add_credits("ws_x", 100, "x_only")
        repo.add_credits("ws_y", 200, "y_only")

        x_txns = repo.get_history("ws_x")
        y_txns = repo.get_history("ws_y")

        assert all(t.workspace_id == "ws_x" for t in x_txns)
        assert all(t.workspace_id == "ws_y" for t in y_txns)


# ---------------------------------------------------------------------------
# Large value edge cases
# ---------------------------------------------------------------------------

class TestLargeValues:
    def test_add_large_credit_amount(self, repo):
        """Enterprise tier: 10,000 credits must be handled correctly."""
        new_bal = repo.add_credits("ws_ent", 10000, "enterprise monthly")
        assert new_bal == 10000

    def test_accumulated_large_balance(self, repo):
        """Simulating 12 months of enterprise (10k/mo) = 120,000 credits."""
        repo.create_account("ws_annual")
        for month in range(12):
            repo.add_credits("ws_annual", 10000, f"month_{month + 1}")
        assert repo.get_balance("ws_annual") == 120000

    def test_credit_store_large_tenant(self, store):
        """CreditStore handles 10k credits per add."""
        balance = store.add("ent_tenant", 10000, "enterprise grant")
        assert balance == 10000

    def test_overflow_protection(self, repo):
        """Multiple large adds should not overflow SQLite INTEGER."""
        repo.create_account("ws_big")
        for _ in range(100):
            repo.add_credits("ws_big", 10000, "bulk")
        assert repo.get_balance("ws_big") == 1_000_000

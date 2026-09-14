"""Tests for MCU Billing System."""
from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from src.core.mcu_billing import (
    LOW_BALANCE_THRESHOLD,
    MCU_COSTS,
    TIER_CREDITS,
    MCUBilling,
    MCUTransaction,
    TenantBalance,
    DeductionResult,
    PaymentResult,
)


@pytest.fixture(autouse=True)
def _wipe_billing_db():
    """Ensure clean billing state for each test in this file."""
    store = MCUBilling()._store
    conn = store._connect()
    try:
        conn.execute("DELETE FROM credit_transactions")
        conn.execute("DELETE FROM credit_accounts")
        conn.commit()
    finally:
        conn.close()
    yield
    conn = store._connect()
    try:
        conn.execute("DELETE FROM credit_transactions")
        conn.execute("DELETE FROM credit_accounts")
        conn.commit()
    finally:
        conn.close()


class TestMCUCosts:
    """Test MCU cost configuration and tier constants."""

    def test_mcu_costs_values(self):
        assert MCU_COSTS["simple"] == 1
        assert MCU_COSTS["standard"] == 3
        assert MCU_COSTS["complex"] == 5

    def test_tier_credits_starter(self):
        assert TIER_CREDITS["starter"] == 200

    def test_tier_credits_growth(self):
        assert TIER_CREDITS["growth"] == 1000

    def test_tier_credits_pro(self):
        assert TIER_CREDITS["pro"] == 5000

    def test_low_balance_threshold(self):
        assert LOW_BALANCE_THRESHOLD == 10


class TestTenantBalance:
    """Test TenantBalance dataclass."""

    def test_tenant_balance_creation(self):
        balance = TenantBalance(tenant_id="tenant-123")
        assert balance.tenant_id == "tenant-123"
        assert balance.balance == 0
        assert balance.total_credited == 0
        assert balance.total_debited == 0
        assert balance.total_refunded == 0
        assert balance.transactions == []

    def test_tenant_balance_to_dict(self):
        balance = TenantBalance(tenant_id="tenant-456")
        balance.balance = 100
        balance.total_credited = 150
        balance.total_debited = 50

        data = balance.to_dict()
        assert data["tenant_id"] == "tenant-456"
        assert data["balance"] == 100
        assert data["total_credited"] == 150
        assert data["total_debited"] == 50
        assert data["transaction_count"] == 0


class TestMCUTransaction:
    """Test MCUTransaction dataclass."""

    def test_transaction_creation(self):
        tx = MCUTransaction(
            tenant_id="tenant-123",
            amount=100,
            balance_after=100,
            transaction_type="credit",
            description="Initial credits",
        )
        assert tx.tenant_id == "tenant-123"
        assert tx.amount == 100
        assert tx.transaction_type == "credit"

    def test_transaction_to_dict(self):
        tx = MCUTransaction(
            tenant_id="tenant-789",
            amount=-5,
            balance_after=95,
            transaction_type="debit",
            description="Task execution",
            mission_id="mission-001",
        )
        data = tx.to_dict()
        assert data["tenant_id"] == "tenant-789"
        assert data["amount"] == -5
        assert data["balance_after"] == 95
        assert data["transaction_type"] == "debit"
        assert data["mission_id"] == "mission-001"
        assert "timestamp" in data


class TestDeductionResult:
    """Test DeductionResult dataclass."""

    def test_deduction_result_success(self):
        result = DeductionResult(
            success=True,
            balance_before=100,
            balance_after=97,
            amount_deducted=3,
            low_balance=False,
        )
        assert result.success is True
        assert result.amount_deducted == 3
        assert result.low_balance is False
        assert result.error == ""

    def test_deduction_result_failure_and_to_dict(self):
        result = DeductionResult(
            success=False,
            balance_before=2,
            balance_after=2,
            amount_deducted=0,
            error="Insufficient MCU: need 3, have 2",
        )
        assert result.success is False
        assert result.error != ""
        d = result.to_dict()
        assert d["success"] is False
        assert d["balance_before"] == 2
        assert d["balance_after"] == 2
        assert d["amount_deducted"] == 0
        assert d["low_balance"] is False
        assert d["error"] == "Insufficient MCU: need 3, have 2"


class TestPaymentResult:
    """Test PaymentResult dataclass."""

    def test_payment_result_defaults_and_to_dict(self):
        pr = PaymentResult(
            pending=True,
            transaction_id="tx-999",
            amount=50.0,
            currency="USD",
            recipient="rec-1",
            note="custom note",
        )
        assert pr.pending is True
        assert pr.amount == 50.0
        d = pr.to_dict()
        assert d == {
            "pending": True,
            "transaction_id": "tx-999",
            "amount": 50.0,
            "currency": "USD",
            "recipient": "rec-1",
            "note": "custom note",
        }


class TestMCUBilling:
    """Test MCUBilling engine."""

    def test_billing_initialization(self):
        billing = MCUBilling()
        assert billing.tenant_count == 0
        assert billing.low_threshold == LOW_BALANCE_THRESHOLD

    def test_add_credits(self):
        billing = MCUBilling()
        tenant = billing.add_credits("tenant-123", 100, "Initial grant")

        assert billing.get_balance("tenant-123") == 100
        assert tenant.balance == 100
        assert tenant.total_credited == 100
        assert len(tenant.transactions) == 1
        assert tenant.transactions[0].description == "Initial grant"

    def test_add_credits_existing_tenant(self):
        billing = MCUBilling()
        billing.add_credits("t1", 50)
        tenant = billing.add_credits("t1", 30)
        assert tenant.balance == 80
        assert tenant.total_credited == 80
        assert len(tenant.transactions) == 2

    def test_add_credits_invalid_amount(self):
        billing = MCUBilling()
        with pytest.raises(ValueError, match="must be positive"):
            billing.add_credits("tenant-123", 0)
        with pytest.raises(ValueError, match="must be positive"):
            billing.add_credits("tenant-123", -10)

    def test_deduct_simple_task(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 10)

        result = billing.deduct("tenant-123", "simple")

        assert result.success is True
        assert result.amount_deducted == 1
        assert result.balance_after == 9
        assert billing.get_balance("tenant-123") == 9

    def test_deduct_standard_task(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 10)

        result = billing.deduct("tenant-123", "standard")

        assert result.success is True
        assert result.amount_deducted == 3
        assert result.balance_after == 7

    def test_deduct_complex_task(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 10)

        result = billing.deduct("tenant-123", "complex")

        assert result.success is True
        assert result.amount_deducted == 5
        assert result.balance_after == 5

    def test_deduct_unknown_complexity_defaults_simple(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        result = billing.deduct("t1", "unknown_type")
        assert result.success is True
        assert result.amount_deducted == 1
        assert result.balance_after == 9

    def test_deduct_insufficient_balance(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 2)

        result = billing.deduct("tenant-123", "standard")  # Needs 3 MCU

        assert result.success is False
        assert result.error != ""
        assert "Insufficient MCU" in result.error
        assert billing.get_balance("tenant-123") == 2  # Unchanged

    def test_deduct_zero_balance(self):
        billing = MCUBilling()
        result = billing.deduct("t1", "simple")
        assert result.success is False
        assert "Insufficient MCU" in result.error

    def test_deduct_low_balance_trigger(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 15)

        billing.deduct("tenant-123", "complex")  # 15 - 5 = 10
        billing.deduct("tenant-123", "complex")  # 10 - 5 = 5

        assert billing.is_low_balance("tenant-123") is True

    def test_deduct_low_balance_warning(self):
        billing = MCUBilling()
        billing.add_credits("t1", 12)
        result = billing.deduct("t1", "standard")
        assert result.success is True
        assert result.low_balance is True  # 12-3=9 < 10 threshold

    def test_deduct_with_mission_id(self):
        billing = MCUBilling()
        billing.add_credits("t1", 20)
        result1 = billing.deduct("t1", "simple", mission_id="m-123")
        result2 = billing.deduct("t1", "simple", mission_id="m_456")
        assert result1.success is True
        assert result2.success is True
        tenant = billing.get_tenant("t1")
        assert tenant is not None
        debit_txs = [t for t in tenant.transactions if t.transaction_type == "debit"]
        assert debit_txs[0].mission_id == "m-123"
        assert debit_txs[1].mission_id == "m_456"

    def test_deduct_updates_total_debited(self):
        billing = MCUBilling()
        billing.add_credits("t1", 20)
        billing.deduct("t1", "simple")
        billing.deduct("t1", "standard")
        tenant = billing.get_tenant("t1")
        assert tenant is not None
        assert tenant.total_debited == 4  # 1 + 3

    def test_refund_credits(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 10)
        billing.deduct("tenant-123", "standard")  # 10 - 3 = 7

        tenant = billing.refund("tenant-123", 5, mission_id="mission-001")
        assert tenant is not None
        assert tenant.balance == 12
        assert tenant.total_refunded == 5

    def test_refund_invalid_amount(self):
        billing = MCUBilling()
        with pytest.raises(ValueError, match="must be positive"):
            billing.refund("tenant-123", 0)
        with pytest.raises(ValueError, match="must be positive"):
            billing.refund("tenant-123", -5)

    def test_refund_nonexistent_tenant(self):
        billing = MCUBilling()
        result = billing.refund("nonexistent", 10)
        assert result is None

    def test_get_balance_existing_and_nonexistent(self):
        billing = MCUBilling()
        billing.add_credits("t1", 50)
        assert billing.get_balance("t1") == 50
        assert billing.get_balance("nonexistent") == 0

    def test_get_tenant(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 100)

        tenant = billing.get_tenant("tenant-123")
        assert tenant is not None
        assert tenant.balance == 100

    def test_get_nonexistent_tenant(self):
        billing = MCUBilling()
        tenant = billing.get_tenant("nonexistent")
        assert tenant is None

    def test_is_low_balance(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 15)

        assert billing.is_low_balance("tenant-123") is False

        billing.deduct("tenant-123", "complex")  # 15 - 5 = 10
        billing.deduct("tenant-123", "complex")  # 10 - 5 = 5
        assert billing.is_low_balance("tenant-123") is True

    def test_tenant_count(self):
        billing = MCUBilling()
        assert billing.tenant_count == 0
        billing.add_credits("t1", 10)
        billing.add_credits("t2", 20)
        assert billing.tenant_count == 2

    def test_tenant_count_exception_returns_zero(self, monkeypatch: pytest.MonkeyPatch):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        assert billing.tenant_count == 1
        monkeypatch.setattr(billing._store, "_connect", MagicMock(side_effect=RuntimeError("db error")))
        assert billing.tenant_count == 0

    def test_custom_low_threshold(self):
        billing = MCUBilling(low_threshold=50)
        billing.add_credits("t1", 30)
        assert billing.is_low_balance("t1") is True


class TestMCUBillingWebhooks:
    """Test MCU Billing webhook integration."""

    def test_webhook_handler_configured(self):
        webhook_called = []

        def mock_webhook(event_type: str, payload: dict) -> None:
            webhook_called.append((event_type, payload))

        billing = MCUBilling(webhook_handler=mock_webhook)
        billing.add_credits("tenant-123", 15)
        billing.deduct("tenant-123", "complex")  # 15 - 5 = 10 (not low)
        billing.deduct("tenant-123", "complex")  # 10 - 5 = 5 (low!)

        assert len(webhook_called) == 1
        event_type, payload = webhook_called[0]
        assert event_type == "credits.low"
        assert payload["tenant_id"] == "tenant-123"
        assert payload["current_balance"] == 5
        assert payload["threshold"] == 10

    def test_webhook_only_once_per_tenant(self):
        webhook_called = []

        def mock_webhook(event_type: str, payload: dict) -> None:
            webhook_called.append((event_type, payload))

        billing = MCUBilling(webhook_handler=mock_webhook)
        billing.add_credits("tenant-123", 20)

        billing.deduct("tenant-123", "complex")  # 20 - 5 = 15
        billing.deduct("tenant-123", "complex")  # 15 - 5 = 10
        billing.deduct("tenant-123", "complex")  # 10 - 5 = 5 (triggers)
        billing.deduct("tenant-123", "complex")  # 5 - 5 = 0 (already notified)

        assert len(webhook_called) == 1

    def test_reset_low_balance_notification(self):
        webhook_called = []

        def mock_webhook(event_type: str, payload: dict) -> None:
            webhook_called.append((event_type, payload))

        billing = MCUBilling(webhook_handler=mock_webhook)
        billing.add_credits("tenant-123", 20)

        billing.deduct("tenant-123", "complex")
        billing.deduct("tenant-123", "complex")
        billing.deduct("tenant-123", "complex")
        assert len(webhook_called) == 1

        billing.reset_low_balance_notification("tenant-123")

        billing.add_credits("tenant-123", 10)  # 5 + 10 = 15
        billing.deduct("tenant-123", "complex")  # 15 - 5 = 10
        billing.deduct("tenant-123", "complex")  # 10 - 5 = 5 (triggers again)

        assert len(webhook_called) == 2

    def test_no_webhook_handler(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 15)
        billing.deduct("tenant-123", "complex")
        billing.deduct("tenant-123", "complex")

        assert billing.is_low_balance("tenant-123") is True

    def test_webhook_handler_exception_handled(self):
        def failing_webhook(event_type: str, payload: dict) -> None:
            raise RuntimeError("Webhook endpoint down")

        billing = MCUBilling(webhook_handler=failing_webhook)
        billing.add_credits("t1", 12)
        # Should not raise exception
        result = billing.deduct("t1", "standard")
        assert result.success is True
        assert result.low_balance is True


class TestMCUBillingTransactions:
    """Test transaction history."""

    def test_transaction_history(self):
        billing = MCUBilling()
        billing.add_credits("tenant-123", 100)
        billing.deduct("tenant-123", "standard", mission_id="m1")
        billing.deduct("tenant-123", "simple", mission_id="m2")

        tenant = billing.get_tenant("tenant-123")
        assert tenant is not None
        assert len(tenant.transactions) == 3

        tx1, tx2, tx3 = tenant.transactions
        assert tx1.amount == 100
        assert tx2.amount == -3
        assert tx3.amount == -1


class TestCheckQuotaAndPaymentAndUsage:
    """Test quota check, payment settlement stub, and usage recording."""

    def test_check_quota_default_tier(self):
        billing = MCUBilling()
        billing.add_credits("t1", 75)
        quota = billing.check_quota("t1")
        assert quota.remaining_mcu == 75
        assert quota.total_mcu == 75
        assert quota.tier == "basic"
        assert quota.reset_at is not None

    def test_check_quota_with_tier_method(self):
        billing = MCUBilling()
        billing.add_credits("t1", 50)
        billing._get_tier_for_org = lambda tenant_id: "pro"  # type: ignore[attr-defined]
        quota = billing.check_quota("t1")
        assert quota.tier == "pro"

    def test_check_quota_with_tier_method_exception(self):
        billing = MCUBilling()
        billing.add_credits("t1", 50)

        def bad_tier(tenant_id: str) -> str:
            raise RuntimeError("tier lookup failed")

        billing._get_tier_for_org = bad_tier  # type: ignore[attr-defined]
        quota = billing.check_quota("t1")
        assert quota.tier == "basic"

    def test_settle_payment(self):
        billing = MCUBilling()
        res = billing.settle_payment(25.5, "USD", "recipient-001")
        assert res.pending is True
        assert res.amount == 25.5
        assert res.currency == "USD"
        assert res.recipient == "recipient-001"
        assert "not yet implemented" in res.note

    def test_record_usage_valid(self):
        billing = MCUBilling()
        billing.record_usage(
            agent="agent-alpha",
            tokens=500,
            model="gpt-4o",
            operation="chat",
        )

    def test_record_usage_negative_tokens_raises(self):
        billing = MCUBilling()
        with pytest.raises(ValueError, match="Token count must be non-negative"):
            billing.record_usage(
                agent="agent-alpha",
                tokens=-10,
                model="gpt-4o",
                operation="chat",
            )

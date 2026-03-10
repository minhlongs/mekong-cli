"""Tests for MCU Billing — Condition C4 credit accounting system."""

import pytest

from src.core.mcu_billing import (
    MCUBilling,
    MCUTransaction,
    TenantBalance,
    DeductionResult,
    MCU_COSTS,
    TIER_CREDITS,
    LOW_BALANCE_THRESHOLD,
)


class TestMCUCosts:
    """Verify MCU cost constants."""

    def test_simple_cost(self):
        assert MCU_COSTS["simple"] == 1

    def test_standard_cost(self):
        assert MCU_COSTS["standard"] == 3

    def test_complex_cost(self):
        assert MCU_COSTS["complex"] == 5

    def test_tier_credits_starter(self):
        assert TIER_CREDITS["starter"] == 50

    def test_tier_credits_growth(self):
        assert TIER_CREDITS["growth"] == 200

    def test_tier_credits_premium(self):
        assert TIER_CREDITS["premium"] == 1000

    def test_low_balance_threshold(self):
        assert LOW_BALANCE_THRESHOLD == 10


class TestMCUTransaction:
    """Test MCUTransaction dataclass."""

    def test_create_credit_transaction(self):
        tx = MCUTransaction(
            tenant_id="t1",
            amount=100,
            balance_after=100,
            transaction_type="credit",
        )
        assert tx.tenant_id == "t1"
        assert tx.amount == 100
        assert tx.transaction_type == "credit"

    def test_to_dict(self):
        tx = MCUTransaction(
            tenant_id="t1",
            amount=-3,
            balance_after=97,
            transaction_type="debit",
            description="test",
            mission_id="m1",
        )
        d = tx.to_dict()
        assert d["tenant_id"] == "t1"
        assert d["amount"] == -3
        assert d["balance_after"] == 97
        assert d["transaction_type"] == "debit"
        assert d["mission_id"] == "m1"
        assert "timestamp" in d


class TestTenantBalance:
    """Test TenantBalance dataclass."""

    def test_default_values(self):
        tb = TenantBalance(tenant_id="t1")
        assert tb.balance == 0
        assert tb.total_credited == 0
        assert tb.total_debited == 0
        assert tb.total_refunded == 0
        assert tb.transactions == []

    def test_to_dict(self):
        tb = TenantBalance(tenant_id="t1", balance=50, total_credited=100)
        d = tb.to_dict()
        assert d["tenant_id"] == "t1"
        assert d["balance"] == 50
        assert d["transaction_count"] == 0


class TestDeductionResult:
    """Test DeductionResult dataclass."""

    def test_successful_deduction(self):
        r = DeductionResult(
            success=True,
            balance_before=100,
            balance_after=97,
            amount_deducted=3,
        )
        assert r.success is True
        assert r.low_balance is False
        assert r.error == ""

    def test_to_dict(self):
        r = DeductionResult(
            success=False,
            balance_before=2,
            balance_after=2,
            amount_deducted=0,
            error="Insufficient MCU",
        )
        d = r.to_dict()
        assert d["success"] is False
        assert d["error"] == "Insufficient MCU"


class TestMCUBillingAddCredits:
    """Test MCUBilling.add_credits."""

    def test_add_credits_new_tenant(self):
        billing = MCUBilling()
        tenant = billing.add_credits("t1", 100)
        assert tenant.balance == 100
        assert tenant.total_credited == 100
        assert len(tenant.transactions) == 1

    def test_add_credits_existing_tenant(self):
        billing = MCUBilling()
        billing.add_credits("t1", 50)
        tenant = billing.add_credits("t1", 30)
        assert tenant.balance == 80
        assert tenant.total_credited == 80
        assert len(tenant.transactions) == 2

    def test_add_credits_zero_raises(self):
        billing = MCUBilling()
        with pytest.raises(ValueError, match="positive"):
            billing.add_credits("t1", 0)

    def test_add_credits_negative_raises(self):
        billing = MCUBilling()
        with pytest.raises(ValueError, match="positive"):
            billing.add_credits("t1", -10)

    def test_add_credits_with_description(self):
        billing = MCUBilling()
        tenant = billing.add_credits("t1", 50, description="Polar checkout")
        tx = tenant.transactions[-1]
        assert tx.description == "Polar checkout"


class TestMCUBillingDeduct:
    """Test MCUBilling.deduct."""

    def test_deduct_simple(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        result = billing.deduct("t1", "simple")
        assert result.success is True
        assert result.amount_deducted == 1
        assert result.balance_after == 9

    def test_deduct_standard(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        result = billing.deduct("t1", "standard")
        assert result.success is True
        assert result.amount_deducted == 3
        assert result.balance_after == 7

    def test_deduct_complex(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        result = billing.deduct("t1", "complex")
        assert result.success is True
        assert result.amount_deducted == 5
        assert result.balance_after == 5

    def test_deduct_insufficient_balance(self):
        billing = MCUBilling()
        billing.add_credits("t1", 2)
        result = billing.deduct("t1", "standard")
        assert result.success is False
        assert result.amount_deducted == 0
        assert "Insufficient" in result.error

    def test_deduct_zero_balance(self):
        billing = MCUBilling()
        result = billing.deduct("t1", "simple")
        assert result.success is False

    def test_deduct_unknown_complexity_defaults_simple(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        result = billing.deduct("t1", "unknown_type")
        assert result.success is True
        assert result.amount_deducted == 1

    def test_deduct_low_balance_warning(self):
        billing = MCUBilling()
        billing.add_credits("t1", 12)
        result = billing.deduct("t1", "standard")
        assert result.success is True
        assert result.low_balance is True  # 12-3=9 < 10 threshold

    def test_deduct_with_mission_id(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        result = billing.deduct("t1", "simple", mission_id="m-123")
        assert result.success is True
        tenant = billing.get_tenant("t1")
        debit_tx = [t for t in tenant.transactions if t.transaction_type == "debit"]
        assert debit_tx[0].mission_id == "m-123"

    def test_deduct_updates_total_debited(self):
        billing = MCUBilling()
        billing.add_credits("t1", 20)
        billing.deduct("t1", "simple")
        billing.deduct("t1", "standard")
        tenant = billing.get_tenant("t1")
        assert tenant.total_debited == 4  # 1 + 3


class TestMCUBillingRefund:
    """Test MCUBilling.refund."""

    def test_refund_existing_tenant(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        billing.deduct("t1", "complex")
        tenant = billing.refund("t1", 5)
        assert tenant is not None
        assert tenant.balance == 10  # 10-5+5
        assert tenant.total_refunded == 5

    def test_refund_nonexistent_tenant(self):
        billing = MCUBilling()
        result = billing.refund("ghost", 10)
        assert result is None

    def test_refund_zero_raises(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        with pytest.raises(ValueError, match="positive"):
            billing.refund("t1", 0)

    def test_refund_negative_raises(self):
        billing = MCUBilling()
        billing.add_credits("t1", 10)
        with pytest.raises(ValueError, match="positive"):
            billing.refund("t1", -5)


class TestMCUBillingQueries:
    """Test MCUBilling query methods."""

    def test_get_balance_existing(self):
        billing = MCUBilling()
        billing.add_credits("t1", 50)
        assert billing.get_balance("t1") == 50

    def test_get_balance_nonexistent(self):
        billing = MCUBilling()
        assert billing.get_balance("ghost") == 0

    def test_get_tenant_existing(self):
        billing = MCUBilling()
        billing.add_credits("t1", 50)
        tenant = billing.get_tenant("t1")
        assert tenant is not None
        assert tenant.tenant_id == "t1"

    def test_get_tenant_nonexistent(self):
        billing = MCUBilling()
        assert billing.get_tenant("ghost") is None

    def test_is_low_balance_true(self):
        billing = MCUBilling()
        billing.add_credits("t1", 5)
        assert billing.is_low_balance("t1") is True

    def test_is_low_balance_false(self):
        billing = MCUBilling()
        billing.add_credits("t1", 50)
        assert billing.is_low_balance("t1") is False

    def test_tenant_count(self):
        billing = MCUBilling()
        assert billing.tenant_count == 0
        billing.add_credits("t1", 10)
        billing.add_credits("t2", 20)
        assert billing.tenant_count == 2

    def test_custom_low_threshold(self):
        billing = MCUBilling(low_threshold=50)
        billing.add_credits("t1", 30)
        assert billing.is_low_balance("t1") is True

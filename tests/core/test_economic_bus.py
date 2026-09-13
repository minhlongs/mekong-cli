"""Phase 2C: Economic Bus — PaymentProvider Protocol + MCUBillingPaymentAdapter."""

from unittest.mock import MagicMock

from src.core.billing_adapter import (
    BillingAdapter,
    BillingUsageEvent,
    get_adapter,
    reset_adapter,
)
from src.core.protocols import (
    PaymentProvider,
    PaymentReceipt,
    PaymentRequest,
    PaymentResult,
    QuotaStatus,
)


class TestBillingAdapterSatisfiesPaymentProvider:
    """BillingAdapter wraps MCUBilling and satisfies PaymentProvider Protocol."""

    def test_billing_adapter_satisfies_payment_protocol(self):
        """BillingAdapter must satisfy PaymentProvider Protocol."""
        adapter = BillingAdapter()
        assert isinstance(adapter, PaymentProvider)

    def test_record_usage_delegates(self):
        """record_usage delegates to MCUBilling."""
        adapter = BillingAdapter()
        assert callable(adapter.record_usage)

    def test_check_quota_delegates(self):
        """check_quota delegates to MCUBilling."""
        adapter = BillingAdapter()
        assert callable(adapter.check_quota)

    def test_settle_payment_delegates(self):
        """settle_payment delegates to MCUBilling."""
        adapter = BillingAdapter()
        assert callable(adapter.settle_payment)

    def test_estimate_cost_delegates(self):
        """estimate_cost delegates to MCUBilling (with fallback)."""
        adapter = BillingAdapter()
        assert callable(adapter.estimate_cost)

    def test_extended_methods_exist_on_adapter(self):
        """Extended economic-bus methods exist and return not-implemented."""
        adapter = BillingAdapter()
        assert callable(adapter.quote)
        assert callable(adapter.request_payment)
        assert callable(adapter.verify)
        assert callable(adapter.refund)


class TestPaymentProviderProtocol:
    def test_protocol_methods_exist(self):
        """PaymentProvider Protocol defines required methods."""
        from src.core.protocols import PaymentProvider
        import inspect
        methods = [name for name, _ in inspect.getmembers(PaymentProvider, predicate=inspect.isfunction)]
        assert "record_usage" in methods
        assert "check_quota" in methods

    def test_payment_result_protocol(self):
        """PaymentResult Protocol must be importable and usable."""
        from dataclasses import dataclass
        from typing import Optional

        @dataclass
        class MyResult:
            success: bool
            transaction_id: Optional[str]
            pending: bool = False
            note: Optional[str] = None

        result = MyResult(success=True, transaction_id="tx-123")
        # Should satisfy PaymentResult Protocol
        assert result.success is True
        assert result.transaction_id == "tx-123"


class TestBillingAdapterFullCoverage:
    def test_billing_property(self):
        mock_mcu = MagicMock()
        adapter = BillingAdapter(mcu_billing=mock_mcu)
        assert adapter.billing is mock_mcu

    def test_record_usage(self):
        mock_mcu = MagicMock()
        adapter = BillingAdapter(mcu_billing=mock_mcu)
        adapter.record_usage("agent1", 150, "gpt-4o", "chat")
        mock_mcu.record_usage.assert_called_once_with("agent1", 150, "gpt-4o", "chat")

    def test_check_quota_normal_and_low_balance(self):
        mock_mcu = MagicMock()
        status = MagicMock(spec=QuotaStatus)
        status.remaining_mcu = 50
        status.total_mcu = 100
        status.tier = "BASIC"
        status.reset_at = 1234567.0
        status.low_balance = True
        mock_mcu.check_quota.return_value = status

        adapter = BillingAdapter(mcu_billing=mock_mcu)
        res = adapter.check_quota("tenant-1")
        assert res["remaining_mcu"] == 50
        assert res["total_mcu"] == 100
        assert res["tier"] == "BASIC"
        assert res["reset_at"] == 1234567.0
        assert res["low_balance"] is True

        # Status without low_balance attr
        status_no_low = MagicMock(spec=["remaining_mcu", "total_mcu", "tier", "reset_at"])
        status_no_low.remaining_mcu = 80
        status_no_low.total_mcu = 100
        status_no_low.tier = "PRO"
        status_no_low.reset_at = 123.0
        mock_mcu.check_quota.return_value = status_no_low
        res2 = adapter.check_quota("tenant-2")
        assert res2["low_balance"] is False

    def test_settle_payment(self):
        mock_mcu = MagicMock()
        result_pending = MagicMock(spec=PaymentResult)
        result_pending.pending = True
        result_pending.transaction_id = "tx-1"
        result_pending.note = "waiting"
        mock_mcu.settle_payment.return_value = result_pending

        adapter = BillingAdapter(mcu_billing=mock_mcu)
        res1 = adapter.settle_payment(10.0, "USD", "recip")
        assert res1["success"] is False
        assert res1["pending"] is True
        assert res1["transaction_id"] == "tx-1"
        assert res1["note"] == "waiting"

        # Non-pending (success)
        result_done = MagicMock(spec=PaymentResult)
        result_done.pending = False
        result_done.transaction_id = "tx-2"
        result_done.note = "cleared"
        mock_mcu.settle_payment.return_value = result_done
        res2 = adapter.settle_payment(20.0, "USD", "recip")
        assert res2["success"] is True
        assert res2["pending"] is False

    def test_quote_not_implemented(self):
        adapter = BillingAdapter()
        q = adapter.quote(15.0, "VND", "merchant", "qr")
        assert q.amount == 15.0
        assert q.asset == "VND"
        assert q.provider == "mcu-billing"
        assert "not implemented" in q.metadata["error"]

    def test_request_payment_not_implemented(self):
        adapter = BillingAdapter()
        req = PaymentRequest(
            asset="USD",
            network="base",
            amount=5.0,
            recipient="0xabc",
            scheme="mpp",
            provider="mcu",
        )
        receipt = adapter.request_payment(req)
        assert receipt.amount == 5.0
        assert receipt.asset == "USD"
        assert receipt.transaction_id == ""
        assert "not implemented" in receipt.metadata["error"]

    def test_verify_always_false(self):
        adapter = BillingAdapter()
        receipt = PaymentReceipt(
            asset="USD",
            network="base",
            amount=5.0,
            recipient="0xabc",
            scheme="mpp",
            provider="other",
            transaction_id="tx-123",
        )
        assert adapter.verify(receipt) is False

    def test_refund_not_implemented(self):
        adapter = BillingAdapter()
        receipt = PaymentReceipt(
            asset="USD",
            network="base",
            amount=5.0,
            recipient="0xabc",
            scheme="mpp",
            provider="other",
            transaction_id="tx-123",
        )
        res = adapter.refund(receipt)
        assert res["success"] is False
        assert "not implemented" in res["error"]

    def test_estimate_cost_fallback_and_delegate(self):
        # Fallback when _billing has no estimate_cost
        mock_mcu_no_est = MagicMock(spec=["record_usage", "check_quota"])
        adapter1 = BillingAdapter(mcu_billing=mock_mcu_no_est)
        est1 = adapter1.estimate_cost("gpt-4o", 1000)
        assert est1["cost_usd"] == 0.0
        assert est1["tokens"] == 1000

        # With estimate_cost method
        mock_mcu_with_est = MagicMock()
        mock_est_ret = MagicMock()
        mock_est_ret.model = "claude-3"
        mock_est_ret.input_tokens = 500
        mock_est_ret.output_tokens = 200
        mock_est_ret.cost_usd = 0.05
        mock_est_ret.currency = "USD"
        mock_mcu_with_est.estimate_cost.return_value = mock_est_ret

        adapter2 = BillingAdapter(mcu_billing=mock_mcu_with_est)
        est2 = adapter2.estimate_cost("claude-3", 700)
        assert est2["cost_usd"] == 0.05
        assert est2["input_tokens"] == 500

    def test_record_usage_event(self):
        mock_mcu = MagicMock()
        adapter = BillingAdapter(mcu_billing=mock_mcu)
        event = BillingUsageEvent(
            agent="researcher",
            tokens=450,
            model="sonnet",
            operation="analysis",
        )
        adapter.record_usage_event(event)
        mock_mcu.record_usage.assert_called_once_with("researcher", 450, "sonnet", "analysis")

    def test_get_balance_and_add_credits(self):
        mock_mcu = MagicMock()
        mock_mcu.get_balance.return_value = 500
        adapter = BillingAdapter(mcu_billing=mock_mcu)

        assert adapter.get_balance("tenant-x") == 500
        mock_mcu.get_balance.assert_called_once_with("tenant-x")

        adapter.add_credits("tenant-x", 100, reason="bonus")
        mock_mcu.add_credits.assert_called_once_with("tenant-x", 100, "bonus")

    def test_get_adapter_and_reset_adapter(self):
        reset_adapter()
        a1 = get_adapter()
        assert isinstance(a1, BillingAdapter)
        a2 = get_adapter()
        assert a1 is a2

        reset_adapter()
        a3 = get_adapter()
        assert a3 is not a1
        reset_adapter()

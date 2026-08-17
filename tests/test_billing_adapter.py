"""Tests for BillingAdapter — unified billing interface wrapping MCUBilling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pytest

from src.core.billing_adapter import BillingAdapter, BillingUsageEvent, reset_adapter
from src.core.protocols import PaymentProvider, PaymentResult, QuotaStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_mcu() -> Any:
    """Minimal fake MCUBilling with controllable return values."""

    class _Fake:
        def __init__(self) -> None:
            self.calls: Dict[str, Any] = {}
            self._balance = 50

        @property
        def balance(self) -> int:
            return self._balance

        def record_usage(self, agent: str, tokens: int, model: str, operation: str) -> None:
            self.calls.setdefault("record_usage", []).append(
                (agent, tokens, model, operation)
            )

        def check_quota(self, tenant_id: str) -> QuotaStatus:
            self.calls.setdefault("check_quota", []).append(tenant_id)

            @dataclass
            class _QS(QuotaStatus):
                remaining_mcu: int = self._balance
                total_mcu: int = 100
                tier: str = "BASIC"
                reset_at: Optional[str] = None
                low_balance: bool = self._balance < 10

            return _QS()

        def settle_payment(self, amount: float, currency: str, recipient: str) -> PaymentResult:
            self.calls.setdefault("settle_payment", []).append(
                (amount, currency, recipient)
            )

            @dataclass
            class _PR(PaymentResult):
                success: bool = True
                transaction_id: str = "tx-123"
                pending: bool = False
                note: str = "ok"

            return _PR()

        def get_balance(self, tenant_id: str) -> int:
            self.calls.setdefault("get_balance", []).append(tenant_id)
            return self._balance

        def add_credits(self, tenant_id: str, amount: int, reason: str = "") -> None:
            self.calls.setdefault("add_credits", []).append((tenant_id, amount, reason))
            self._balance += amount

    return _Fake()


@pytest.fixture()
def adapter(fake_mcu: Any) -> BillingAdapter:
    return BillingAdapter(mcu_billing=fake_mcu)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_adapter()


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------

class TestAdapterCreation:
    def test_adapter_creation_default(self) -> None:
        adapter = BillingAdapter()
        assert adapter.billing is not None

    def test_adapter_creation_with_mcu_billing(self, fake_mcu: Any) -> None:
        adapter = BillingAdapter(mcu_billing=fake_mcu)
        assert adapter.billing is fake_mcu


# ---------------------------------------------------------------------------
# record_usage
# ---------------------------------------------------------------------------

class TestRecordUsage:
    def test_record_usage_delegates_to_mcu(self, adapter: BillingAdapter, fake_mcu: Any) -> None:
        adapter.record_usage("agent-x", 42, "gpt-4o", "chat")
        assert fake_mcu.calls["record_usage"] == [("agent-x", 42, "gpt-4o", "chat")]

    def test_record_usage_event_dataclass(self, adapter: BillingAdapter, fake_mcu: Any) -> None:
        event = BillingUsageEvent(agent="agent-x", tokens=99, model="gpt-4o", operation="summarize")
        adapter.record_usage_event(event)
        assert fake_mcu.calls["record_usage"] == [("agent-x", 99, "gpt-4o", "summarize")]


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

class TestCheckQuota:
    def test_check_quota_returns_dict_with_required_fields(
        self, adapter: BillingAdapter, fake_mcu: Any
    ) -> None:
        result = adapter.check_quota("tenant-1")
        assert set(result.keys()) >= {"remaining_mcu", "total_mcu", "tier", "reset_at"}
        assert result["remaining_mcu"] == fake_mcu.balance
        assert fake_mcu.calls["check_quota"] == ["tenant-1"]

    def test_check_quota_low_balance_flag(self, adapter: BillingAdapter, fake_mcu: Any) -> None:
        fake_mcu._balance = 5
        result = adapter.check_quota("tenant-1")
        assert result["low_balance"] is True


# ---------------------------------------------------------------------------
# settle_payment
# ---------------------------------------------------------------------------

class TestSettlePayment:
    def test_settle_payment_returns_dict_with_required_fields(
        self, adapter: BillingAdapter, fake_mcu: Any
    ) -> None:
        result = adapter.settle_payment(25.0, "USD", "recipient-abc")
        assert set(result.keys()) >= {"success", "transaction_id", "pending", "note"}
        assert result["success"] is True
        assert fake_mcu.calls["settle_payment"] == [(25.0, "USD", "recipient-abc")]


# ---------------------------------------------------------------------------
# estimate_cost
# ---------------------------------------------------------------------------

class TestEstimateCost:
    def test_estimate_cost_returns_dict_when_no_method(self, adapter: BillingAdapter) -> None:
        result = adapter.estimate_cost("gpt-4o", 1000)
        assert result["cost_usd"] == 0.0
        assert result["currency"] == "USD"
        assert result["model"] == "gpt-4o"

    def test_estimate_cost_with_fake_method(self, fake_mcu: Any) -> None:
        class _Est:
            model = "gpt-4o"
            input_tokens = 100
            output_tokens = 900
            cost_usd = 0.05
            currency = "USD"

        fake_mcu.estimate_cost = lambda model, tokens: _Est()  # type: ignore[attr-defined]
        adapter = BillingAdapter(mcu_billing=fake_mcu)
        result = adapter.estimate_cost("gpt-4o", 1000)
        assert result["cost_usd"] == 0.05


# ---------------------------------------------------------------------------
# get_balance / add_credits
# ---------------------------------------------------------------------------

class TestBalanceHelpers:
    def test_get_balance(self, adapter: BillingAdapter, fake_mcu: Any) -> None:
        assert adapter.get_balance("tenant-1") == 50
        assert fake_mcu.calls["get_balance"] == ["tenant-1"]

    def test_add_credits(self, adapter: BillingAdapter, fake_mcu: Any) -> None:
        adapter.add_credits("tenant-1", 25, "top-up")
        assert fake_mcu._balance == 75
        assert fake_mcu.calls["add_credits"] == [("tenant-1", 25, "top-up")]


# ---------------------------------------------------------------------------
# PaymentProvider protocol satisfaction
# ---------------------------------------------------------------------------

class TestProtocolSatisfaction:
    def test_billing_adapter_satisfies_payment_provider(
        self, adapter: BillingAdapter
    ) -> None:
        """BillingAdapter must satisfy the PaymentProvider protocol."""
        def _expects_provider(p: PaymentProvider) -> None:
            p.record_usage("a", 1, "m", "op")
            p.check_quota("org-1")
            p.settle_payment(1.0, "USD", "r")

        _expects_provider(adapter)  # must not raise TypeError
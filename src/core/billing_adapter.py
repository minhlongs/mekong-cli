# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""BillingAdapter — unified billing interface wrapping MCUBilling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.core.protocols import PaymentReceipt, PaymentRequest, PaymentResult, QuotaStatus, Quote


@dataclass(frozen=True)
class BillingUsageEvent:
    """Structured usage event for billing recording."""
    agent: str
    tokens: int
    model: str
    operation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BillingAdapter:
    """Unified billing interface wrapping MCUBilling."""

    _NOT_IMPLEMENTED = (
        "not implemented: MCUBilling is an internal credit ledger; "
        "use a dedicated PaymentProvider adapter for settlement"
    )

    def __init__(self, mcu_billing: Any = None) -> None:
        from src.core.mcu_billing import MCUBilling
        self._billing = mcu_billing if mcu_billing is not None else MCUBilling()

    @property
    def billing(self) -> Any:
        return self._billing

    def record_usage(self, agent: str, tokens: int, model: str, operation: str) -> None:
        self._billing.record_usage(agent, tokens, model, operation)

    def check_quota(self, tenant_id: str) -> Dict[str, Any]:
        status: QuotaStatus = self._billing.check_quota(tenant_id)
        return {
            "remaining_mcu": status.remaining_mcu,
            "total_mcu": status.total_mcu,
            "tier": status.tier,
            "reset_at": status.reset_at,
            "low_balance": getattr(status, "low_balance", False),
        }

    def settle_payment(self, amount: float, currency: str, recipient: str) -> Dict[str, Any]:
        result: PaymentResult = self._billing.settle_payment(amount, currency, recipient)
        return {
            "success": not result.pending,
            "transaction_id": result.transaction_id,
            "pending": result.pending,
            "note": result.note,
        }

    def quote(self, amount: float, currency: str, recipient: str, scheme: str) -> Quote:
        return Quote(
            asset=currency, network="mcu-internal", amount=amount,
            recipient=recipient, scheme=scheme, provider="mcu-billing",
            metadata={"error": self._NOT_IMPLEMENTED},
        )

    def request_payment(self, req: PaymentRequest) -> PaymentReceipt:
        return PaymentReceipt(
            asset=req.asset, network=req.network, amount=req.amount,
            recipient=req.recipient, scheme=req.scheme, provider="mcu-billing",
            transaction_id="", metadata={"error": self._NOT_IMPLEMENTED},
        )

    def verify(self, receipt: PaymentReceipt) -> bool:
        return False

    def refund(self, receipt: PaymentReceipt) -> Dict[str, Any]:
        return {
            "success": False, "transaction_id": None,
            "pending": False, "note": None, "error": self._NOT_IMPLEMENTED,
        }

    def estimate_cost(self, model: str, tokens: int) -> Dict[str, Any]:
        if hasattr(self._billing, "estimate_cost"):
            est: Any = self._billing.estimate_cost(model, tokens)
            return {
                "model": est.model,
                "input_tokens": getattr(est, "input_tokens", tokens),
                "output_tokens": getattr(est, "output_tokens", tokens),
                "cost_usd": float(est.cost_usd),
                "currency": getattr(est, "currency", "USD"),
            }
        return {"model": model, "tokens": tokens, "cost_usd": 0.0, "currency": "USD"}

    def record_usage_event(self, event: BillingUsageEvent) -> None:
        self.record_usage(agent=event.agent, tokens=event.tokens, model=event.model, operation=event.operation)

    def get_balance(self, tenant_id: str) -> int:
        return self._billing.get_balance(tenant_id)

    def add_credits(self, tenant_id: str, amount: int, reason: str = "") -> None:
        self._billing.add_credits(tenant_id, amount, reason)


_adapter: Optional[BillingAdapter] = None


def get_adapter() -> BillingAdapter:
    global _adapter
    if _adapter is None:
        _adapter = BillingAdapter()
    return _adapter


def reset_adapter() -> None:
    global _adapter
    _adapter = None


__all__ = ["BillingAdapter", "BillingUsageEvent", "get_adapter", "reset_adapter"]
# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MockPaymentProvider — deterministic in-memory PaymentProvider.

Test/dev provider for the economic bus. Guarantees:
- No IO, no network, no keys, no wallet, no real money (§18).
- Deterministic: same inputs always produce the same outputs.
- Idempotent: requests sharing ``metadata["idempotency_key"]`` return the
  SAME receipt and never double-settle.
"""

from __future__ import annotations

from typing import Dict

from src.core.protocols import (
    PaymentReceipt,
    PaymentRequest,
    Quote,
)

from .payment_mock_types import (
    DEFAULT_ASSET,
    DEFAULT_NETWORK,
    DEFAULT_SCHEME,
    MockPaymentResult,
    MockQuotaStatus,
    PROVIDER_NAME,
    deterministic_tx_id,
    idempotency_key_from_receipt,
    idempotency_key_from_request,
    validate_amount,
)


class MockPaymentProvider:
    """Deterministic, idempotent, in-memory PaymentProvider."""

    def __init__(
        self,
        asset: str = DEFAULT_ASSET,
        network: str = DEFAULT_NETWORK,
        scheme: str = DEFAULT_SCHEME,
    ) -> None:
        self._asset = asset
        self._network = network
        self._scheme = scheme
        self._receipts: Dict[str, PaymentReceipt] = {}
        self._settled: Dict[str, float] = {}
        self._refunded: Dict[str, bool] = {}
        self._usage: Dict[str, int] = {}

    def record_usage(self, agent: str, tokens: int, model: str) -> None:
        """Accumulate token usage per agent (in-memory only)."""
        self._usage[agent] = self._usage.get(agent, 0) + max(0, int(tokens))

    def check_quota(self, org_id: str) -> MockQuotaStatus:
        """Return a static quota status (mock has no quota limits)."""
        return MockQuotaStatus(
            remaining_mcu=10_000,
            total_mcu=10_000,
            tier="MOCK",
            reset_at="1970-01-01T00:00:00Z",
        )

    def settle_payment(
        self, amount: float, currency: str, recipient: str
    ) -> MockPaymentResult:
        """Settle via the mock ledger — deterministic, no real money."""
        if amount <= 0:
            return MockPaymentResult(
                success=False,
                transaction_id=None,
                pending=False,
                note=None,
                error=f"invalid amount: {amount!r} (must be > 0)",
            )
        tx_id = deterministic_tx_id(
            self._asset, self._network, amount, recipient, self._scheme, ""
        )
        self._settled[tx_id] = self._settled.get(tx_id, 0.0) + amount
        return MockPaymentResult(
            success=True,
            transaction_id=tx_id,
            pending=False,
            note="mock settlement",
        )

    def quote(
        self, amount: float, currency: str, recipient: str, scheme: str
    ) -> Quote:
        """Return a deterministic quote. Invalid amount raises ValueError."""
        validate_amount(amount)
        return Quote(
            asset=self._asset,
            network=self._network,
            amount=amount,
            recipient=recipient,
            scheme=scheme or self._scheme,
            provider=PROVIDER_NAME,
            metadata={"currency": currency},
        )

    def request_payment(self, req: PaymentRequest) -> PaymentReceipt:
        """Process a payment request with idempotency protection."""
        validate_amount(req.amount)
        if req.asset != self._asset:
            raise ValueError(f"wrong asset: {req.asset!r} (provider accepts {self._asset!r})")
        if req.network != self._network:
            raise ValueError(f"wrong network: {req.network!r} (provider accepts {self._network!r})")

        key = idempotency_key_from_request(req)
        existing = self._receipts.get(key)
        if existing is not None:
            return existing

        tx_id = deterministic_tx_id(
            req.asset, req.network, req.amount, req.recipient, req.scheme, key
        )
        receipt = PaymentReceipt(
            asset=req.asset,
            network=req.network,
            amount=req.amount,
            recipient=req.recipient,
            scheme=req.scheme,
            provider=PROVIDER_NAME,
            transaction_id=tx_id,
            metadata={"idempotency_key": key},
        )
        self._receipts[key] = receipt
        self._settled[tx_id] = req.amount
        return receipt

    def verify(self, receipt: PaymentReceipt) -> bool:
        """Verify a receipt against the mock ledger."""
        stored = self._receipts.get(idempotency_key_from_receipt(receipt))
        if stored is None or stored.transaction_id != receipt.transaction_id:
            return False
        return not self._refunded.get(receipt.transaction_id, False)

    def refund(self, receipt: PaymentReceipt) -> MockPaymentResult:
        """Refund a previously issued receipt. Idempotent per receipt."""
        if not self.verify(receipt):
            return MockPaymentResult(
                success=False,
                transaction_id=receipt.transaction_id,
                pending=False,
                note=None,
                error="refund rejected: receipt not verifiable",
            )
        self._refunded[receipt.transaction_id] = True
        self._settled.pop(receipt.transaction_id, None)
        return MockPaymentResult(
            success=True,
            transaction_id=receipt.transaction_id,
            pending=False,
            note="mock refund",
        )

    def settled_amount(self, transaction_id: str) -> float:
        """Return total settled amount for a transaction (0 if none)."""
        return self._settled.get(transaction_id, 0.0)

    def usage(self, agent: str) -> int:
        """Return accumulated token usage for an agent."""
        return self._usage.get(agent, 0)

    _validate_amount = staticmethod(validate_amount)
    _idempotency_key = staticmethod(idempotency_key_from_request)
    _idempotency_key_from_receipt = staticmethod(idempotency_key_from_receipt)
    _deterministic_tx_id = staticmethod(deterministic_tx_id)


__all__ = [
    "MockPaymentProvider",
    "MockPaymentResult",
    "MockQuotaStatus",
    "PROVIDER_NAME",
]

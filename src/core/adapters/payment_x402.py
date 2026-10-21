# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""X402SettlementProvider — fail-closed x402 settlement behind PaymentProvider."""

from __future__ import annotations

from typing import Dict, Optional

from src.core.protocols import PaymentReceipt, PaymentRequest, Quote

from .payment_x402_engine import X402ExecutionEngine
from .payment_x402_helpers import content_key, to_atomic, validated_tx
from .payment_x402_shape import (
    X402_SCHEME,
    X402_VERSION,
    PaymentRequired,
    encode_payment_required,
)
from .payment_x402_types import (
    _REQUIRED_FIELDS,
    ApprovalGate,
    ATOMIC_DECIMALS,
    PROVIDER_NAME,
    X402ConfigError,
    X402PaymentResult,
    X402QuotaStatus,
    X402ReplayError,
    X402SettlementError,
    X402Transport,
)


class X402SettlementProvider:
    """Fail-closed x402 settlement provider."""

    def __init__(
        self,
        *,
        endpoint: Optional[str],
        asset: Optional[str],
        network: Optional[str],
        recipient: Optional[str],
        governance: Optional[ApprovalGate],
        transport: Optional[X402Transport],
    ) -> None:
        cfg = {"endpoint": endpoint, "asset": asset, "network": network, "recipient": recipient}
        for name in _REQUIRED_FIELDS:
            if not isinstance(cfg[name], str) or not cfg[name].strip():
                raise X402ConfigError(f"missing required x402 config: {name} (never default-allow)")
        if governance is None or not callable(getattr(governance, "request_approval", None)):
            raise X402ConfigError("missing required x402 config: governance approval gate")
        if transport is None or not callable(transport):
            raise X402ConfigError("missing required x402 config: injected transport callable")
        self._endpoint = str(endpoint).strip()
        self._asset = str(asset).strip()
        self._network = str(network).strip()
        self._recipient = str(recipient).strip()
        self._governance = governance
        self._transport = transport
        self._receipts: Dict[str, PaymentReceipt] = {}
        self._refunded: Dict[str, bool] = {}
        self._usage: Dict[str, int] = {}
        self._engine = X402ExecutionEngine(
            self._endpoint, self._asset, self._network, self._recipient, self._governance, self._transport
        )

    def record_usage(self, agent: str, tokens: int, model: str) -> None:
        self._usage[agent] = self._usage.get(agent, 0) + max(0, int(tokens))

    def check_quota(self, org_id: str) -> X402QuotaStatus:
        return X402QuotaStatus(remaining_mcu=0, total_mcu=0, tier="X402", reset_at="1970-01-01T00:00:00Z")

    def settle_payment(self, amount: float, currency: str, recipient: str) -> X402PaymentResult:
        try:
            key = content_key(self._asset, self._network, to_atomic(amount), recipient)
            req = PaymentRequest(
                asset=self._asset,
                network=self._network,
                amount=amount,
                recipient=recipient,
                scheme=X402_SCHEME,
                provider=PROVIDER_NAME,
                metadata={"idempotency_key": key, "currency": currency},
            )
            receipt = self._settle(req, action="settle_payment")
            return X402PaymentResult(
                success=True,
                transaction_id=receipt.transaction_id,
                pending=False,
                note="x402 settlement confirmed by transport",
            )
        except ValueError as exc:
            return X402PaymentResult(success=False, transaction_id=None, pending=False, error=str(exc))

    def quote(self, amount: float, currency: str, recipient: str, scheme: str) -> Quote:
        atomic = to_atomic(amount)
        if scheme and scheme != X402_SCHEME:
            raise ValueError(f"unsupported scheme: {scheme!r} (x402 uses {X402_SCHEME!r})")
        self._engine.require_recipient(recipient)
        payment_required = encode_payment_required(
            PaymentRequired(
                x402_version=X402_VERSION,
                accepts_asset=self._asset,
                accepts_network=self._network,
                amount=atomic,
                recipient=self._recipient,
            )
        )
        return Quote(
            asset=self._asset,
            network=self._network,
            amount=amount,
            recipient=self._recipient,
            scheme=X402_SCHEME,
            provider=PROVIDER_NAME,
            metadata={"currency": currency, "atomic_amount": atomic, "payment_required": payment_required},
        )

    def request_payment(self, req: PaymentRequest) -> PaymentReceipt:
        to_atomic(req.amount)
        return self._settle(req, action="request_payment")

    def verify(self, receipt: PaymentReceipt) -> bool:
        if receipt.provider != PROVIDER_NAME or receipt.asset != self._asset or receipt.network != self._network:
            return False
        key = receipt.metadata.get("idempotency_key")
        if not key:
            return False
        stored = self._receipts.get(str(key))
        if stored is None or stored.transaction_id != receipt.transaction_id:
            return False
        return not self._refunded.get(receipt.transaction_id, False)

    def refund(self, receipt: PaymentReceipt) -> X402PaymentResult:
        if not self.verify(receipt):
            return X402PaymentResult(
                success=False, transaction_id=receipt.transaction_id, pending=False, error="refund rejected: receipt not verifiable"
            )
        try:
            self._engine.require_approval("refund", receipt.transaction_id)
        except X402SettlementError as exc:
            return X402PaymentResult(success=False, transaction_id=receipt.transaction_id, pending=False, error=str(exc))
        self._refunded[receipt.transaction_id] = True
        return X402PaymentResult(
            success=True, transaction_id=receipt.transaction_id, pending=False, note="x402 refund recorded"
        )

    def usage(self, agent: str) -> int:
        return self._usage.get(agent, 0)

    def _settle(self, req: PaymentRequest, action: str) -> PaymentReceipt:
        return self._engine.execute_settle(req, action, self._receipts)

    _to_atomic = staticmethod(to_atomic)
    _content_key = staticmethod(content_key)
    _validated_tx = staticmethod(validated_tx)


__all__ = [
    "X402SettlementProvider",
    "X402QuotaStatus",
    "X402PaymentResult",
    "X402ConfigError",
    "X402ReplayError",
    "X402SettlementError",
    "X402Transport",
    "ApprovalGate",
    "PROVIDER_NAME",
    "ATOMIC_DECIMALS",
]

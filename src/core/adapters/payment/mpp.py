# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MPPSettlementProvider — fail-closed MPP settlement behind PaymentProvider."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from src.core.protocols import PaymentReceipt, PaymentRequest, Quote

from .mpp_data import (
    ApprovalGate,
    MPPPaymentResult,
    MPPQuotaStatus,
    MPPReplayError,
    MPPSettlementError,
    MPPTransport,
    PROVIDER_NAME,
    _REQUIRED_FIELDS,
)
from .mpp_engine import MPPExecutionEngine
from .mpp_helpers import validate_amount, validated_tx
from .mpp_shape import MPP_SCHEME, encode_mpp_quote


class MPPConfigError(ValueError):
    """Raised when explicit MPP settlement config is missing or invalid."""


class MPPSettlementProvider:
    """Fail-closed MPP settlement provider (PaymentProvider shape)."""

    def __init__(
        self,
        *,
        endpoint: Optional[str],
        asset: Optional[str],
        network: Optional[str],
        recipient: Optional[str],
        governance: Optional[ApprovalGate],
        transport: Optional[MPPTransport],
    ) -> None:
        config = dict(endpoint=endpoint, asset=asset, network=network, recipient=recipient)
        for name in _REQUIRED_FIELDS:
            value = config[name]
            if not isinstance(value, str) or not value.strip():
                raise MPPConfigError(f"missing required mpp config: {name} (never default-allow)")
        if governance is None or not callable(getattr(governance, "request_approval", None)):
            raise MPPConfigError("missing required mpp config: governance approval gate")
        if transport is None or not callable(transport):
            raise MPPConfigError("missing required mpp config: injected transport callable")
        self._endpoint = str(endpoint).strip()
        self._asset = str(asset).strip()
        self._network = str(network).strip()
        self._recipient = str(recipient).strip()
        self._governance = governance
        self._transport = transport
        self._receipts: Dict[str, PaymentReceipt] = {}
        self._refunded: Dict[str, bool] = {}
        self._usage: Dict[str, int] = {}
        self._engine = MPPExecutionEngine(
            self._endpoint, self._asset, self._network, self._recipient, self._governance, self._transport
        )

    def record_usage(self, agent: str, tokens: int, model: str) -> None:
        self._usage[agent] = self._usage.get(agent, 0) + max(0, int(tokens))

    def check_quota(self, org_id: str) -> MPPQuotaStatus:
        return MPPQuotaStatus(remaining_mcu=0, total_mcu=0, tier="MPP", reset_at="1970-01-01T00:00:00Z")

    def settle_payment(self, amount: float, currency: str, recipient: str) -> MPPPaymentResult:
        try:
            receipt = self._settle(
                PaymentRequest(
                    asset=self._asset,
                    network=self._network,
                    amount=amount,
                    recipient=recipient,
                    scheme=MPP_SCHEME,
                    provider=PROVIDER_NAME,
                    metadata={"idempotency_key": uuid.uuid4().hex, "currency": currency},
                ),
                action="settle_payment",
            )
            return MPPPaymentResult(
                success=True, transaction_id=receipt.transaction_id, note="mpp settlement confirmed by transport"
            )
        except ValueError as exc:
            return MPPPaymentResult(success=False, error=str(exc))

    def quote(self, amount: float, currency: str, recipient: str, scheme: str) -> Quote:
        validate_amount(amount)
        if scheme and scheme != MPP_SCHEME:
            raise ValueError(f"unsupported scheme: {scheme!r} (mpp uses {MPP_SCHEME!r})")
        self._engine.require_recipient(recipient)
        return Quote(
            asset=self._asset,
            network=self._network,
            amount=amount,
            recipient=self._recipient,
            scheme=MPP_SCHEME,
            provider=PROVIDER_NAME,
            metadata={
                "currency": currency,
                "payment_required": encode_mpp_quote(self._asset, self._network, amount, self._recipient),
            },
        )

    def request_payment(self, req: PaymentRequest) -> PaymentReceipt:
        validate_amount(req.amount)
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

    def refund(self, receipt: PaymentReceipt) -> MPPPaymentResult:
        if not self.verify(receipt):
            return MPPPaymentResult(
                success=False, transaction_id=receipt.transaction_id, error="refund rejected: receipt not verifiable"
            )
        try:
            self._engine.require_approval("refund", receipt.transaction_id)
        except MPPSettlementError as exc:
            return MPPPaymentResult(success=False, transaction_id=receipt.transaction_id, error=str(exc))
        self._refunded[receipt.transaction_id] = True
        return MPPPaymentResult(
            success=True, transaction_id=receipt.transaction_id, note="mpp refund recorded"
        )

    def usage(self, agent: str) -> int:
        return self._usage.get(agent, 0)

    def _settle(self, req: PaymentRequest, action: str) -> PaymentReceipt:
        return self._engine.execute_settle(req, action, self._receipts)

    _validate_amount = staticmethod(validate_amount)
    _validated_tx = staticmethod(validated_tx)


__all__ = [
    "MPPSettlementProvider",
    "MPPConfigError",
    "MPPPaymentResult",
    "MPPQuotaStatus",
    "MPPTransport",
    "PROVIDER_NAME",
    "MPPReplayError",
    "MPPSettlementError",
]

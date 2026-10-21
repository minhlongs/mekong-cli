# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Core fail-closed settlement execution engine for x402 protocol."""

from __future__ import annotations

import logging
from typing import Dict

from src.core.governance import ActionClass, GovernanceDecision
from src.core.protocols import PaymentReceipt, PaymentRequest

from .payment_x402_helpers import content_key, to_atomic, validated_tx
from .payment_x402_shape import (
    X402_SCHEME,
    X402_VERSION,
    X_PAYMENT_HEADER,
    PaymentRequired,
    XPaymentPayload,
    _reject_forbidden_fields,
    encode_payment_required,
    encode_x_payment_header,
)
from .payment_x402_types import (
    ApprovalGate,
    PROVIDER_NAME,
    X402ReplayError,
    X402SettlementError,
    X402Transport,
)

logger = logging.getLogger(__name__)


class X402ExecutionEngine:
    """Executes validated payment settlement hops through governance and transport."""

    def __init__(
        self,
        endpoint: str,
        asset: str,
        network: str,
        recipient: str,
        governance: ApprovalGate,
        transport: X402Transport,
    ) -> None:
        self.endpoint = endpoint
        self.asset = asset
        self.network = network
        self.recipient = recipient
        self.governance = governance
        self.transport = transport

    def execute_settle(
        self,
        req: PaymentRequest,
        action: str,
        receipts: Dict[str, PaymentReceipt],
    ) -> PaymentReceipt:
        """Run fail-closed settlement: validate -> approval -> transport -> receipt."""
        if req.asset != self.asset:
            raise ValueError(
                f"wrong asset: {req.asset!r} (provider accepts {self.asset!r})"
            )
        if req.network != self.network:
            raise ValueError(
                f"wrong network: {req.network!r} (provider accepts {self.network!r})"
            )
        if req.scheme != X402_SCHEME:
            raise ValueError(
                f"unsupported scheme: {req.scheme!r} (x402 uses {X402_SCHEME!r})"
            )
        self.require_recipient(req.recipient)
        _reject_forbidden_fields(dict(req.metadata))
        atomic = to_atomic(req.amount)

        key = str(req.metadata.get("idempotency_key") or "")
        if not key:
            key = content_key(req.asset, req.network, atomic, req.recipient)
        if key in receipts:
            raise X402ReplayError(
                "replayed idempotency key rejected: duplicate settlement attempt"
            )

        self.require_approval(action, f"{req.asset}:{req.network}:{atomic}")

        header = encode_x_payment_header(
            XPaymentPayload(
                x402_version=X402_VERSION,
                scheme=X402_SCHEME,
                asset=req.asset,
                network=req.network,
                amount=atomic,
                recipient=req.recipient,
                metadata={"idempotency_key": key},
            )
        )
        body = encode_payment_required(
            PaymentRequired(
                x402_version=X402_VERSION,
                accepts_asset=req.asset,
                accepts_network=req.network,
                amount=atomic,
                recipient=req.recipient,
            )
        )
        logger.info(
            "x402 %s: asset=%s network=%s atomic_amount=%s",
            action,
            req.asset,
            req.network,
            atomic,
        )
        try:
            response = self.transport(self.endpoint, {X_PAYMENT_HEADER: header}, body)
        except Exception as exc:
            raise X402SettlementError(
                f"transport failure: {action} aborted ({type(exc).__name__})"
            ) from exc
        tx_id = validated_tx(response)

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
        receipts[key] = receipt
        return receipt

    def require_approval(self, action: str, detail: str) -> None:
        """Route the action through governance; denial fails closed."""
        decision = GovernanceDecision(
            action_class=ActionClass.REVIEW_REQUIRED,
            reason=f"x402 {action} requires governance approval",
            requires_approval=True,
        )
        if not self.governance.request_approval(f"x402:{action}:{detail}", decision):
            raise X402SettlementError(
                f"governance approval denied for {action}: settlement blocked"
            )

    def require_recipient(self, recipient: str) -> None:
        """Fail-closed: only the explicitly configured recipient is payable."""
        if recipient != self.recipient:
            raise ValueError(
                "recipient mismatch: provider settles only to the configured recipient"
            )


__all__ = ["X402ExecutionEngine"]

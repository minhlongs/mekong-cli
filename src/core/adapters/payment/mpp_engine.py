# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Core fail-closed execution engine for MPP settlement."""

from __future__ import annotations

import logging
import uuid
from typing import Dict

from src.core.governance import ActionClass, GovernanceDecision
from src.core.protocols import PaymentReceipt, PaymentRequest

from .mpp_data import (
    ApprovalGate,
    MPPReplayError,
    MPPSettlementError,
    MPPTransport,
    PROVIDER_NAME,
)
from .mpp_helpers import validate_amount, validated_tx
from .mpp_shape import MPP_SCHEME, encode_mpp_quote, reject_forbidden_fields

logger = logging.getLogger(__name__)


class MPPExecutionEngine:
    """Executes validated MPP payment settlement hops through governance and transport."""

    def __init__(
        self,
        endpoint: str,
        asset: str,
        network: str,
        recipient: str,
        governance: ApprovalGate,
        transport: MPPTransport,
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
        """Shared fail-closed settlement core for settle/request paths."""
        validate_amount(req.amount)
        if req.asset != self.asset:
            raise ValueError(f"wrong asset: {req.asset!r} (provider accepts {self.asset!r})")
        if req.network != self.network:
            raise ValueError(f"wrong network: {req.network!r} (provider accepts {self.network!r})")
        if req.scheme != MPP_SCHEME:
            raise ValueError(f"unsupported scheme: {req.scheme!r} (mpp uses {MPP_SCHEME!r})")
        self.require_recipient(req.recipient)
        reject_forbidden_fields(dict(req.metadata))

        key = str(req.metadata.get("idempotency_key") or uuid.uuid4().hex)
        if key in receipts:
            raise MPPReplayError("replayed idempotency key rejected: duplicate settlement attempt")

        self.require_approval(action, f"{req.asset}:{req.network}:{req.amount}")

        body = encode_mpp_quote(req.asset, req.network, req.amount, req.recipient)
        logger.info("mpp %s: asset=%s network=%s amount=%s", action, req.asset, req.network, req.amount)
        try:
            response = self.transport(self.endpoint, {"X-MPP-PAYMENT": key}, body)
        except Exception as exc:
            raise MPPSettlementError(f"transport failure: {action} aborted ({type(exc).__name__})") from exc
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
            reason=f"mpp {action} requires governance approval",
            requires_approval=True,
        )
        if not self.governance.request_approval(f"mpp:{action}:{detail}", decision):
            raise MPPSettlementError(f"governance approval denied for {action}: settlement blocked")

    def require_recipient(self, recipient: str) -> None:
        """Fail-closed: only the explicitly configured recipient is payable."""
        if recipient != self.recipient:
            raise ValueError("recipient mismatch: provider settles only to the configured recipient")


__all__ = ["MPPExecutionEngine"]

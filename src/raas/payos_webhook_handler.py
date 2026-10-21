# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""PayOS VietQR HMAC-SHA256 webhook handler, anti-replay, MCU top-up & AuditLedger."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import hmac
from typing import Any

from src.core.mcu_billing import MCUBilling
from src.core.opencore.saas_immutable_audit_ledger import AuditLedger


@dataclass(frozen=True)
class PayOSWebhookPayload:
    """Incoming PayOS VietQR payment webhook payload."""

    code: str
    desc: str
    success: bool
    data: dict[str, Any]
    signature: str
    tenant_id: str


@dataclass(frozen=True)
class PayOSWebhookResult:
    """Deterministic processing result for a PayOS VietQR webhook."""

    accepted: bool
    order_code: int
    tenant_id: str
    mcu_credited: int
    balance_after: int
    ledger_hash: str
    reason: str


class PayOSWebhookHandler:
    """Verifies PayOS HMAC-SHA256 signatures, blocks replays, credits MCU, and appends to AuditLedger."""

    def __init__(
        self,
        checksum_key: str,
        mcu_billing: MCUBilling | None = None,
        audit_ledger: AuditLedger | None = None,
        vnd_per_mcu: int = 1000,
    ) -> None:
        if not checksum_key or not checksum_key.strip():
            raise ValueError("PayOS checksum_key must not be empty")
        if vnd_per_mcu <= 0:
            raise ValueError("vnd_per_mcu must be positive")
        self._checksum_key = checksum_key
        self._mcu_billing = mcu_billing or MCUBilling()
        self._audit_ledger = audit_ledger or AuditLedger()
        self._vnd_per_mcu = vnd_per_mcu
        self._processed_orders: set[tuple[int, str]] = set()

    @staticmethod
    def compute_payos_signature(data: Mapping[str, Any], checksum_key: str) -> str:
        """Compute canonical PayOS HMAC-SHA256 signature over alphabetically sorted keys."""
        parts: list[str] = []
        for key in sorted(data.keys()):
            val = data[key]
            normalized = "" if val is None else str(val)
            parts.append(f"{key}={normalized}")
        canonical = "&".join(parts)
        return hmac.new(
            checksum_key.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_signature(self, data: Mapping[str, Any], signature: str) -> bool:
        """Verify PayOS HMAC-SHA256 signature using constant-time comparison."""
        if not signature:
            return False
        expected = self.compute_payos_signature(data, self._checksum_key)
        return hmac.compare_digest(expected.lower(), signature.strip().lower())

    def process_webhook(self, payload: PayOSWebhookPayload) -> PayOSWebhookResult:
        """Validate PayOS webhook, prevent replay, credit MCUBilling, and log to AuditLedger."""
        raw_order = payload.data.get("orderCode", 0)
        try:
            order_code = int(raw_order)
        except (TypeError, ValueError):
            order_code = 0

        if not self.verify_signature(payload.data, payload.signature):
            return PayOSWebhookResult(
                accepted=False,
                order_code=order_code,
                tenant_id=payload.tenant_id,
                mcu_credited=0,
                balance_after=self._mcu_billing.get_balance(payload.tenant_id),
                ledger_hash="",
                reason="INVALID_PAYOS_SIGNATURE",
            )

        if payload.code != "00" or not payload.success or order_code <= 0:
            return PayOSWebhookResult(
                accepted=False,
                order_code=order_code,
                tenant_id=payload.tenant_id,
                mcu_credited=0,
                balance_after=self._mcu_billing.get_balance(payload.tenant_id),
                ledger_hash="",
                reason="PAYMENT_NOT_SUCCESSFUL",
            )

        reference = str(payload.data.get("reference") or payload.data.get("paymentLinkId") or "")
        dedup_key = (order_code, reference)
        if dedup_key in self._processed_orders or any(
            existing_order == order_code for existing_order, _ in self._processed_orders
        ):
            return PayOSWebhookResult(
                accepted=False,
                order_code=order_code,
                tenant_id=payload.tenant_id,
                mcu_credited=0,
                balance_after=self._mcu_billing.get_balance(payload.tenant_id),
                ledger_hash="",
                reason="REPLAY_ORDER_DETECTED",
            )

        raw_amount = int(payload.data.get("amount", 0))
        if raw_amount <= 0:
            return PayOSWebhookResult(
                accepted=False,
                order_code=order_code,
                tenant_id=payload.tenant_id,
                mcu_credited=0,
                balance_after=self._mcu_billing.get_balance(payload.tenant_id),
                ledger_hash="",
                reason="INVALID_PAYMENT_AMOUNT",
            )

        self._processed_orders.add(dedup_key)
        mcu_credited = max(1, raw_amount // self._vnd_per_mcu)
        tenant_balance = self._mcu_billing.add_credits(
            payload.tenant_id,
            mcu_credited,
            description=f"PayOS order #{order_code}",
        )
        entry = self._audit_ledger.append_event(
            event_type="PAYOS_MCU_TOPUP",
            actor="payos_webhook",
            payload={
                "tenant_id": payload.tenant_id,
                "order_code": order_code,
                "amount_vnd": raw_amount,
                "mcu_credited": mcu_credited,
                "balance_after": tenant_balance.balance,
                "reference": reference,
            },
        )
        return PayOSWebhookResult(
            accepted=True,
            order_code=order_code,
            tenant_id=payload.tenant_id,
            mcu_credited=mcu_credited,
            balance_after=tenant_balance.balance,
            ledger_hash=entry.hash,
            reason="CREDITED",
        )


__all__ = [
    "PayOSWebhookHandler",
    "PayOSWebhookPayload",
    "PayOSWebhookResult",
]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dataclasses, constants, and hash utilities for MockPaymentProvider."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

from src.core.protocols import PaymentReceipt, PaymentRequest


@dataclass(frozen=True)
class MockQuotaStatus:
    """Concrete QuotaStatus-shaped carrier (satisfies the Protocol structurally)."""

    remaining_mcu: int
    total_mcu: int
    tier: str
    reset_at: str


@dataclass(frozen=True)
class MockPaymentResult:
    """Concrete PaymentResult-shaped carrier (satisfies the Protocol structurally)."""

    success: bool
    transaction_id: Optional[str] = None
    pending: bool = False
    note: Optional[str] = None
    error: Optional[str] = None


PROVIDER_NAME = "mock"
DEFAULT_ASSET = "USDC"
DEFAULT_NETWORK = "base"
DEFAULT_SCHEME = "exact"


def validate_amount(amount: float) -> None:
    """Validate payment amount format and bounds."""
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError(f"invalid amount: {amount!r} (must be numeric)")
    if amount <= 0:
        raise ValueError(f"invalid amount: {amount!r} (must be > 0)")


def idempotency_key_from_request(req: PaymentRequest) -> str:
    """Extract or deterministically derive idempotency key from PaymentRequest."""
    key = req.metadata.get("idempotency_key")
    if key:
        return str(key)
    payload = f"{req.asset}|{req.network}|{req.amount}|{req.recipient}|{req.scheme}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def idempotency_key_from_receipt(receipt: PaymentReceipt) -> str:
    """Extract or deterministically derive idempotency key from PaymentReceipt."""
    key = receipt.metadata.get("idempotency_key")
    if key:
        return str(key)
    payload = (
        f"{receipt.asset}|{receipt.network}|{receipt.amount}|"
        f"{receipt.recipient}|{receipt.scheme}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def deterministic_tx_id(
    asset: str,
    network: str,
    amount: float,
    recipient: str,
    scheme: str,
    key: str,
) -> str:
    """Derive deterministic transaction identifier hash."""
    payload = f"{asset}|{network}|{amount}|{recipient}|{scheme}|{key}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"mock-tx-{digest[:16]}"


__all__ = [
    "MockQuotaStatus",
    "MockPaymentResult",
    "PROVIDER_NAME",
    "DEFAULT_ASSET",
    "DEFAULT_NETWORK",
    "DEFAULT_SCHEME",
    "validate_amount",
    "idempotency_key_from_request",
    "idempotency_key_from_receipt",
    "deterministic_tx_id",
]

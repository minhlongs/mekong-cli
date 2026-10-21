# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Validation and atomic conversion helpers for x402 settlement."""

from __future__ import annotations

import hashlib
from typing import Any

from .payment_x402_types import ATOMIC_DECIMALS, X402SettlementError


def to_atomic(amount: float) -> str:
    """Convert a positive numeric amount to an atomic-unit integer string."""
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError(f"invalid amount: {amount!r} (must be numeric)")
    if amount <= 0:
        raise ValueError(f"invalid amount: {amount!r} (must be > 0)")
    atomic = int(round(amount * 10**ATOMIC_DECIMALS))
    if atomic <= 0:
        raise ValueError(f"invalid amount: {amount!r} (rounds to zero atomic units)")
    return str(atomic)


def content_key(asset: str, network: str, atomic: str, recipient: str) -> str:
    """Generate SHA256 content key for idempotent settlement deduplication."""
    payload = f"{asset}|{network}|{atomic}|{recipient}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def validated_tx(response: Any) -> str:
    """Accept only an explicit confirmed response carrying a transaction id."""
    if not isinstance(response, dict) or response.get("success") is not True:
        raise X402SettlementError(
            "transport response rejected: no confirmed settlement"
        )
    tx_id = response.get("transaction_id")
    if not isinstance(tx_id, str) or not tx_id.strip():
        raise X402SettlementError("transport response missing transaction_id")
    return tx_id


__all__ = ["to_atomic", "content_key", "validated_tx"]

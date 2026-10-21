# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Validation and transaction helpers for MPP settlement."""

from __future__ import annotations

from typing import Any

from .mpp_data import MPPSettlementError


def validated_tx(response: Any) -> str:
    """Accept only an explicit confirmed response carrying a transaction id."""
    if not isinstance(response, dict) or response.get("success") is not True:
        raise MPPSettlementError("transport response rejected: no confirmed settlement")
    tx_id = response.get("transaction_id")
    if not isinstance(tx_id, str) or not tx_id.strip():
        raise MPPSettlementError("transport response missing transaction_id")
    return tx_id


def validate_amount(amount: Any) -> None:
    """Reject non-numeric, boolean, or non-positive amounts."""
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError(f"invalid amount: {amount!r} (must be numeric)")
    if amount <= 0:
        raise ValueError(f"invalid amount: {amount!r} (must be > 0)")


__all__ = ["validated_tx", "validate_amount"]

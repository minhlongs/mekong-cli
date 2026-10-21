# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pydantic models and helpers for VN Pilot Billing."""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Request
from pydantic import BaseModel, Field

_USER_ID_RE = re.compile(r"^opc_[a-z0-9_]{2,50}$")

_VND_TIERS: dict[str, int] = {
    "starter_vnd": 199_000,
    "growth_vnd": 299_000,
    "pro_vnd": 499_000,
}


def _facade() -> Any:
    """Return the parent vn_pilot_billing module if loaded."""
    return sys.modules.get("src.api.vn_pilot_billing")


def _resolve_user_id(request: Request) -> Optional[str]:
    """Resolve user_id from env var (preferred) or X-User-ID header."""
    env_id = os.environ.get("MEKONG_USER_ID")
    if env_id:
        return env_id.lower() if env_id else env_id
    header_id = request.headers.get("x-user-id")
    if header_id:
        return header_id.lower()
    return None


class CreditStatusResponse(BaseModel):
    """Credit + subscription status for paywall decisions."""

    user_id: str
    status: str = Field(description="active | overdue | expired | cancelled | none")
    credits: int
    tier: Optional[str] = None
    monthly_vnd: Optional[int] = None
    next_due_at: Optional[str] = None
    renewal_count: int = 0
    suggested_tier: str = Field(default="starter_vnd")
    suggested_price_vnd: int = Field(default=199_000)


class RenewResponse(BaseModel):
    """Result of a manual renewal topup."""

    user_id: str
    status: str
    credits: int
    message: str


class VietQRQRRequest(BaseModel):
    """Request body for VietQR QR data generation."""

    bank_bin: str = Field(min_length=2, max_length=8, description="Bank BIN code (e.g. 970422)")
    account_number: str = Field(min_length=6, max_length=20, description="Bank account number")
    account_name: str = Field(default="", max_length=100, description="Account holder name")
    amount_vnd: int = Field(ge=0, le=999_000_000, description="Transfer amount in VND")
    memo: str = Field(default="", max_length=50, description="Transfer content/memo")
    city: str = Field(default="Ho Chi Minh", max_length=50)


class VietQRQRResponse(BaseModel):
    """VietQR QR data payload for client-side rendering."""

    qr_data: str
    bank_bin: str
    account_number: str
    account_name: str
    amount_vnd: int
    memo: str
    bank: str
    city: str


class PaymentInstructionsResponse(BaseModel):
    """Vietnamese payment instructions for VietQR / bank transfer."""

    user_id: str
    tier: str
    amount_vnd: int
    bank_tx_ref: str
    instructions_vn: str
    instructions_en: str
    bank: str
    account: str
    account_number: str
    status: str = "payment_required"
    renew_url: str = "/v1/pilot/credit-status"


class ExpiringClient(BaseModel):
    """A pilot user whose subscription expires within N days."""

    user_id: str
    tier: str
    monthly_vnd: int
    credits: int
    next_due_at: str
    days_until_due: int
    status: str


class ExpiringClientsResponse(BaseModel):
    """List of clients with upcoming expiry."""

    clients: list[ExpiringClient]
    scanned: int
    warning_days: int


def _days_diff(start: str, end: str) -> int:
    """Days between two ISO dates (positive = end is after start)."""
    try:
        d1 = datetime.fromisoformat(start).date()
        d2 = datetime.fromisoformat(end).date()
        return (d2 - d1).days
    except (ValueError, TypeError):
        return 0


def _user_status_label(sub: dict, today_str: str) -> str:
    """Human-readable status for expiring-clients view."""
    next_due = sub.get("next_due_at", "")
    credits = sub.get("credits", 0)
    if credits <= 0:
        return "no_credits"
    if next_due < today_str:
        return "overdue"
    if next_due <= (datetime.now(timezone.utc).date() + timedelta(days=3)).isoformat():
        return "expiring_soon"
    return "active"


__all__ = [
    "CreditStatusResponse",
    "ExpiringClient",
    "ExpiringClientsResponse",
    "PaymentInstructionsResponse",
    "RenewResponse",
    "VietQRQRRequest",
    "VietQRQRResponse",
    "_USER_ID_RE",
    "_VND_TIERS",
    "_days_diff",
    "_facade",
    "_resolve_user_id",
    "_user_status_label",
]

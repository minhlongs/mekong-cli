# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

# DEPRECATED: retained for backward compatibility with vn_pilot_routes.py
# and pilot_credit_gate.py. New code must use src.api.billing_routes.py.
# See Phase 9 billing consolidation.

"""VN Pilot Billing — subscription + credit status for pilot users.

Endpoints:
- GET /v1/pilot/credit-status → current subscription + credit balance
  (user-scoped via MEKONG_USER_ID env or X-User-ID header).
- POST /v1/pilot/renew → trigger manual credit topup after external
  payment confirmation (e.g., user paid via bank transfer directly).

Storage: delegated to `src.services.vietqr_recurring` (JSONL subscriptions)
+ `vn_pilot_common` (credit JSONL).
"""
from __future__ import annotations

import hmac
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.services.vietqr_generator import build_qr_payload
from src.services.vietqr_recurring import (
    get_credit_status,
    get_subscription,
    renew_subscription,
)

_USER_ID_RE = re.compile(r"^opc_[a-z0-9_]{2,50}$")

billing_router = APIRouter()

logger = logging.getLogger(__name__)


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


@billing_router.get("/credit-status", response_model=CreditStatusResponse)
async def credit_status(request: Request) -> CreditStatusResponse:
    """Return current credit balance + subscription info for paywall decisions.

    Resolves user from MEKONG_USER_ID env or X-User-ID header.
    Returns 404 if user has never been onboarded.
    """
    user_id = _resolve_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MEKONG_USER_ID env var or X-User-ID header required",
        )

    sub = get_subscription(user_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for user",
        )

    credit_data = get_credit_status(user_id)
    logger.info(
        '{"event": "credit_status_check", "user_id": "%s", "credits": %d, "status": "%s"}',
        user_id,
        credit_data.get("credits", 0),
        credit_data.get("status", "unknown"),
    )
    return CreditStatusResponse(**credit_data)


@billing_router.post("/renew", response_model=RenewResponse)
async def manual_renew(request: Request, bank_tx_ref: str = "") -> RenewResponse:
    """Manually topup credits after external payment confirmation.

    Idempotent: same bank_tx_ref → skip. Used when founder confirms
    a bank transfer that the webhook missed (e.g., memo format issue).
    """
    user_id = _resolve_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MEKONG_USER_ID env var or X-User-ID header required",
        )

    sub = get_subscription(user_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found — user must convert first",
        )

    paid_at = datetime.now(timezone.utc).date().isoformat()
    tx_ref = bank_tx_ref or f"manual-{paid_at}"

    try:
        updated = renew_subscription(
            user_id=user_id,
            bank_tx_ref=tx_ref,
            paid_at=paid_at,
        )
        credits = updated.get("credits", 0)
        logger.info(
            '{"event": "manual_renew", "user_id": "%s", "credits": %d, "tx_ref": "%s"}',
            user_id,
            credits,
            tx_ref,
        )
        return RenewResponse(
            user_id=user_id,
            status="renewed",
            credits=credits,
            message=f"Credits topped up to {credits}",
        )
    except ValueError as exc:
        logger.warning(
            '{"event": "manual_renew_failed", "user_id": "%s", "error": "%s"}',
            user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ---- Payment Instructions ----

_VND_TIERS: dict[str, int] = {
    "starter_vnd": 199_000,
    "growth_vnd": 299_000,
    "pro_vnd": 499_000,
}

def _bank_info() -> dict[str, str]:
    """Resolve bank account info from env vars (with hardcoded fallback).

    Env vars:
        MEKONG_BANK_NAME, MEKONG_BANK_ACCOUNT, MEKONG_BANK_ACCOUNT_NUMBER

    Fallback values preserve existing behavior if env vars are unset.
    """
    return {
        "bank": os.environ.get("MEKONG_BANK_NAME", "Techcombank"),
        "account": os.environ.get("MEKONG_BANK_ACCOUNT", "SET_MEKONG_BANK_ACCOUNT"),
        "account_number": os.environ.get("MEKONG_BANK_ACCOUNT_NUMBER", "SET_MEKONG_BANK_ACCOUNT_NUMBER"),
    }


def _payment_instructions_data(user_id: str, tier: str = "starter_vnd") -> dict:
    """Build payment instructions payload."""
    if not _USER_ID_RE.match(user_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user_id format: {user_id!r}",
        )
    amount_vnd = _VND_TIERS.get(tier, 199_000)
    formatted = f"{amount_vnd:,}"
    tx_ref = f"MEKONG-{user_id}"
    instructions_vn = (
        f"Để tiếp tục sử dụng MekongMind, vui lòng thanh toán hóa đơn tháng:\n\n"
        f"💰 Số tiền: {formatted} VND\n"
        f"📋 Nội dung CK: {tx_ref}\n"
        f"🏦 Ngân hàng: {_bank_info()['bank']} — {_bank_info()['account']} ({_bank_info()['account_number']})\n\n"
        f"Sau khi chuyển khoản, hệ thống tự động cộng credit trong 1-5 phút. "
        f"Cần hỗ trợ: Zalo 0977.048.051."
    )
    instructions_en = (
        f"To continue using MekongMind, pay your monthly invoice:\n\n"
        f"💰 Amount: {formatted} VND\n"
        f"📋 Transfer content: {tx_ref}\n"
        f"🏦 Bank: {_bank_info()['bank']} — {_bank_info()['account']} ({_bank_info()['account_number']})\n\n"
        f"Credits auto-activate 1-5 min after transfer. Help: +84 977 048 051."
    )
    return {
        "user_id": user_id,
        "tier": tier,
        "amount_vnd": amount_vnd,
        "bank_tx_ref": tx_ref,
        "instructions_vn": instructions_vn,
        "instructions_en": instructions_en,
        **_bank_info(),
        "status": "payment_required",
    }



@billing_router.post(
    "/payment-qr",
    response_model=VietQRQRResponse,
    summary="Generate VietQR QR data string (no external deps)",
)
async def generate_payment_qr(req: VietQRQRRequest) -> VietQRQRResponse:
    """Return VietQR EMV-compatible QR data for bank transfer.

    Client-side JS renders this into a scannable QR code.
    Zero external API calls — pure string computation.
    """
    bank_map = {
        "970422": "Techcombank",
        "970436": "Vietcombank",
        "970405": "MB Bank",
        "970443": "VPBank",
        "970488": "MSB",
        "970403": "Agribank",
    }
    bank_name = bank_map.get(req.bank_bin, "Bank")
    qr_data = build_qr_payload(
        bin_code=req.bank_bin,
        account=req.account_number,
        account_name=req.account_name or "MEKONG User",
        amount_vnd=req.amount_vnd,
        memo=req.memo,
        city=req.city,
    )
    return VietQRQRResponse(
        qr_data=qr_data,
        bank_bin=req.bank_bin,
        account_number=req.account_number,
        account_name=req.account_name,
        amount_vnd=req.amount_vnd,
        memo=req.memo,
        bank=bank_name,
        city=req.city,
    )

@billing_router.get(
    "/payment-instructions",
    response_model=PaymentInstructionsResponse,
    summary="Get VietQR payment instructions for a user",
)
async def get_payment_instructions(
    request: Request,
    tier: str = "starter_vnd",
) -> PaymentInstructionsResponse:
    """Return Vietnamese bank transfer instructions for renewing a subscription.

    Resolves user from MEKONG_USER_ID env or X-User-ID header.
    If the user has an existing subscription, uses their current tier.
    Falls back to the `tier` query param (default starter_vnd).
    """
    user_id = _resolve_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MEKONG_USER_ID env var or X-User-ID header required",
        )

    # Use existing tier if available
    sub = get_subscription(user_id)
    effective_tier = sub.get("tier", tier) if sub else tier

    data = _payment_instructions_data(user_id, effective_tier)
    data["renew_url"] = "/v1/pilot/credit-status"

    logger.info(
        '{"event": "payment_instructions_served", "user_id": "%s", "tier": "%s"}',
        user_id,
        effective_tier,
    )
    return PaymentInstructionsResponse(**data)


# ---- Admin: Expiring clients ----

@billing_router.get(
    "/expiring-clients",
    response_model=ExpiringClientsResponse,
    summary="List pilot users whose subscription expires soon (admin)",
)
async def get_expiring_clients(
    request: Request,
    days: int = 7,
) -> ExpiringClientsResponse:
    """Return pilot users whose subscription expires within `days` days.

    Used by founder for proactive Zalo outreach before churn.
    Requires MEKONG_ADMIN_TOKEN env var + matching per-request token.
    """
    admin_token = os.environ.get("MEKONG_ADMIN_TOKEN", "")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoint — MEKONG_ADMIN_TOKEN not configured",
        )
    # Per-request auth: require matching token in header or query param.
    # Prevents URL-discovery enumeration of all pilot accounts.
    req_token = (
        request.headers.get("x-admin-token", "")
        or request.query_params.get("admin_token", "")
    )
    if not req_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin endpoint — x-admin-token header or admin_token query param required",
        )
    if not hmac.compare_digest(req_token, admin_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )

    from src.services.vietqr_recurring import _load_subs, _refresh_subscription_status

    all_subs = _load_subs()
    today = datetime.now(timezone.utc).date()
    cutoff = (today + timedelta(days=days)).isoformat()
    today_str = today.isoformat()

    seen: set[str] = set()
    expiring: list[ExpiringClient] = []

    for sub in all_subs:
        if sub.get("status") == "cancelled":
            continue
        uid = sub.get("user_id", "")
        if uid in seen:
            continue
        seen.add(uid)

        _refresh_subscription_status(sub)
        effective = sub.get("_effective_status", sub.get("status", "active"))
        next_due = sub.get("next_due_at", "")

        if not next_due or effective != "active":
            continue

        # Expiring: due within N days (not already overdue)
        if next_due <= cutoff and next_due >= today_str:
            d_until = _days_diff(today_str, next_due)
            expiring.append(
                ExpiringClient(
                    user_id=uid,
                    tier=sub.get("tier", "starter_vnd"),
                    monthly_vnd=sub.get("monthly_vnd", 199_000),
                    credits=sub.get("credits", 0),
                    next_due_at=next_due,
                    days_until_due=d_until,
                    status=_user_status_label(sub, today_str),
                )
            )

    expiring.sort(key=lambda c: c.days_until_due)

    logger.info(
        '{"event": "expiring_clients_query", "days": %d, "found": %d, "scanned": %d}',
        days,
        len(expiring),
        len(seen),
    )
    return ExpiringClientsResponse(
        clients=expiring,
        scanned=len(seen),
        warning_days=days,
    )

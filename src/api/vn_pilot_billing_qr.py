# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VietQR QR generation and bank transfer payment instructions for VN Pilot Billing."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Request, status

from src.api.vn_pilot_billing_models import (
    PaymentInstructionsResponse,
    VietQRQRRequest,
    VietQRQRResponse,
    _USER_ID_RE,
    _VND_TIERS,
    _facade,
    _resolve_user_id,
)
from src.services.vietqr_generator import build_qr_payload
from src.services.vietqr_recurring import get_subscription

logger = logging.getLogger(__name__)
qr_router = APIRouter()


def _bank_info() -> dict[str, str]:
    """Resolve bank account info from env vars (with hardcoded fallback)."""
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
    facade = _facade()
    bank_fn = getattr(facade, "_bank_info", _bank_info) if facade else _bank_info
    info = bank_fn()
    amount_vnd = _VND_TIERS.get(tier, 199_000)
    formatted = f"{amount_vnd:,}"
    tx_ref = f"MEKONG-{user_id}"
    instructions_vn = (
        f"Để tiếp tục sử dụng MekongMind, vui lòng thanh toán hóa đơn tháng:\n\n"
        f"💰 Số tiền: {formatted} VND\n"
        f"📋 Nội dung CK: {tx_ref}\n"
        f"🏦 Ngân hàng: {info['bank']} — {info['account']} ({info['account_number']})\n\n"
        f"Sau khi chuyển khoản, hệ thống tự động cộng credit trong 1-5 phút. "
        f"Cần hỗ trợ: Zalo 0977.048.051."
    )
    instructions_en = (
        f"To continue using MekongMind, pay your monthly invoice:\n\n"
        f"💰 Amount: {formatted} VND\n"
        f"📋 Transfer content: {tx_ref}\n"
        f"🏦 Bank: {info['bank']} — {info['account']} ({info['account_number']})\n\n"
        f"Credits auto-activate 1-5 min after transfer. Help: +84 977 048 051."
    )
    return {
        "user_id": user_id,
        "tier": tier,
        "amount_vnd": amount_vnd,
        "bank_tx_ref": tx_ref,
        "instructions_vn": instructions_vn,
        "instructions_en": instructions_en,
        **info,
        "status": "payment_required",
    }


@qr_router.post(
    "/payment-qr",
    response_model=VietQRQRResponse,
    summary="Generate VietQR QR data string (no external deps)",
)
async def generate_payment_qr(req: VietQRQRRequest) -> VietQRQRResponse:
    """Return VietQR EMV-compatible QR data for bank transfer."""
    bank_map = {
        "970422": "Techcombank",
        "970436": "Vietcombank",
        "970405": "MB Bank",
        "970443": "VPBank",
        "970488": "MSB",
        "970403": "Agribank",
    }
    facade = _facade()
    build_fn = getattr(facade, "build_qr_payload", build_qr_payload) if facade else build_qr_payload
    bank_name = bank_map.get(req.bank_bin, "Bank")
    qr_data = build_fn(
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


@qr_router.get(
    "/payment-instructions",
    response_model=PaymentInstructionsResponse,
    summary="Get VietQR payment instructions for a user",
)
async def get_payment_instructions(
    request: Request,
    tier: str = "starter_vnd",
) -> PaymentInstructionsResponse:
    """Return Vietnamese bank transfer instructions for renewing a subscription."""
    facade = _facade()
    resolve_fn = getattr(facade, "_resolve_user_id", _resolve_user_id) if facade else _resolve_user_id
    get_sub_fn = getattr(facade, "get_subscription", get_subscription) if facade else get_subscription
    data_fn = getattr(facade, "_payment_instructions_data", _payment_instructions_data) if facade else _payment_instructions_data

    user_id = resolve_fn(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MEKONG_USER_ID env var or X-User-ID header required",
        )

    sub = get_sub_fn(user_id)
    effective_tier = sub.get("tier", tier) if sub else tier

    data = data_fn(user_id, effective_tier)
    data["renew_url"] = "/v1/pilot/credit-status"

    logger.info(
        '{"event": "payment_instructions_served", "user_id": "%s", "tier": "%s"}',
        user_id,
        effective_tier,
    )
    return PaymentInstructionsResponse(**data)

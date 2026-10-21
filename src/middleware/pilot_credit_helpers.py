# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pilot credit gate helpers — config, payment instructions, and 402 response builder."""
from __future__ import annotations

import logging
import os
from datetime import datetime

from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Override these via env or direct setattr
_cfg = {
    "enabled": os.environ.get("MEKONG_PILOT_GATE", "0") == "1",
    "warning_days": int(os.environ.get("MEKONG_PILOT_WARNING_DAYS", "7")),
    "grace_days": int(os.environ.get("MEKONG_PILOT_GRACE_DAYS", "3")),
}

_WARN_THRESHOLD_PCT = 20  # warn when credits < 20% of tier default


def is_enabled() -> bool:
    return _cfg["enabled"]


def configure(enabled: bool = True, warning_days: int = 7, grace_days: int = 3) -> None:
    _cfg["enabled"] = enabled
    _cfg["warning_days"] = warning_days
    _cfg["grace_days"] = grace_days


_STARTER_DEFAULT = 300
_VND_TIERS: dict[str, int] = {
    "starter_vnd": 199_000,
    "growth_vnd": 299_000,
    "pro_vnd": 499_000,
}

_payment_text_vn = (
    "Để tiếp tục sử dụng MekongMind, vui lòng thanh toán hóa đơn tháng:\n\n"
    "💰 Số tiền: {amount} VND\n"
    "📋 Nội dung CK: MEKONG-{user_id}\n"
    "🏦 Ngân hàng: {bank} — {account}\n\n"
    "Sau khi chuyển khoản, hệ thống sẽ tự động cộng credit trong 1-5 phút. "
    "Nếu cần hỗ trợ, nhắn Zalo 0977.048.051."
)

_payment_text_en = (
    "To continue using MekongMind, please pay your monthly invoice:\n\n"
    "💰 Amount: {amount} VND\n"
    "📋 Transfer content: MEKONG-{user_id}\n"
    "🏦 Bank: {bank} — {account}\n\n"
    "Credits auto-activate 1-5 minutes after transfer. "
    "Need help? Zalo: +84 977 048 051."
)

_default_bank = {
    "bank": os.environ.get("MEKONG_BANK_NAME", "Techcombank"),
    "account": os.environ.get("MEKONG_BANK_ACCOUNT", "SET_MEKONG_BANK_ACCOUNT"),
}


def _payment_instructions(user_id: str, tier: str = "starter_vnd") -> dict:
    """Return Vietnamese + English payment instructions for a user."""
    amount_vnd = _VND_TIERS.get(tier, 199_000)
    formatted = f"{amount_vnd:,}"
    instructions_vn = _payment_text_vn.format(
        amount=formatted,
        user_id=user_id,
        **_default_bank,
    )
    instructions_en = _payment_text_en.format(
        amount=formatted,
        user_id=user_id,
        **_default_bank,
    )
    return {
        "user_id": user_id,
        "tier": tier,
        "amount_vnd": amount_vnd,
        "bank_tx_ref": f"MEKONG-{user_id}",
        "instructions_vn": instructions_vn,
        "instructions_en": instructions_en,
        "bank": _default_bank["bank"],
        "account": _default_bank["account"],
        "status": "payment_required",
    }


def _credit_block_response(user_id: str, tier: str, reason: str) -> JSONResponse:
    """Build a 402 JSON response with VietQR payment instructions."""
    data = _payment_instructions(user_id, tier)
    data["reason"] = reason
    logger.info(
        '{"event": "pilot_credit_blocked", "user_id": "%s", "reason": "%s", "tier": "%s"}',
        user_id,
        reason,
        tier,
    )
    return JSONResponse(
        status_code=402,
        content={
            "error": "subscription_payment_required",
            "detail": data,
            "renew_url": "/v1/pilot/credit-status",
            "payment_url": f"/v1/pilot/payment-instructions?tier={tier}",
        },
    )


def _days_diff(start: str, end: str) -> int:
    """Days between two ISO dates (positive = end is after start)."""
    try:
        d1 = datetime.fromisoformat(start).date()
        d2 = datetime.fromisoformat(end).date()
        return (d2 - d1).days
    except (ValueError, TypeError):
        return 0

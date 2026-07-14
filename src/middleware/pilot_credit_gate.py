"""Pilot credit gate middleware — soft paywall for VN pilot users.

Blocks expired/overdue pilot users from credit-consuming routes with
HTTP 402 + Vietnamese payment instructions. Lets them through on
public endpoints so they can always pay their bill.

Activation: MEKONG_PILOT_GATE=1

Usage in gateway:
    app.add_middleware(PilotCreditGateMiddleware)

Pattern: rate_limit_gateway_middleware (BaseHTTPMiddleware + path exclusions).
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Override these via env or direct setattr
_cfg = {
    "enabled": os.environ.get("MEKONG_PILOT_GATE", "0") == "1",
    # days before next_due_at to flag as "expiring soon"
    "warning_days": int(os.environ.get("MEKONG_PILOT_WARNING_DAYS", "7")),
    # days after due date before blocking commands
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
    "bank": "Techcombank",
    "account": "Nguyễn Văn Minh (0977048051)",
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
        user_id, reason, tier,
    )
    return JSONResponse(
        status_code=402,
        content={
            "error": "subscription_payment_required",
            "detail": data,
            "renew_url": f"/v1/pilot/credit-status",
            "payment_url": f"/v1/pilot/payment-instructions?tier={tier}",
        },
    )


def check_pilot_credit(request: Request) -> Optional[JSONResponse]:
    """Check if the requesting pilot user has valid subscription credits.

    Returns None if allowed, or a JSONResponse(402) if blocked.
    Only activates when MEKONG_PILOT_GATE=1 env var is set.
    Reads user_id from X-User-ID header or MEKONG_USER_ID env.
    """
    if not is_enabled():
        return None

    # Resolve user_id
    user_id: Optional[str] = None
    user_header = request.headers.get("x-user-id")
    if user_header:
        user_id = user_header.lower()
    if not user_id:
        user_id = os.environ.get("MEKONG_USER_ID", "").lower()
    if not user_id:
        return None # anonymous — no block

    try:
        from src.api.vn_pilot_billing import get_subscription, get_credit_status

        sub = get_subscription(user_id)
        if not sub:
            # No subscription at all — let through (will hit 404 on protected routes)
            return None

        status = sub.get("_effective_status") or sub.get("status", "active")
        today = datetime.now(timezone.utc).date().isoformat()
        credits = sub.get("credits", 0)
        tier = sub.get("tier", "starter_vnd")
        next_due = sub.get("next_due_at", "")

        # Expired / cancelled → block
        if status in ("expired", "cancelled"):
            return _credit_block_response(user_id, tier, f"subscription_{status}")

        # Overdue beyond grace period → block
        if next_due and status == "overdue":
            overdue_days = _days_diff(next_due, today)
            if overdue_days > _cfg["grace_days"]:
                return _credit_block_response(
                    user_id, tier, f"overdue_{overdue_days}d"
                )

        # Zero credits on active sub → warn (no block yet — block only at 402 via credit-status)
        if credits <= 0:
            logger.info(
                '{"event": "pilot_zero_credits", "user_id": "%s", "tier": "%s"}',
                user_id, tier,
            )

        return None

    except Exception as exc:
        # Fail open — don't block users on internal errors
        logger.warning("pilot_credit_gate error: %s", exc)
        return None


def _days_diff(start: str, end: str) -> int:
    """Days between two ISO dates (positive = end is after start)."""
    try:
        d1 = datetime.fromisoformat(start).date()
        d2 = datetime.fromisoformat(end).date()
        return (d2 - d1).days
    except (ValueError, TypeError):
        return 0


# =============================================================================
# FASTAPI MIDDLEWARE (gateway integration)
# =============================================================================

_SKIP_PATHS = frozenset({
    "/health",
    "/healthz",
    "/metrics",
    "/v1/pilot/payment-instructions",
    "/v1/pilot/credit-status",
    "/v1/pilot/expiring-clients",
    "/v1/pilot/signup",
    "/v1/pilot/health",
    "/v1/pilot/stats",
    "/v1/pilot/recent",
})


class PilotCreditGateMiddleware(BaseHTTPMiddleware):
    """Global middleware: blocks expired/overdue pilot users from credit-consuming routes.

    Skips payment/health endpoints so expired users can always see how to pay.
    Only activates when MEKONG_PILOT_GATE=1.

    Pattern: rate_limit_gateway_middleware (BaseHTTPMiddleware + path exclusions).
    """

    async def dispatch(self, request: Request, call_next):
        if not is_enabled():
            return await call_next(request)

        path = request.url.path
        if path in _SKIP_PATHS or path.startswith("/v1/pilot/signup"):
            return await call_next(request)

        response = check_pilot_credit(request)
        if response is not None:
            return response

        return await call_next(request)

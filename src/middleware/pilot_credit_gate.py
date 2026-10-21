# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pilot credit gate middleware — soft paywall for VN pilot users.

Blocks expired/overdue pilot users from credit-consuming routes with
HTTP 402 + Vietnamese payment instructions. Lets them through on
public endpoints so they can always pay their bill.

Activation: MEKONG_PILOT_GATE=1
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.middleware.pilot_credit_helpers import (
    _STARTER_DEFAULT,
    _VND_TIERS,
    _WARN_THRESHOLD_PCT,
    _cfg,
    _credit_block_response,
    _days_diff,
    _default_bank,
    _payment_instructions,
    _payment_text_en,
    _payment_text_vn,
    configure,
    is_enabled,
)

logger = logging.getLogger(__name__)


def check_pilot_credit(request: Request) -> Optional[JSONResponse]:
    """Check if the requesting pilot user has valid subscription credits.

    Returns None if allowed, or a JSONResponse(402) if blocked.
    Only activates when MEKONG_PILOT_GATE=1 env var is set.
    Reads user_id from X-User-ID header or MEKONG_USER_ID env.
    """
    if not is_enabled():
        return None

    user_id: Optional[str] = None
    user_header = request.headers.get("x-user-id")
    if user_header:
        user_id = user_header.lower()
    if not user_id:
        user_id = os.environ.get("MEKONG_USER_ID", "").lower()
    if not user_id:
        return None

    try:
        from src.api.vn_pilot_billing import get_subscription

        sub = get_subscription(user_id)
        if not sub:
            return None

        status = sub.get("_effective_status") or sub.get("status", "active")
        today = datetime.now(timezone.utc).date().isoformat()
        credits = sub.get("credits", 0)
        tier = sub.get("tier", "starter_vnd")
        next_due = sub.get("next_due_at", "")

        if status in ("expired", "cancelled"):
            return _credit_block_response(user_id, tier, f"subscription_{status}")

        if next_due and status == "overdue":
            overdue_days = _days_diff(next_due, today)
            if overdue_days > _cfg["grace_days"]:
                return _credit_block_response(
                    user_id, tier, f"overdue_{overdue_days}d"
                )

        if credits <= 0:
            logger.info(
                '{"event": "pilot_zero_credits", "user_id": "%s", "tier": "%s"}',
                user_id,
                tier,
            )

        return None

    except Exception as exc:
        logger.warning("pilot_credit_gate error: %s", exc)
        return None


_SKIP_PATHS = frozenset({
    "/health",
    "/healthz",
    "/metrics",
    "/v1/pilot/payment-instructions",
    "/v1/pilot/credit-status",
    "/v1/pilot/expiring-clients",
    "/v1/pilot/renew",
    "/v1/pilot/signup",
    "/v1/pilot/health",
    "/v1/pilot/stats",
    "/v1/pilot/recent",
    "/v1/pilot/marketing-signup",
})


class PilotCreditGateMiddleware(BaseHTTPMiddleware):
    """Global middleware: blocks expired/overdue pilot users from credit-consuming routes."""

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


__all__ = [
    "PilotCreditGateMiddleware",
    "_SKIP_PATHS",
    "_STARTER_DEFAULT",
    "_VND_TIERS",
    "_WARN_THRESHOLD_PCT",
    "_cfg",
    "_credit_block_response",
    "_days_diff",
    "_default_bank",
    "_payment_instructions",
    "_payment_text_en",
    "_payment_text_vn",
    "check_pilot_credit",
    "configure",
    "is_enabled",
]

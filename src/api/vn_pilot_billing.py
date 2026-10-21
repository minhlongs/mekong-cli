# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

# DEPRECATED: retained for backward compatibility with vn_pilot_routes.py
# and pilot_credit_gate.py. New code must use src.api.billing_routes.py.

"""VN Pilot Billing — subscription + credit status for pilot users."""

from __future__ import annotations

import hmac
import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status

from src.api.vn_pilot_billing_models import (  # noqa: F401
    CreditStatusResponse,
    ExpiringClient,
    ExpiringClientsResponse,
    PaymentInstructionsResponse,
    RenewResponse,
    VietQRQRRequest,
    VietQRQRResponse,
    _USER_ID_RE,
    _VND_TIERS,
    _days_diff,
    _resolve_user_id,
    _user_status_label,
)
from src.api.vn_pilot_billing_qr import (  # noqa: F401
    _bank_info,
    _payment_instructions_data,
    generate_payment_qr,
    get_payment_instructions,
    qr_router,
)
from src.services.vietqr_generator import build_qr_payload  # noqa: F401
from src.services.vietqr_recurring import (  # noqa: F401
    get_credit_status,
    get_subscription,
    renew_subscription,
)

billing_router = APIRouter()
logger = logging.getLogger(__name__)


@billing_router.get("/credit-status", response_model=CreditStatusResponse)
async def credit_status(request: Request) -> CreditStatusResponse:
    """Return current credit balance + subscription info for paywall decisions."""
    user_id = _resolve_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MEKONG_USER_ID env var or X-User-ID header required",
        )
    sub = get_subscription(user_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found for user")
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
    """Manually topup credits after external payment confirmation."""
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
        updated = renew_subscription(user_id=user_id, bank_tx_ref=tx_ref, paid_at=paid_at)
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
        logger.warning('{"event": "manual_renew_failed", "user_id": "%s", "error": "%s"}', user_id, exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


billing_router.include_router(qr_router)


@billing_router.get(
    "/expiring-clients",
    response_model=ExpiringClientsResponse,
    summary="List pilot users whose subscription expires soon (admin)",
)
async def get_expiring_clients(request: Request, days: int = 7) -> ExpiringClientsResponse:
    """Return pilot users whose subscription expires within `days` days."""
    admin_token = os.environ.get("MEKONG_ADMIN_TOKEN", "")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoint — MEKONG_ADMIN_TOKEN not configured",
        )
    req_token = request.headers.get("x-admin-token", "") or request.query_params.get("admin_token", "")
    if not req_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin endpoint — x-admin-token header or admin_token query param required",
        )
    if not hmac.compare_digest(req_token, admin_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")

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

        if next_due <= cutoff and next_due >= today_str:
            expiring.append(
                ExpiringClient(
                    user_id=uid,
                    tier=sub.get("tier", "starter_vnd"),
                    monthly_vnd=sub.get("monthly_vnd", 199_000),
                    credits=sub.get("credits", 0),
                    next_due_at=next_due,
                    days_until_due=_days_diff(today_str, next_due),
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
    return ExpiringClientsResponse(clients=expiring, scanned=len(seen), warning_days=days)

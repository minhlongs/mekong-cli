# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

# DEPRECATED: retained for backward compatibility with gateway.py.
# New code must use src.api.billing_routes.py.
# See Phase 9 billing consolidation.

"""
VN Payments API — bank webhook handlers for auto-conversion.

POST /v1/payments/vietqr/webhook → Sepay/MB/etc forward bank transfer
confirmations here; we map memo→user_id, amount→tier, call internal conversion.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from src.api import vn_pilot_routes as vpr
from src.api.vn_payments_helpers import (
    _MEMO_RE,
    _TIER_PRICES_VND,
    VietQRWebhookPayload,
    _log_webhook,
    _parse_memo,
    _sync_vietqr_subscription,
    _webhook_log_path,
)
from src.services.vietqr_recurring import (
    create_subscription,
    get_subscription_status,
    renew_subscription,
)
from src.services.vietqr_verifier import get_verifier

router = APIRouter(prefix="/v1/payments", tags=["VN Payments"])


@router.post("/vietqr/webhook")
async def vietqr_webhook(payload: VietQRWebhookPayload, request: Request) -> dict:
    """Receive bank transfer notification, map to pilot conversion + subscription."""
    # 1. Verify signature (gate must pass before we trust ANY payload field)
    try:
        verifier = get_verifier()
    except RuntimeError as exc:
        logging.error("VietQR webhook config error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    if not verifier.verify(body, headers):
        _log_webhook({
            "outcome": "signature_invalid",
            "tx_ref": payload.tx_ref,
            "bank_code": payload.bank_code,
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # 2. Parse memo → (org_id, user_id)
    parsed = _parse_memo(payload.memo)
    if not parsed:
        _log_webhook({
            "outcome": "memo_unparseable",
            "tx_ref": payload.tx_ref,
            "memo_preview": payload.memo[:20],
        })
        logging.warning(
            '{"event": "vietqr_parse_failed", "memo_preview": "%s", "memo_len": %d}',
            payload.memo[:20],
            len(payload.memo),
        )
        return {"status": "memo_unparseable", "tx_ref": payload.tx_ref}
    org_id, user_id = parsed
    logging.info(
        '{"event": "vietqr_parse", "org_id": "%s", "user_id": "%s"}',
        org_id,
        user_id,
    )

    # 3. Match amount → tier (exact match; mismatches logged + accepted)
    tier_key = _TIER_PRICES_VND.get(payload.amount)
    if not tier_key:
        _log_webhook({
            "outcome": "amount_no_tier",
            "tx_ref": payload.tx_ref,
            "user_id": user_id,
            "org_id": org_id,
            "amount": payload.amount,
        })
        return {
            "status": "amount_no_tier",
            "tx_ref": payload.tx_ref,
            "amount": payload.amount,
            "org_id": org_id,
        }

    # 4. Record conversion (idempotent via bank_tx_ref)
    try:
        result = vpr._record_conversion(
            user_id=user_id,
            tier=tier_key,
            monthly_vnd=payload.amount,
            bank_tx_ref=payload.tx_ref,
            org_id=org_id,
        )
    except ValueError as exc:
        _log_webhook({
            "outcome": "user_not_found",
            "tx_ref": payload.tx_ref,
            "user_id": user_id,
            "org_id": org_id,
            "detail": str(exc),
        })
        return {
            "status": "user_not_found",
            "tx_ref": payload.tx_ref,
            "user_id": user_id,
            "org_id": org_id,
        }

    outcome = "already_processed" if not result.get("is_new") else "converted"

    # 5. Subscription management (never raises — webhook must always return 200)
    subscription_action = _sync_vietqr_subscription(
        user_id=user_id,
        org_id=org_id,
        tier_key=tier_key,
        amount=payload.amount,
        tx_ref=payload.tx_ref,
    )

    _log_webhook({
        "outcome": outcome,
        "tx_ref": payload.tx_ref,
        "user_id": user_id,
        "org_id": org_id,
        "tier": tier_key,
        "amount": payload.amount,
        "subscription_action": subscription_action,
    })
    return {
        "status": outcome,
        "tx_ref": payload.tx_ref,
        "user_id": user_id,
        "org_id": org_id,
        "tier": tier_key,
        "subscription_action": subscription_action,
    }


__all__ = [
    "VietQRWebhookPayload",
    "_MEMO_RE",
    "_TIER_PRICES_VND",
    "_log_webhook",
    "_parse_memo",
    "_sync_vietqr_subscription",
    "_webhook_log_path",
    "create_subscription",
    "get_subscription_status",
    "get_verifier",
    "renew_subscription",
    "router",
    "vietqr_webhook",
]

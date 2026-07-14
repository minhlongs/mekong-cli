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

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.services.vietqr_recurring import (
    get_credit_status,
    get_subscription,
    renew_subscription,
)

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


# ---- Models ----

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


# ---- Endpoints ----

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

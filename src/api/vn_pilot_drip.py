"""VN Pilot Drip — Day 3 / 7 / 14 nurture email dispatcher.

Endpoint:
- POST /v1/pilot/drip-trigger → send a nurture email by day offset.

Idempotent by design: caller tracks which day was sent.
No built-in scheduler — operator runs via cron / external trigger.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

import src.api.vn_pilot_common as _common
import src.api.vn_pilot_state as _state
from src.services.resend_client import send_drip_email as _send_drip_email

drip_router = APIRouter()
logger = logging.getLogger(__name__)


class DripTriggerRequest(BaseModel):
    user_id: str = Field(min_length=4, max_length=50)
    drip_day: int = Field(ge=1, le=14, description="Days since signup (3, 7, or 14)")
    background: bool = Field(default=True, description="Fire-and-forget via BackgroundTasks")


class DripTriggerResponse(BaseModel):
    user_id: str
    drip_day: int
    sent: bool
    credential: str = Field(description="'id' from Resend or 'skipped'")
    pilot_onboarded_at: Optional[str] = None


def _days_since(iso_ts: str) -> int:
    try:
        onboarded = datetime.fromisoformat(iso_ts).date()
        return (datetime.now(timezone.utc).date() - onboarded).days
    except (ValueError, TypeError):
        return -1


@drip_router.post(
    "/drip-trigger",
    response_model=DripTriggerResponse,
    summary="Send a Day-3/7/14 nurture email to a pilot user",
)
async def trigger_drip(
    req: DripTriggerRequest,
    background_tasks: BackgroundTasks,
) -> DripTriggerResponse:
    """Dispatch a nurture email based on pilot's elapsed days since signup.

    Validates drip_day against actual onboarding date (won't send Day-3
    email before Day 3). Soft-fails if email infra is unavailable.

    Requires MEKONG_USER_ID env var or X-User-ID header for auth
    (enforced by PilotCreditGateMiddleware when MEKONG_PILOT_GATE=1).
    """
    if not req.user_id.startswith("opc_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id must start with 'opc_'",
        )

    pilots = _common._load_pilots()
    pilot = None
    for p in pilots:
        if p.get("user_id") == req.user_id:
            pilot = p
            break

    if not pilot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pilot user not found",
        )

    onboarded_at = pilot.get("onboarded_at", "")
    elapsed = _days_since(onboarded_at)

    # Gate: don't send early
    if req.drip_day > elapsed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"drip_day={req.drip_day} but only {elapsed} days elapsed "
                f"since signup (onboarded_at={onboarded_at})"
            ),
        )

    email = pilot.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pilot has no email address — cannot send drip",
        )

    credits = _common._credit_balance(req.user_id)
    user_name = pilot.get("name", "Bạn")
    business_type = pilot.get("business_type", "")

    if req.background:
        result_holder: dict = {}

        def _run() -> None:
            result_holder["r"] = _send_drip_email(
                email, user_name, req.user_id, credits, req.drip_day, business_type
            )

        background_tasks.add_task(_run)
        logger.info(
            '{"event": "drip_triggered_bg", "user_id": "%s", "day": %d}',
            req.user_id,
            req.drip_day,
        )
        return DripTriggerResponse(
            user_id=req.user_id,
            drip_day=req.drip_day,
            sent=True,
            credential="queued",
            pilot_onboarded_at=onboarded_at,
        )

    result = _send_drip_email(email, user_name, req.user_id, credits, req.drip_day, business_type)
    logger.info(
        '{"event": "drip_triggered_sync", "user_id": "%s", "day": %d, "result": "%s"}',
        req.user_id,
        req.drip_day,
        result.get("id", "error"),
    )
    return DripTriggerResponse(
        user_id=req.user_id,
        drip_day=req.drip_day,
        sent=result.get("id", "") != "skipped",
        credential=result.get("id", "unknown"),
        pilot_onboarded_at=onboarded_at,
    )

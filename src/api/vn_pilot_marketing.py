# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Lightweight marketing-lead signup.

Matches the marketing site trial form, which only collects email.
Derives a stable user_id from email, creates a pilot record with
minimal fields, and returns credits + user_id on creation.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from src.api import vn_pilot_common as _common

router = APIRouter()
logger = logging.getLogger(__name__)

PILOT_WEEKS = 2
MAX_MARKETING = 500


class MarketingSignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    source: str = Field(default="web_form", pattern=r"^[a-z0-9_]{1,40}$")


class MarketingSignupResponse(BaseModel):
    user_id: str
    credits: int
    pilot_end_at: str
    is_new: bool


@field_validator("email")
def _normalize_email(cls, v: str) -> str:
    return v.strip().lower()


@router.post(
    "/marketing-signup",
    response_model=MarketingSignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Marketing-site trial enrollment (email-only)",
)
async def marketing_signup(
    req: MarketingSignupRequest,
    background_tasks: BackgroundTasks,
) -> MarketingSignupResponse:
    org_id = "default"
    email = req.email

    existing = _common._find_by_email(email, org_id)
    if existing:
        return MarketingSignupResponse(
            user_id=existing["user_id"],
            credits=_common._credit_balance(existing["user_id"]),
            pilot_end_at=existing["pilot_end_at"],
            is_new=False,
        )

    pilots = _common._org_filter(_common._load_pilots(), org_id)
    if len(pilots) >= MAX_MARKETING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pilot đã đủ. Vui lòng đăng ký waitlist: hello@mekongmind.com",
        )

    seq = len(pilots) + 1
    digest = hashlib.sha256(email.encode()).hexdigest()[:6]
    user_id = f"opc_web_{seq:03d}_{digest}"

    display_name = req.name or email.split("@")[0]
    now = datetime.now(timezone.utc)
    record = {
        "user_id": user_id,
        "name": display_name,
        "zalo": f"web:{email}",
        "email": email,
        "business_type": "other",
        "city": "HCM",
        "source": req.source,
        "org_id": org_id,
        "onboarded_at": now.isoformat(timespec="seconds"),
        "pilot_end_at": (now + timedelta(weeks=PILOT_WEEKS)).isoformat(timespec="seconds"),
        "status": "active",
    }
    _common._append_pilot(record)
    credits = _common._add_credits(user_id, _common.INITIAL_FREE_CREDITS)

    # Best-effort welcome email (skip if RESEND not configured)
    try:
        from src.services.resend_client import send_welcome_email as _send
        background_tasks.add_task(
            _send, email, display_name, user_id, credits, record["pilot_end_at"]
        )
    except Exception:
        pass

    return MarketingSignupResponse(
        user_id=user_id,
        credits=credits,
        pilot_end_at=record["pilot_end_at"],
        is_new=True,
    )
marketing_router = router

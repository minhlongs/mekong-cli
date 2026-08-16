# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VN Pilot — signup route + founder webhook notification."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from src.api.vn_pilot_common import (
    INITIAL_FREE_CREDITS,
    PILOT_DURATION_WEEKS,
    SignupRequest,
    SignupResponse,
    _add_credits,
    _append_pilot,
    _find_by_zalo,
    _credit_balance,
    _org_filter,
    _load_pilots,
    _stable_user_id,
)
import src.api.vn_pilot_state as _state
import src.api.vn_pilot_routes as _routes  # noqa: E402
from src.services.resend_client import send_welcome_email as _send_welcome_email

signup_router = APIRouter(tags=["VN Pilot"])

logger = logging.getLogger(__name__)


async def _notify_founder_signup(record: dict) -> None:
    """Fire founder webhook on new pilot signup. Non-blocking, resilient.

    Env vars (both optional):
    - MEKONG_SIGNUP_WEBHOOK_URL: target endpoint (Zapier/Pipedream/Telegram bot)
    - MEKONG_SIGNUP_WEBHOOK_AUTH: optional Authorization header value

    Failures logged at WARNING but never raised — signup response must
    succeed even if webhook endpoint is down.
    """
    url = os.environ.get("MEKONG_SIGNUP_WEBHOOK_URL")
    if not url:
        return
    headers = {"Content-Type": "application/json"}
    auth = os.environ.get("MEKONG_SIGNUP_WEBHOOK_AUTH")
    if auth:
        headers["Authorization"] = auth
    payload = {
        "event": "pilot.signup.new",
        "user_id": record.get("user_id"),
        "name": record.get("name"),
        "zalo": record.get("zalo"),
        "business_type": record.get("business_type"),
        "city": record.get("city"),
        "industry": record.get("industry"),
        "source": record.get("source"),
        "onboarded_at": record.get("onboarded_at"),
    }
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                logging.warning(
                    "Founder signup webhook returned %d: %s",
                    resp.status_code,
                    resp.text[:200],
                )
    except Exception as exc:  # noqa: BLE001
        logging.warning("Founder signup webhook failed: %s", exc)


@signup_router.post(
    "/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    req: SignupRequest,
    background_tasks: BackgroundTasks,
) -> SignupResponse:
    """Onboard 1 pilot user. Idempotent: same Zalo -> return existing user_id."""
    org_id = req.org_id
    existing = _find_by_zalo(req.zalo, org_id)
    if existing:
        return SignupResponse(
            user_id=existing["user_id"],
            credits=_credit_balance(existing["user_id"]),
            pilot_end_at=existing["pilot_end_at"],
            is_new=False,
        )

    org_pilots = _org_filter(_load_pilots(), org_id)
    seq = len(org_pilots) + 1
    if seq > _state.MAX_PILOTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pilot da du {_state.MAX_PILOTS} user. Subscribe waitlist: hello@mekongmind.com",
        )

    user_id = _stable_user_id(req.name, req.zalo, seq, org_id)
    now = datetime.now(timezone.utc)
    record = {
        "user_id": user_id,
        "name": req.name,
        "zalo": req.zalo,
        "business_type": req.business_type,
        "city": req.city,
        "industry": req.industry,
        "source": req.source,
        "org_id": org_id,
        "onboarded_at": now.isoformat(timespec="seconds"),
        "pilot_end_at": (
            now + timedelta(weeks=PILOT_DURATION_WEEKS)
        ).isoformat(timespec="seconds"),
        "status": "active",
    }
    _append_pilot(record)
    balance = _add_credits(user_id, INITIAL_FREE_CREDITS)

    # Fire-and-forget welcome email: soft-fail if RESEND_API_KEY missing.
    if req.email:
        background_tasks.add_task(
            _send_welcome_email,
            req.email,
            req.name,
            user_id,
            balance,
            record["pilot_end_at"],
        )

    # Resolve _notify_founder_signup through vn_pilot_routes so that
    # tests can monkeypatch the shared closure via
    # monkeypatch.setattr(vpr, "_notify_founder_signup", ...).
    # Lazy import avoids circular at module load time.
    notify_fn = getattr(
        _routes, "_notify_founder_signup", _notify_founder_signup
    )
    background_tasks.add_task(notify_fn, record)

    return SignupResponse(
        user_id=user_id,
        credits=balance,
        pilot_end_at=record["pilot_end_at"],
        is_new=True,
    )

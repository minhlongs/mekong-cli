# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VN Pilot — poll response route."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.api.raas_auth_middleware import require_tenant
from src.api.vn_pilot_common import (
    PollResponseRequest,
    _append_response,
    _current_iso_week,
    _load_pilots,
)
from src.raas.auth import TenantContext

logger = logging.getLogger(__name__)
polls_router = APIRouter(tags=["VN Pilot"])


def _optional_tenant(request: Request) -> Optional[TenantContext]:
    """Try to resolve tenant from Bearer token; fall back to None on auth failure.

    Logs a deprecation warning when the request arrives without valid credentials
    so operators can track migration progress before auth becomes mandatory.
    """
    auth_header: Optional[str] = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(
            "Anonymous poll response from %s — auth mandatory after 2026-07-01.",
            request.client.host if request.client else "unknown",
        )
        return None
    try:
        return require_tenant(request)
    except HTTPException:
        logger.warning(
            "Rejected poll response (invalid token) from %s — auth mandatory after 2026-07-01.",
            request.client.host if request.client else "unknown",
        )
        return None


@polls_router.post("/response", status_code=status.HTTP_201_CREATED)
async def poll_response(
    req: PollResponseRequest,
    tenant: Optional[TenantContext] = Depends(_optional_tenant),
    response: Response = None,
) -> dict[str, object]:
    """Capture poll response — accepts authenticated and anonymous requests.

    Authenticated requests resolve to a tenant context.
    Anonymous requests are accepted with a deprecation warning;
    the ``X-Auth-Deprecated`` response header signals the upcoming mandatory change.
    """
    if not any(p["user_id"] == req.user_id for p in _load_pilots()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown user_id: {req.user_id}",
        )
    iso_week = req.iso_week or _current_iso_week()
    record = {
        "user_id": req.user_id,
        "score": req.score,
        "comment": req.comment,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "iso_week": iso_week,
    }
    _append_response(record)
    if tenant is None:
        response.headers["X-Auth-Deprecated"] = "true"
        response.headers["X-Auth-Deprecation-Info"] = (
            "Authorization will be mandatory after 2026-07-01. "
            "Provide Bearer mk_<key> to opt in."
        )
    return {
        "recorded": True,
        "user_id": req.user_id,
        "score": req.score,
        "iso_week": iso_week,
        "low_nps_alert": req.score < 4,
    }

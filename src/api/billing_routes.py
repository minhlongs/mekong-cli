# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Billing routes — Polar.sh org subscription checkout + webhook handler."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.api.billing_routes_models import (  # noqa: F401
    _extract_email_from_request,
    _log_webhook_error,
    _open_db_conn,
    _state,
    _webhook_log_path,
)
from src.api.billing_routes_webhooks import (  # noqa: F401
    _dispatch_event,
    _handle_subscription_cancelled,
    _handle_subscription_created,
    webhook_org,
    webhooks_router,
)
from src.api.vn_pilot_auth import _require_scope
from src.services import org_service  # noqa: F401
from src.services.polar_client import (  # noqa: F401
    PolarAPIError,
    PolarEventInvalid,
    create_checkout_session,
    parse_event,
    verify_webhook_signature,
)
from src.services.sqlite_migrations import ensure_schema  # noqa: F401

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/billing", tags=["billing"])


@router.post(
    "/checkout/org",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def checkout_org(
    request: Request,
    org_id: str = Query(..., min_length=1, max_length=64),
) -> dict:
    """Create a Polar.sh checkout session for an org platform fee."""
    email = _extract_email_from_request(request)

    conn = _open_db_conn()
    try:
        org_row = conn.execute(
            "SELECT org_id, status FROM orgs WHERE org_id = ?",
            (org_id,),
        ).fetchone()

        if org_row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Org not found",
            )

        if org_row["status"] == "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="org_already_active",
            )
    finally:
        conn.close()

    product_id = os.environ.get("POLAR_PRODUCT_ID_ORG_PLATFORM_FEE", "")
    if not product_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="POLAR_PRODUCT_ID_ORG_PLATFORM_FEE not set",
        )

    base_url = os.environ.get("MEKONG_PUBLIC_BASE_URL", "https://api.mekong.dev")
    success_url = f"{base_url}/billing/success"
    cancel_url = f"{base_url}/billing/cancel"

    try:
        result = create_checkout_session(
            org_id=org_id,
            customer_email=email,
            product_id=product_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except PolarAPIError as exc:
        _log_webhook_error(f"checkout API error: {exc.status} {exc.body[:200]}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Polar API error",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "checkout_url": result["url"],
        "polar_checkout_id": result["id"],
    }


router.include_router(webhooks_router)

__all__ = ["router"]

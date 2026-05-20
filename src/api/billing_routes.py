"""Billing routes — Polar.sh org subscription checkout + webhook handler.

Two endpoints:
  POST /v1/billing/checkout/org?org_id=<slug>  — org_admin/founder gate
  POST /v1/billing/webhook/org                 — public (signature-gated)

Follows Phase 7 P02 webhook error idiom: 200-on-app-error, 401 on bad sig,
503 on missing secret. Errors logged to ~/.mekong/polar_webhook.log.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import src.api.vn_pilot_state as _state
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.api.vn_pilot_auth import _require_scope
from src.services import org_service
from src.services.polar_client import (
    PolarAPIError,
    PolarEventInvalid,
    create_checkout_session,
    parse_event,
    verify_webhook_signature,
)
from src.services.sqlite_migrations import ensure_schema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/billing", tags=["billing"])

# ---------- Webhook error log ----------


def _webhook_log_path() -> Path:
    """Resolve webhook log path at call time (respects CONFIG_DIR monkeypatch)."""
    return _state.CONFIG_DIR / "polar_webhook.log"


def _log_webhook_error(msg: str) -> None:
    """Append error to polar_webhook.log (mode 0600)."""
    try:
        _state.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = _webhook_log_path()
        if not log_path.exists():
            log_path.touch(mode=0o600)
        ts = datetime.now(timezone.utc).isoformat()
        with open(log_path, "a") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass  # Never let logging break the webhook handler


def _open_db_conn():
    """Open SQLite connection with schema ensured."""
    import sqlite3

    from src.services.org_service import _db_path

    db = _db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    ensure_schema(conn)
    return conn


# ---------- Checkout endpoint ----------


@router.post(
    "/checkout/org",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def checkout_org(
    request: Request,
    org_id: str = Query(..., min_length=1, max_length=64),
) -> dict:
    """Create a Polar.sh checkout session for an org platform fee.

    Requires org_admin or founder scope. Only unverified orgs can checkout.

    Returns 409 if org is already active.
    Returns 404 if org not found.
    """
    # Extract email from JWT for Polar customer_email
    email = _extract_email_from_request(request)

    # Verify org status
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

    # Create Polar checkout session
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


# ---------- Webhook endpoint ----------


@router.post("/webhook/org")
async def webhook_org(request: Request) -> dict:
    """Handle Polar.sh webhooks for org subscription lifecycle.

    Signature-gated: 401 on bad HMAC, 503 on missing secret.
    Idempotent: replay returns 200 noop.
    App errors return 200 {ok: false, reason: "..."} (Phase 7 P02 idiom).
    """
    raw_body = await request.body()
    headers = dict(request.headers)

    # 503 if secret not configured
    webhook_secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")
    if not webhook_secret:
        _log_webhook_error("webhook rejected: POLAR_WEBHOOK_SECRET not set")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )

    # 401 on bad signature
    try:
        sig_valid = verify_webhook_signature(headers, raw_body, webhook_secret)
    except ValueError as exc:
        # Replay window expired
        _log_webhook_error(f"webhook replay window: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="replay_window_expired",
        ) from exc

    if not sig_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bad_signature",
        )

    # Parse event
    try:
        event = parse_event(raw_body)
    except PolarEventInvalid as exc:
        _log_webhook_error(f"event parse error: {exc}")
        return {"ok": False, "reason": "invalid_event"}

    event_id = event["event_id"]
    event_type = event["event_type"]
    payload = event["payload"]

    # Idempotency check
    conn = _open_db_conn()
    try:
        seen = conn.execute(
            "SELECT 1 FROM polar_webhook_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()

        if seen is not None:
            return {"ok": True, "replayed": True}

        # Store event
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        conn.execute(
            """
            INSERT INTO polar_webhook_events
                (event_id, event_type, received_at, org_id, raw_payload, processed_ok)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (event_id, event_type, now_iso, None, raw_body.decode("utf-8")),
        )
        conn.commit()
    finally:
        conn.close()

    # Dispatch by event type
    try:
        _dispatch_event(event_type, payload)
    except Exception as exc:
        _log_webhook_error(f"dispatch error {event_type}: {exc}")
        # Mark as failed
        conn = _open_db_conn()
        try:
            conn.execute(
                "UPDATE polar_webhook_events SET processed_ok = 0 WHERE event_id = ?",
                (event_id,),
            )
            conn.commit()
        finally:
            conn.close()
        return {"ok": False, "reason": str(exc)}

    return {"ok": True}


def _dispatch_event(event_type: str, payload: dict) -> None:
    """Route webhook event to handler."""
    if event_type == "subscription.created":
        _handle_subscription_created(payload)
    elif event_type == "subscription.cancelled":
        _handle_subscription_cancelled(payload)
    elif event_type == "checkout.completed":
        pass  # No-op; handled via subscription.created
    else:
        logger.info("Polar webhook: unhandled event type %s", event_type)


def _handle_subscription_created(payload: dict) -> None:
    """subscription.created → mark_org_paid."""
    data = payload.get("data", payload)
    org_id = data.get("metadata", {}).get("mekong_org_id", "")
    polar_sub_id = data.get("id", "")
    current_period_end = data.get("current_period_end", "")

    if not org_id:
        _log_webhook_error("subscription.created: missing mekong_org_id in metadata")
        return

    # Verify org exists
    conn = _open_db_conn()
    try:
        org_row = conn.execute(
            "SELECT 1 FROM orgs WHERE org_id = ?", (org_id,)
        ).fetchone()
        if org_row is None:
            _log_webhook_error(
                f"subscription.created: org '{org_id}' not found — possible metadata tampering"
            )
            return
    finally:
        conn.close()

    org_service.mark_org_paid(org_id, polar_sub_id, current_period_end)


def _handle_subscription_cancelled(payload: dict) -> None:
    """subscription.cancelled → mark_org_cancelled."""
    data = payload.get("data", payload)
    org_id = data.get("metadata", {}).get("mekong_org_id", "")

    if not org_id:
        _log_webhook_error("subscription.cancelled: missing mekong_org_id in metadata")
        return

    org_service.mark_org_cancelled(org_id)


# ---------- Helpers ----------


def _extract_email_from_request(request: Request) -> str:
    """Decode bearer JWT and return sub (email) claim.
    Falls back to legacy admin token → placeholder email.
    Raises HTTPException 401 on any failure.
    """
    from src.api.vn_pilot_auth import JWTExpiredError, JWTInvalidError
    from src.services.admin_token_service import decode_jwt

    jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT auth disabled — MEKONG_JWT_SECRET not set",
        )

    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'Authorization: Bearer <token>' header",
        )
    raw_token = auth[len("Bearer "):].strip()

    # Legacy admin token passthrough
    legacy = os.environ.get("MEKONG_ADMIN_TOKEN")
    if legacy and raw_token == legacy:
        return "admin@legacy"

    try:
        claims = decode_jwt(raw_token, jwt_secret)
    except JWTExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    email = claims.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT missing sub claim",
        )
    return email

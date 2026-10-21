# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Polar.sh webhook handler and event dispatchers for org subscriptions."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from src.api.billing_routes_models import _facade, _log_webhook_error, _open_db_conn
from src.services import org_service
from src.services.polar_client import PolarEventInvalid, parse_event, verify_webhook_signature

logger = logging.getLogger(__name__)
webhooks_router = APIRouter()


@webhooks_router.post("/webhook/org")
async def webhook_org(request: Request) -> dict:
    """Handle Polar.sh webhooks for org subscription lifecycle."""
    raw_body = await request.body()
    headers = dict(request.headers)
    facade = _facade()
    log_err = getattr(facade, "_log_webhook_error", _log_webhook_error) if facade else _log_webhook_error
    open_conn = getattr(facade, "_open_db_conn", _open_db_conn) if facade else _open_db_conn
    verify_fn = getattr(facade, "verify_webhook_signature", verify_webhook_signature) if facade else verify_webhook_signature
    parse_fn = getattr(facade, "parse_event", parse_event) if facade else parse_event
    dispatch_fn = getattr(facade, "_dispatch_event", _dispatch_event) if facade else _dispatch_event

    webhook_secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")
    if not webhook_secret:
        log_err("webhook rejected: POLAR_WEBHOOK_SECRET not set")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )

    try:
        sig_valid = verify_fn(headers, raw_body, webhook_secret)
    except ValueError as exc:
        log_err(f"webhook replay window: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="replay_window_expired",
        ) from exc

    if not sig_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad_signature")

    try:
        event = parse_fn(raw_body)
    except PolarEventInvalid as exc:
        log_err(f"event parse error: {exc}")
        return {"ok": False, "reason": "invalid_event"}

    event_id = event["event_id"]
    event_type = event["event_type"]
    payload = event["payload"]

    conn = open_conn()
    try:
        seen = conn.execute(
            "SELECT 1 FROM polar_webhook_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if seen is not None:
            return {"ok": True, "replayed": True}

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

    try:
        dispatch_fn(event_type, payload)
    except Exception as exc:
        log_err(f"dispatch error {event_type}: {exc}")
        conn = open_conn()
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
    facade = _facade()
    created_fn = getattr(facade, "_handle_subscription_created", _handle_subscription_created) if facade else _handle_subscription_created
    cancelled_fn = getattr(facade, "_handle_subscription_cancelled", _handle_subscription_cancelled) if facade else _handle_subscription_cancelled
    if event_type == "subscription.created":
        created_fn(payload)
    elif event_type == "subscription.cancelled":
        cancelled_fn(payload)
    elif event_type == "checkout.completed":
        pass
    else:
        logger.info("Polar webhook: unhandled event type %s", event_type)


def _handle_subscription_created(payload: dict) -> None:
    """subscription.created -> mark_org_paid."""
    facade = _facade()
    log_err = getattr(facade, "_log_webhook_error", _log_webhook_error) if facade else _log_webhook_error
    open_conn = getattr(facade, "_open_db_conn", _open_db_conn) if facade else _open_db_conn
    org_svc = getattr(facade, "org_service", org_service) if facade else org_service

    data = payload.get("data", payload)
    org_id = data.get("metadata", {}).get("mekong_org_id", "")
    polar_sub_id = data.get("id", "")
    current_period_end = data.get("current_period_end", "")

    if not org_id:
        log_err("subscription.created: missing mekong_org_id in metadata")
        return

    conn = open_conn()
    try:
        org_row = conn.execute("SELECT 1 FROM orgs WHERE org_id = ?", (org_id,)).fetchone()
        if org_row is None:
            log_err(f"subscription.created: org '{org_id}' not found — possible metadata tampering")
            return
    finally:
        conn.close()

    org_svc.mark_org_paid(org_id, polar_sub_id, current_period_end)


def _handle_subscription_cancelled(payload: dict) -> None:
    """subscription.cancelled -> mark_org_cancelled."""
    facade = _facade()
    log_err = getattr(facade, "_log_webhook_error", _log_webhook_error) if facade else _log_webhook_error
    org_svc = getattr(facade, "org_service", org_service) if facade else org_service

    data = payload.get("data", payload)
    org_id = data.get("metadata", {}).get("mekong_org_id", "")

    if not org_id:
        log_err("subscription.cancelled: missing mekong_org_id in metadata")
        return

    org_svc.mark_org_cancelled(org_id)

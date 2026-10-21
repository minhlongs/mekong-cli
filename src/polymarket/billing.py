# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CashClaw billing — Polar.sh subscription management for 3 tiers."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, HTTPException, Request

from src.polymarket.billing_models import BillingDB, Subscription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/polar", tags=["CashClaw Billing"])

POLAR_WEBHOOK_SECRET = os.getenv("POLAR_WEBHOOK_SECRET", "")
DB_PATH = os.getenv("DATABASE_PATH", "data/algo-trade.db")

# Product ID → tier mapping
PRODUCT_TIERS: dict[str, str] = {
    os.getenv("POLAR_STARTER_PRODUCT_ID", "prod_starter"): "starter",
    os.getenv("POLAR_PRO_PRODUCT_ID", "prod_pro"): "pro",
    os.getenv("POLAR_ENTERPRISE_PRODUCT_ID", "prod_enterprise"): "elite",
}


def verify_polar_signature(payload: bytes, signature: str) -> bool:
    """Verify Polar.sh webhook HMAC-SHA256 signature."""
    import src.polymarket.billing as _billing

    secret = _billing.POLAR_WEBHOOK_SECRET
    if not secret:
        logger.warning("POLAR_WEBHOOK_SECRET not set — skipping verification")
        return True

    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    provided = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, provided)


@router.post("")
async def handle_polar_webhook(request: Request) -> dict:
    """Handle Polar.sh subscription webhooks."""
    body = await request.body()
    signature = request.headers.get("X-Polar-Signature", "")

    if not verify_polar_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get("type", "")
    data = payload.get("data", {}).get("object", {})

    import src.polymarket.billing as _billing

    db = BillingDB(_billing.DB_PATH)
    subscription_id = data.get("id", "unknown")
    db.log_event(event_type, subscription_id, body.decode())

    if event_type == "subscription.created":
        return _handle_subscription_created(db, data)
    elif event_type == "subscription.updated":
        return _handle_subscription_updated(db, data)
    elif event_type == "subscription.cancelled":
        return _handle_subscription_cancelled(db, data)
    elif event_type == "payment.failed":
        return _handle_payment_failed(db, data)
    else:
        logger.info("Unhandled webhook event: %s", event_type)
        return {"status": "ignored", "event": event_type}


def _handle_subscription_created(db: BillingDB, data: dict) -> dict:
    import src.polymarket.billing as _billing

    product_id = data.get("product_id", "")
    tier = _billing.PRODUCT_TIERS.get(product_id, "starter")
    sub = db.provision_subscription(
        subscription_id=data.get("id", ""),
        user_id=data.get("customer_id", ""),
        email=data.get("customer_email", ""),
        tier=tier,
    )
    return {"status": "provisioned", "tier": tier, "api_key": sub.api_key, "subscription_id": sub.subscription_id}


def _handle_subscription_updated(db: BillingDB, data: dict) -> dict:
    import src.polymarket.billing as _billing

    product_id = data.get("product_id", "")
    new_tier = _billing.PRODUCT_TIERS.get(product_id, "starter")
    subscription_id = data.get("id", "")
    db.update_tier(subscription_id, new_tier)
    return {"status": "updated", "tier": new_tier}


def _handle_subscription_cancelled(db: BillingDB, data: dict) -> dict:
    subscription_id = data.get("id", "")
    db.cancel_subscription(subscription_id, grace_days=7)
    return {"status": "cancelled", "grace_days": 7}


def _handle_payment_failed(db: BillingDB, data: dict) -> dict:
    subscription_id = data.get("subscription_id", "")
    logger.warning("Payment failed for subscription %s", subscription_id)
    return {"status": "payment_failed", "retry_days": 3}


__all__ = [
    "BillingDB", "DB_PATH", "POLAR_WEBHOOK_SECRET", "PRODUCT_TIERS",
    "Subscription", "_handle_payment_failed", "_handle_subscription_cancelled",
    "_handle_subscription_created", "_handle_subscription_updated",
    "handle_polar_webhook", "router", "verify_polar_signature",
]

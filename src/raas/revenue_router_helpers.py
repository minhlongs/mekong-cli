# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pricing constants, request models, and Polar webhook verification helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import time as _time

from fastapi import HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

CREDIT_MAP = {
    "free": 50,
    "starter": 300,
    "growth": 1200,
    "scale": 3500,
    "pro": 7000,
}

# Polar.sh product/price IDs — set POLAR_PRICE_<TIER> env vars to override
_POLAR_PRICE_DEFAULTS = {
    "starter": "polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA",
    "growth": "polar_cl_TDhelBvQfsZq3Rayqf9to4tl0UD6D04OBFqXm1zJDVC",
    "pro": "polar_cl_zi7LHdaPk93V0xbNVQZgqum96gWCFDTVzpDNR2kfN3j",
}

_POLAR_PRODUCT_TO_TIER = {v: k for k, v in _POLAR_PRICE_DEFAULTS.items()}

_PRICING_TIERS = [
    {"name": "Free", "tier": "free", "price_usd": 0, "credits": 50},
    {"name": "Starter", "tier": "starter", "price_usd": 49, "credits": 300},
    {"name": "Growth", "tier": "growth", "price_usd": 149, "credits": 1200},
    {"name": "Scale", "tier": "scale", "price_usd": 299, "credits": 3500},
    {"name": "Pro", "tier": "pro", "price_usd": 499, "credits": 7000},
]


class OnboardRequest(BaseModel):
    name: str = Field(..., description="Tenant name (company or person)")
    email: str = Field(..., description="Contact email")


class OnboardResponse(BaseModel):
    tenant_id: str
    api_key: str
    credits: int
    message: str


def _polar_checkout_base() -> str:
    """Return the Polar.sh organisation checkout base URL."""
    return os.environ.get(
        "POLAR_CHECKOUT_BASE",
        "https://polar.sh/longtho638-jpg/mekong-cli/subscriptions",
    )


def _polar_price_id(tier: str) -> str:
    """Return the Polar price ID for a given tier (from env or fallback)."""
    env_key = f"POLAR_PRICE_{tier.upper()}"
    return os.environ.get(env_key, _POLAR_PRICE_DEFAULTS.get(tier, tier))


def _tier_from_session(session_id: str) -> str:
    """Derive tier from Polar session_id prefix convention."""
    for tier in CREDIT_MAP:
        if tier in session_id.lower():
            return tier
    return "starter"


def verify_polar_webhook_signature(request: Request, body: bytes) -> None:
    """Verify Standard Webhooks HMAC signature for Polar.sh webhook requests."""
    secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")

    if not secret:
        if os.environ.get("POLAR_WEBHOOK_SKIP_VERIFY") == "true":
            logger.warning("DEV MODE: POLAR_WEBHOOK_SKIP_VERIFY=true — skipping verification")
            return
        logger.error("POLAR_WEBHOOK_SECRET not set — rejecting webhook")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    webhook_id = request.headers.get("webhook-id", "")
    webhook_ts = request.headers.get("webhook-timestamp", "")
    webhook_sig = request.headers.get("webhook-signature", "")

    if not (webhook_id and webhook_ts and webhook_sig):
        raise HTTPException(status_code=401, detail="Missing webhook signature headers")

    try:
        ts = int(webhook_ts)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid webhook timestamp") from exc
    if abs(_time.time() - ts) > 300:
        raise HTTPException(status_code=401, detail="Webhook replay window expired")

    signing_input = f"{webhook_id}.{webhook_ts}.{body.decode('utf-8')}"
    expected = base64.b64encode(
        hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    ).decode()

    sig_parts = webhook_sig.split(",", 1)
    if len(sig_parts) != 2 or sig_parts[0] != "v1":
        raise HTTPException(status_code=401, detail="Invalid signature format")
    if not hmac.compare_digest(expected, sig_parts[1]):
        logger.warning("Webhook signature mismatch: got=%s", webhook_sig[:20])
        raise HTTPException(status_code=401, detail="Invalid signature")

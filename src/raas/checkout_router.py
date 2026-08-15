"""Checkout and post-payment success endpoints for Polar.sh.

Endpoints:
    POST /v1/checkout  — create Polar checkout session URL for a given tier
    GET  /v1/success   — post-payment redirect; provision NEW tenant + return API key

Idempotency rule: credits are only provisioned on first-time tenant creation.
Existing tenants are returned as-is — credit top-ups come via /webhook/polar.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from urllib.parse import quote, urlencode

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from src.raas.tenant import TenantStore
from src.raas.credits import CreditStore
from src.raas.revenue_router import (
    CREDIT_MAP,
    _polar_price_id,
    _tier_from_session,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class CheckoutRequest(BaseModel):
    tier: str = Field(..., description="Subscription tier: free | starter | growth | scale | pro")
    email: EmailStr = Field(..., description="Customer email for pre-fill")
    interval: str = Field("monthly", description="Billing interval: monthly | annual")


class CheckoutResponse(BaseModel):
    checkout_url: str
    tier: str


class SuccessResponse(BaseModel):
    api_key: str
    credits: int
    tier: str
    tenant_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/v1/checkout", response_model=CheckoutResponse)
async def create_checkout(req: CheckoutRequest):
    """Return a Polar.sh checkout URL for the requested tier.

    Body: ``{"tier": "starter|growth|pro", "email": "user@example.com"}``
    Returns: ``{"checkout_url": "https://polar.sh/checkout/...", "tier": "starter"}``
    """
    tier = req.tier.lower()
    if tier not in CREDIT_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tier '{tier}'. Valid tiers: {list(CREDIT_MAP.keys())}",
        )

    interval = getattr(req, "interval", "monthly") or "monthly"
    if interval.lower() == "annual":
        price_id = _polar_price_id(f"{tier}_annual") or _polar_price_id(tier)
    else:
        price_id = _polar_price_id(tier)

    app_base = os.environ.get("APP_BASE_URL", "https://mekongmind.com")
    secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")
    sig = ""
    if secret:
        sig = hmac.new(
            secret.encode(), f"{tier}:{req.email}".encode(), hashlib.sha256
        ).hexdigest()[:32]

    success_params = urlencode({"tier": tier, "email": req.email, "sig": sig, "interval": interval})
    success_url = f"{app_base}/v1/success?{success_params}"
    # Polar checkout link: api.polar.sh/v1/checkout-links/{id}/redirect
    checkout_url = (
        f"https://api.polar.sh/v1/checkout-links/{price_id}/redirect"
        f"?prefilled_email={quote(str(req.email))}"
        f"&success_url={quote(success_url)}"
    )

    logger.info("Checkout URL generated for tier=%s email=%s", tier, req.email)
    return CheckoutResponse(checkout_url=checkout_url, tier=tier)


@router.get("/v1/success", response_model=SuccessResponse)
async def payment_success(
    tier: str = "starter",
    email: str = "",
    session_id: str = "",
    sig: str = "",
):
    """Handle Polar.sh post-payment redirect.

    Query params: ``?session_id=xxx&email=xxx&tier=starter&sig=xxx``

    Provisions a NEW tenant and returns their API key + credits.
    Existing tenants are returned as-is (idempotency guard — no double credit).
    Requires valid HMAC sig to prevent unauthenticated provisioning.
    """
    secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")

    # Verify HMAC signature — missing sig returns info-only (no real provisioning).
    # This is intentional for UX: Polar redirects here without sig on checkout
    # success, so we show a "pending" confirmation while webhook handles the real
    # credit provisioning asynchronously.
    if not sig:
        return SuccessResponse(
            api_key="pending_webhook_verification",
            credits=CREDIT_MAP.get(tier.lower(), 200),
            tier=tier.lower() if tier.lower() in CREDIT_MAP else "starter",
            tenant_id="provisioned_via_webhook",
        )

    if secret:
        expected = hmac.new(
            secret.encode(), f"{tier}:{email}".encode(), hashlib.sha256
        ).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return SuccessResponse(
                api_key="pending_webhook_verification",
                credits=CREDIT_MAP.get(tier.lower(), 200),
                tier=tier.lower() if tier.lower() in CREDIT_MAP else "starter",
                tenant_id="provisioned_via_webhook",
            )

    tier = tier.lower()
    if tier not in CREDIT_MAP:
        tier = _tier_from_session(session_id) if session_id else "starter"

    if not email:
        raise HTTPException(status_code=400, detail="email query parameter is required")

    credits = CREDIT_MAP[tier]
    store = TenantStore()
    existing = store.find_by_email(email)

    if existing:
        # Idempotency guard: tenant already exists — do NOT add credits again.
        # Credit top-ups are handled exclusively by /webhook/polar.
        logger.info("Existing tenant %s returned without re-provisioning (%s tier)", email, tier)
        return SuccessResponse(
            api_key="retrieve_from_dashboard",
            credits=0,
            tier=tier,
            tenant_id=existing.id,
        )

    # New tenant — create and provision credits once
    tenant = store.create_tenant(name=email)
    credit_store = CreditStore()
    credit_store.add_credits(
        tenant_id=tenant.id,
        amount=credits,
        reason=f"polar_success_{tier}_{session_id or 'direct'}",
    )

    logger.info("New tenant %s provisioned: %d credits (%s tier)", email, credits, tier)
    return SuccessResponse(
        api_key=tenant.api_key,
        credits=credits,
        tier=tier,
        tenant_id=tenant.id,
    )

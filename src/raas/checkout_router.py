# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Checkout and post-payment success endpoints.

Endpoints:
    POST /v1/checkout  — return tier + credit metadata for a requested tier
    GET  /v1/success   — post-payment redirect; provision NEW tenant + return API key

Idempotency rule: credits are only provisioned on first-time tenant creation.
Existing tenants are returned as-is — credit top-ups come via the payment
provider's webhook (see the payment rail router).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from src.raas.billing_tiers import CREDIT_MAP, tier_from_reference
from src.raas.tenant import TenantStore
from src.raas.credits import CreditStore

logger = logging.getLogger(__name__)

router = APIRouter()


class CheckoutRequest(BaseModel):
    tier: str = Field(..., description="Subscription tier: free | starter | growth | scale | pro")
    email: EmailStr = Field(..., description="Customer email for pre-fill")
    interval: str = Field("monthly", description="Billing interval: monthly | annual")


class CheckoutResponse(BaseModel):
    checkout_url: str
    tier: str
    credits: int
    checkout_provider: str


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
    """Return checkout metadata for the requested tier.

    Body: ``{"tier": "starter|growth|pro", "email": "user@example.com"}``
    Returns: ``{"tier": "starter", "credits": 300, "checkout_provider": "nowpayments"}``

    The concrete payment-session URL is created by the payment rail itself
    (NOWPayments / VietQR); this endpoint only publishes the tier and the
    credits the tier grants, so clients know what they are buying.
    """
    tier = req.tier.lower()
    if tier not in CREDIT_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tier '{tier}'. Valid tiers: {list(CREDIT_MAP.keys())}",
        )

    credits = CREDIT_MAP[tier]
    logger.info("Checkout requested for tier=%s email=%s credits=%d", tier, req.email, credits)

    return CheckoutResponse(
        checkout_url="",
        tier=tier,
        credits=credits,
        checkout_provider="nowpayments",
    )


@router.get("/v1/success", response_model=SuccessResponse)
async def payment_success(
    tier: str = "starter",
    email: str = "",
    session_id: str = "",
):
    """Handle the post-payment redirect.

    Query params: ``?session_id=xxx&email=xxx&tier=starter``

    Provisions a NEW tenant and returns their API key + credits.
    Existing tenants are returned as-is (idempotency guard — no double credit).
    """
    resolved_tier = tier.lower()
    if resolved_tier not in CREDIT_MAP:
        resolved_tier = tier_from_reference(session_id) if session_id else "starter"

    if not email:
        raise HTTPException(status_code=400, detail="email query parameter is required")

    credits = CREDIT_MAP[resolved_tier]
    store = TenantStore()
    existing = store.find_by_email(email)

    if existing:
        # Idempotency guard: tenant already exists — do NOT add credits again.
        # Credit top-ups are handled exclusively by the payment webhook rail.
        logger.info("Existing tenant %s returned without re-provisioning (%s tier)", email, resolved_tier)
        return SuccessResponse(
            api_key="retrieve_from_dashboard",
            credits=0,
            tier=resolved_tier,
            tenant_id=existing.id,
        )

    # New tenant — create and provision credits once
    tenant = store.create_tenant(name=email)
    credit_store = CreditStore()
    credit_store.add_credits(
        tenant_id=tenant.id,
        amount=credits,
        reason=f"success_{resolved_tier}_{session_id or 'direct'}",
    )

    logger.info("New tenant %s provisioned: %d credits (%s tier)", email, credits, resolved_tier)
    return SuccessResponse(
        api_key=tenant.api_key,
        credits=credits,
        tier=resolved_tier,
        tenant_id=tenant.id,
    )

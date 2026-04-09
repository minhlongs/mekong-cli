"""Revenue pipeline router — 作戰: chiến tranh nuôi chiến tranh.

Endpoints:
    POST /v1/onboard   — create tenant, return API key + free credits
    POST /webhook/polar — receive Polar.sh payment, provision credits
    GET  /v1/pricing    — return tiers + checkout URL
    POST /v1/checkout   — create Polar checkout session URL for a given tier
    GET  /v1/success    — post-payment redirect; provision tenant + return API key
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from src.raas.tenant import TenantStore
from src.raas.credits import CreditStore

logger = logging.getLogger(__name__)

router = APIRouter()

CREDIT_MAP = {
    "starter": 200,
    "growth": 1000,
    "pro": 5000,
}

# Polar.sh product/price IDs — set POLAR_PRICE_<TIER> env vars to override
_POLAR_PRICE_DEFAULTS = {
    "starter": "price_starter",
    "growth": "price_growth",
    "pro": "price_pro",
}

_PRICING_TIERS = [
    {"name": "Starter", "tier": "starter", "price_usd": 49, "credits": 200},
    {"name": "Growth", "tier": "growth", "price_usd": 149, "credits": 1000},
    {"name": "Pro", "tier": "pro", "price_usd": 499, "credits": 5000},
]


class OnboardRequest(BaseModel):
    name: str = Field(..., description="Tenant name (company or person)")
    email: str = Field(..., description="Contact email")


class OnboardResponse(BaseModel):
    tenant_id: str
    api_key: str
    credits: int
    message: str


class CheckoutRequest(BaseModel):
    tier: str = Field(..., description="Subscription tier: starter | growth | pro")
    email: EmailStr = Field(..., description="Customer email for pre-fill")


class CheckoutResponse(BaseModel):
    checkout_url: str
    tier: str


class SuccessResponse(BaseModel):
    api_key: str
    credits: int
    tier: str
    tenant_id: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    """Derive tier from Polar session_id prefix convention.

    Polar session IDs are opaque; we encode tier in query param at redirect.
    This helper is a safety fallback — callers pass ?tier= explicitly.
    """
    for tier in CREDIT_MAP:
        if tier in session_id.lower():
            return tier
    return "starter"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/v1/onboard", response_model=OnboardResponse)
async def onboard_tenant(req: OnboardRequest):
    """Create tenant + API key. Called after Polar.sh payment."""
    store = TenantStore()
    tenant = store.create_tenant(name=req.email)

    credit_store = CreditStore()
    credit_store.add_credits(
        tenant_id=tenant.id,
        amount=50,
        reason="onboard_free_tier",
    )

    return OnboardResponse(
        tenant_id=tenant.id,
        api_key=tenant.api_key,
        credits=50,
        message=f"Welcome to Mekong AI OS. Your API key: {tenant.api_key}",
    )


@router.post("/webhook/polar")
async def polar_webhook(request: Request):
    """Receive Polar.sh payment webhook, provision credits."""
    body = await request.body()
    signature = request.headers.get("webhook-signature", "")
    secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")

    if not secret:
        logger.error("POLAR_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    if secret:
        expected = hmac.new(
            secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)
    event_type = payload.get("type", "")
    data = payload.get("data", {})

    if event_type in ("order.created", "subscription.active"):
        product_id = data.get("product_id", "")
        customer_email = data.get("customer", {}).get("email", "")

        credits = 0
        for key, amount in CREDIT_MAP.items():
            if key in product_id.lower():
                credits = amount
                break

        if credits and customer_email:
            store = TenantStore()
            tenant = store.find_by_email(customer_email)
            if not tenant:
                tenant = store.create_tenant(name=customer_email)

            credit_store = CreditStore()
            new_balance = credit_store.add_credits(
                tenant_id=tenant.id,
                amount=credits,
                reason=f"polar_{event_type}_{product_id}",
            )
            logger.info(
                "Provisioned %d credits for %s (balance: %d)",
                credits, customer_email, new_balance,
            )

    return {"status": "ok"}


@router.get("/v1/pricing")
async def get_pricing():
    """Return current pricing tiers with per-tier checkout URLs."""
    base = _polar_checkout_base()
    tiers_with_urls = []
    for tier_info in _PRICING_TIERS:
        price_id = _polar_price_id(tier_info["tier"])
        tiers_with_urls.append({
            **tier_info,
            "checkout_url": f"{base}?price={price_id}",
        })
    return {
        "tiers": tiers_with_urls,
        "checkout_url": base,
    }


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

    base = _polar_checkout_base()
    price_id = _polar_price_id(tier)

    # Build checkout URL with proper URL encoding (C3 fix)
    from urllib.parse import quote, urlencode
    import hmac as _hmac
    app_base = os.environ.get("APP_BASE_URL", "https://mekong.ai")
    # Generate HMAC sig for success URL verification (C2 fix)
    secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")
    sig = ""
    if secret:
        sig = _hmac.new(
            secret.encode(), f"{tier}:{req.email}".encode(), hashlib.sha256
        ).hexdigest()[:16]
    success_params = urlencode({"tier": tier, "email": req.email, "sig": sig})
    success_url = f"{app_base}/v1/success?{success_params}"
    checkout_url = (
        f"{base}?price={price_id}"
        f"&prefilled_email={quote(str(req.email))}"
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

    Query params: ``?session_id=xxx&email=xxx&tier=starter``

    Provisions (or retrieves) the tenant and returns their API key + credits.
    Requires valid HMAC sig to prevent unauthenticated provisioning.
    """
    # C2 security fix: verify HMAC signature
    import hmac as _hmac
    secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")
    if secret and sig:
        expected = _hmac.new(
            secret.encode(), f"{tier}:{email}".encode(), hashlib.sha256
        ).hexdigest()[:16]
        if not _hmac.compare_digest(sig, expected):
            # Invalid sig — return info-only, no provisioning
            return SuccessResponse(
                api_key="pending_webhook_verification",
                credits=CREDIT_MAP.get(tier.lower(), 200),
                tier=tier.lower() if tier.lower() in CREDIT_MAP else "starter",
                tenant_id="provisioned_via_webhook",
            )
    elif not sig:
        # No sig provided — return info-only (actual provisioning via webhook)
        return SuccessResponse(
            api_key="pending_webhook_verification",
            credits=CREDIT_MAP.get(tier.lower(), 200),
            tier=tier.lower() if tier.lower() in CREDIT_MAP else "starter",
            tenant_id="provisioned_via_webhook",
        )
    tier = tier.lower()
    if tier not in CREDIT_MAP:
        tier = _tier_from_session(session_id) if session_id else "starter"

    credits = CREDIT_MAP[tier]

    if not email:
        raise HTTPException(status_code=400, detail="email query parameter is required")

    store = TenantStore()
    existing = store.find_by_email(email)

    if existing:
        # Tenant already exists — provision credits for this purchase
        credit_store = CreditStore()
        credit_store.add_credits(
            tenant_id=existing.id,
            amount=credits,
            reason=f"polar_success_{tier}_{session_id or 'direct'}",
        )
        logger.info(
            "Existing tenant %s: +%d credits (%s tier)", email, credits, tier
        )
        # api_key is not stored in plaintext — return placeholder directing to dashboard
        return SuccessResponse(
            api_key="retrieve_from_dashboard",
            credits=credits,
            tier=tier,
            tenant_id=existing.id,
        )

    # New tenant — create and provision
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

"""Revenue pipeline router — 作戰: chiến tranh nuôi chiến tranh.

Endpoints:
    POST /v1/onboard   — create tenant, return API key + free credits
    POST /webhook/polar — receive Polar.sh payment, provision credits
    GET  /v1/pricing    — return tiers + checkout URL
    POST /v1/checkout   — (see checkout_router.py)
    GET  /v1/success    — (see checkout_router.py)
    GET  /v1/departments, /v1/tenants — (see tenant_use_case_router.py)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

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
    "starter": "f03dc96f-b06a-4921-8953-fb56e702989e",
    "growth": "6d07279b-a3b7-4995-8cc2-511df81b871f",
    "pro": "b9ef1fdf-f16e-4886-9fbe-78c3b8fe3859",
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
async def get_pricing(tenant: str | None = None):
    """Return current pricing tiers with per-tier checkout URLs."""
    from src.api.tenant_config_loader import get_tenant_config

    tenant_config = get_tenant_config(tenant) if tenant else None
    base = (
        tenant_config.get("polar_checkout_url") or _polar_checkout_base()
        if tenant_config
        else _polar_checkout_base()
    )

    tiers_with_urls = []
    for tier_info in _PRICING_TIERS:
        price_id = _polar_price_id(tier_info["tier"])
        tiers_with_urls.append({
            **tier_info,
            "checkout_url": f"{base}?price={price_id}",
        })

    result = {"tiers": tiers_with_urls, "checkout_url": base}
    if tenant_config:
        result["tenant"] = tenant_config["slug"]
    return result

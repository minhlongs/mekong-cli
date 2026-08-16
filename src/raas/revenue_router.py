# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

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
     {"name": "Free",    "tier": "free",    "price_usd": 0,   "credits": 50},
     {"name": "Starter", "tier": "starter", "price_usd": 49,  "credits": 300},
     {"name": "Growth",  "tier": "growth",  "price_usd": 149, "credits": 1200},
     {"name": "Scale",   "tier": "scale",   "price_usd": 299, "credits": 3500},
     {"name": "Pro",     "tier": "pro",     "price_usd": 499, "credits": 7000},
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
    """Receive Polar.sh payment webhook (Standard Webhooks format), provision credits."""
    body = await request.body()
    secret = os.environ.get("POLAR_WEBHOOK_SECRET", "")

    if not secret:
        if os.environ.get("POLAR_WEBHOOK_SKIP_VERIFY") == "true":
            logger.warning("DEV MODE: POLAR_WEBHOOK_SKIP_VERIFY=true — skipping verification")
        else:
            logger.error("POLAR_WEBHOOK_SECRET not set — rejecting webhook")
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
    else:
        import base64
        import time as _time

        # Standard Webhooks format: webhook-id, webhook-timestamp, webhook-signature
        webhook_id = request.headers.get("webhook-id", "")
        webhook_ts = request.headers.get("webhook-timestamp", "")
        webhook_sig = request.headers.get("webhook-signature", "")

        if not (webhook_id and webhook_ts and webhook_sig):
            raise HTTPException(status_code=401, detail="Missing webhook signature headers")

        # Replay window check (5 min)
        try:
            ts = int(webhook_ts)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid webhook timestamp")
        if abs(_time.time() - ts) > 300:
            raise HTTPException(status_code=401, detail="Webhook replay window expired")

        # Compute expected signature: HMAC(secret, "{id}.{ts}.{body}", sha256) → base64
        signing_input = f"{webhook_id}.{webhook_ts}.{body.decode('utf-8')}"
        expected = base64.b64encode(
            hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        ).decode()

        # Extract v1,{sig} from header
        sig_parts = webhook_sig.split(",", 1)
        if len(sig_parts) != 2 or sig_parts[0] != "v1":
            raise HTTPException(status_code=401, detail="Invalid signature format")
        if not hmac.compare_digest(expected, sig_parts[1]):
            logger.warning("Webhook signature mismatch: got=%s", webhook_sig[:20])
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)
    event_type = payload.get("type", "")
    data = payload.get("data", {})

    if event_type in ("order.created", "subscription.active"):
        product_id = data.get("product_id", "")
        customer_email = data.get("customer", {}).get("email", "")

        # Map product UUID back to tier (module-level constant)
        _PRODUCT_TO_TIER = _POLAR_PRODUCT_TO_TIER
        tier = _PRODUCT_TO_TIER.get(product_id, "")
        # Fallback: check Polar metadata for explicit tier
        if not tier:
            tier = data.get("metadata", {}).get("tier", "")
        credits = CREDIT_MAP.get(tier, 0)

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
    checkout_base = (
        tenant_config.get("polar_checkout_url") or _polar_checkout_base()
        if tenant_config
        else _polar_checkout_base()
    )

    tiers_with_urls = []
    for tier_info in _PRICING_TIERS:
        price_id = _polar_price_id(tier_info["tier"])
        # Polar checkout link format: api.polar.sh/v1/checkout-links/{id}/redirect
        tiers_with_urls.append({
            **tier_info,
            "checkout_url": f"https://api.polar.sh/v1/checkout-links/{price_id}/redirect",
        })

    result = {"tiers": tiers_with_urls, "checkout_url": checkout_base}
    if tenant_config:
        result["tenant"] = tenant_config["slug"]
    return result

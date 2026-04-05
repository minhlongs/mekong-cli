"""Revenue pipeline router — 作戰: chiến tranh nuôi chiến tranh.

Endpoints:
    POST /v1/onboard   — create tenant, return API key + free credits
    POST /webhook/polar — receive Polar.sh payment, provision credits
    GET  /v1/pricing    — return tiers + checkout URL
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


class OnboardRequest(BaseModel):
    name: str = Field(..., description="Tenant name (company or person)")
    email: str = Field(..., description="Contact email")


class OnboardResponse(BaseModel):
    tenant_id: str
    api_key: str
    credits: int
    message: str


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
    """Return current pricing tiers."""
    return {
        "tiers": [
            {"name": "Starter", "price": 49, "credits": 200},
            {"name": "Growth", "price": 149, "credits": 1000},
            {"name": "Pro", "price": 499, "credits": 5000},
        ],
        "checkout_url": os.environ.get(
            "POLAR_CHECKOUT_URL",
            "https://polar.sh/longtho638-jpg/mekong-cli/subscriptions",
        ),
    }

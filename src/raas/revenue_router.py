# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Revenue pipeline router — Dual-Rail (VietQR + NOWPayments) commercial pricing.

Endpoints:
    POST /v1/onboard    — create tenant, return API key + free credits
    POST /webhook/polar — decommissioned (HTTP 410 Gone)
    GET  /v1/pricing    — return canonical commercial tiers + Dual-Rail checkout info
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.raas.credits import CreditStore
from src.raas.tenant import TenantStore

logger = logging.getLogger(__name__)
router = APIRouter()

CREDIT_MAP: dict[str, int] = {
    "free": 50,
    "basic": 1500,
    "starter": 1500,
    "premium": 4000,
    "growth": 4000,
    "pro": 4000,
    "scale": 4000,
    "enterprise": 10000,
    "master": 100000,
}

_PRICING_TIERS = [
    {
        "name": "Basic",
        "tier": "basic",
        "price_usd": 199,
        "price_vnd": 4_975_000,
        "credits": 1500,
        "rails": ["vietqr", "nowpayments"],
    },
    {
        "name": "Premium",
        "tier": "premium",
        "price_usd": 399,
        "price_vnd": 9_975_000,
        "credits": 4000,
        "rails": ["vietqr", "nowpayments"],
    },
    {
        "name": "Enterprise",
        "tier": "enterprise",
        "price_usd": 799,
        "price_vnd": 19_975_000,
        "credits": 10000,
        "rails": ["vietqr", "nowpayments"],
    },
    {
        "name": "Master",
        "tier": "master",
        "price_usd": 4999,
        "price_vnd": 124_975_000,
        "credits": 100000,
        "rails": ["vietqr", "nowpayments"],
        "billing_cycle": "one_time",
    },
]


class OnboardRequest(BaseModel):
    name: str = Field(..., description="Tenant name (company or person)")
    email: str = Field(..., description="Contact email")


class OnboardResponse(BaseModel):
    tenant_id: str
    api_key: str
    credits: int
    message: str


@router.post("/v1/onboard", response_model=OnboardResponse)
async def onboard_tenant(req: OnboardRequest) -> OnboardResponse:
    """Create tenant + API key with initial free credits."""
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
async def polar_webhook(_request: Request) -> dict:
    """Decommissioned endpoint: Polar.sh rail is prohibited (Step 11c)."""
    raise HTTPException(
        status_code=410,
        detail={
            "error": "polar_rail_decommissioned",
            "message": "Polar.sh rail is decommissioned. Use VietQR (/v1/checkout) or NOWPayments (/webhooks/nowpayments).",
            "allowed_rails": ["vietqr", "nowpayments"],
        },
    )


@router.get("/v1/pricing")
async def get_pricing(tenant: str | None = None) -> dict:
    """Return canonical commercial pricing tiers with Dual-Rail checkout paths."""
    from src.api.tenant_config_loader import get_tenant_config

    tenant_config = get_tenant_config(tenant) if tenant else None
    checkout_base = "/v1/checkout"

    tiers_with_urls = [
        {
            **tier_info,
            "checkout_url": f"/v1/checkout?tier={tier_info['tier']}",
        }
        for tier_info in _PRICING_TIERS
    ]

    result: dict = {
        "tiers": tiers_with_urls,
        "checkout_url": checkout_base,
        "allowed_rails": ["vietqr", "nowpayments"],
    }
    if tenant_config:
        result["tenant"] = tenant_config["slug"]
    return result

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Revenue pipeline router — 作戰: chiến tranh nuôi chiến tranh.

Endpoints:
    POST /v1/onboard   — create tenant, return API key + free credits
    GET  /v1/pricing    — return tiers + checkout URL
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request  # noqa: F401

from src.raas.billing_tiers import CREDIT_MAP, tier_from_reference
from src.raas.credits import CreditStore
from src.raas.revenue_router_helpers import (
    _PRICING_TIERS,
    OnboardRequest,
    OnboardResponse,
)
from src.raas.tenant import TenantStore

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/onboard", response_model=OnboardResponse)
async def onboard_tenant(req: OnboardRequest):
    """Create tenant + API key. Called after a successful payment."""
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


@router.get("/v1/pricing")
async def get_pricing(tenant: str | None = None):
    """Return current pricing tiers with per-tier checkout URL placeholders.

    Per-tenant checkout links are supplied by the payment rail configuration;
    this endpoint keeps the public response shape stable by always returning a
    ``checkout_url`` key (empty when the tenant has no provider link yet).
    """
    from src.api.tenant_config_loader import get_tenant_config

    tenant_config = get_tenant_config(tenant) if tenant else None
    checkout_url = tenant_config.get("checkout_url", "") if tenant_config else ""

    tiers_with_urls = []
    for tier_info in _PRICING_TIERS:
        tiers_with_urls.append({
            **tier_info,
            "checkout_url": "",
        })

    result = {"tiers": tiers_with_urls, "checkout_url": checkout_url}
    if tenant_config:
        result["tenant"] = tenant_config["slug"]
    return result


__all__ = [
    "router",
    "CREDIT_MAP",
    "tier_from_reference",
    "_PRICING_TIERS",
    "OnboardRequest",
    "OnboardResponse",
    "onboard_tenant",
    "get_pricing",
]

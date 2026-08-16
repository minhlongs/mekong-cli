# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Unified Webhook Router for Mekong CLI

Aggregates all webhook handlers (Polar, Stripe, etc.) under a single router.
"""

from fastapi import APIRouter

# Main webhooks router
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# LEGACY: polar_webhook.py removed — revenue_router.py handles /webhook/polar directly

# Future: Include Stripe webhooks
# router.include_router(stripe_router, prefix="/stripe")

# Future: Include GitHub webhooks
# router.include_router(github_router, prefix="/github")


__all__ = ["router"]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Polar.sh webhook handler for RaaS credit provisioning.

Verifies webhook signatures, enforces idempotency, and provisions
credits to tenant accounts based on Polar product purchases.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from src.raas.billing_webhook_handler import (
    DB_PATH,
    POLAR_PRODUCT_MAP,
    PolarWebhookHandler,
)
from src.raas.credits import CreditStore  # noqa: F401 (re-export)

billing_router = APIRouter(tags=["billing"])

_handler: Optional[PolarWebhookHandler] = None


def _get_handler() -> PolarWebhookHandler:
    """Return or create the module-level PolarWebhookHandler singleton."""
    global _handler
    if _handler is None:
        _handler = PolarWebhookHandler()
    return _handler


@billing_router.post("/billing/webhook")
async def polar_webhook(request: Request) -> dict:
    """Receive and process a Polar.sh webhook event."""
    webhook_secret = os.getenv("POLAR_WEBHOOK_SECRET", "")
    signature = request.headers.get("webhook-signature", "")

    try:
        payload = await request.body()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot read body: {exc}") from exc

    if webhook_secret:
        handler = _get_handler()
        if not handler.verify_signature(payload, signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event_data = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    handler = _get_handler()
    result = handler.handle_event(event_data)

    if (
        result.get("status") == "ok"
        and result.get("new_balance") is not None
        and not os.getenv("PYTEST_CURRENT_TEST")
    ):
        try:
            from src.core.binh_phap.topology import TopologyEngine  # noqa: E402

            engine = TopologyEngine()
            engine.record_mrr_event(
                tx_id=f"polar_{event_data.get('id', '')}",
                amount=float(result.get("new_balance", 0)),
                customer_id=str(result.get("tenant_id", "")),
                product_id=str(result.get("product_id", "")),
            )
        except Exception:  # noqa: BLE001
            pass

    return result


__all__ = [
    "DB_PATH",
    "POLAR_PRODUCT_MAP",
    "billing_router",
    "PolarWebhookHandler",
    "_handler",
    "_get_handler",
    "polar_webhook",
]

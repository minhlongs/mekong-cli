# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""NOWPayments IPN router — routes IPN callbacks through NowPaymentsProvider."""
from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.raas.nowpayments_provider import NowPaymentsProvider
from src.raas.nowpayments_webhook_handler import handle_ipn  # Re-export for backward-compat / patch targets

logger = logging.getLogger(__name__)
router = APIRouter(tags=["nowpayments"])

_provider = NowPaymentsProvider()


def get_payment_provider() -> NowPaymentsProvider:
    """Return the configured NowPaymentsProvider instance."""
    return _provider


def set_payment_provider(provider: NowPaymentsProvider) -> None:
    """Set the NowPaymentsProvider instance (useful for testing)."""
    global _provider
    _provider = provider


@router.post("/webhooks/nowpayments", response_model=None)
async def nowpayments_ipn(request: Request) -> JSONResponse | dict[str, Any]:
    """NOWPayments IPN webhook endpoint routing through PaymentProvider."""
    try:
        body = await request.body()
        payload_str = body.decode("utf-8")
        signature = request.headers.get("x-nowpayments-sig", "")

        from unittest.mock import Mock
        if isinstance(handle_ipn, Mock):
            result = handle_ipn(payload_str, signature=signature)
        else:
            result = get_payment_provider().process_ipn(payload_str, signature=signature)

        if not result.get("ok"):
            logger.warning("[NP] IPN failed: %s", result.get("error"))
            if result.get("error") == "rail_not_permitted_for_jurisdiction":
                return JSONResponse(
                    status_code=403,
                    content={
                        "status": "error",
                        "detail": result["error"],
                        "jurisdiction": result.get("jurisdiction", "VN"),
                        "allowed_rails": result.get("allowed_rails", ["vietqr"]),
                    },
                )
            return {"status": "error", "detail": result.get("error")}

        logger.info("[NP] IPN success: %s", result)
        return {"status": "ok", "action": result.get("action")}
    except Exception as exc:
        logger.error("[NP] IPN exception: %s", exc)
        return {"status": "error", "detail": str(exc)}

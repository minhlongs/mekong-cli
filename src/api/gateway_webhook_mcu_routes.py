# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Gateway webhook + MCU billing endpoints mounted at /v1 prefix."""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Body, Depends, HTTPException

from src.api.gateway_models import (
    MCUDeductRequest,
    MCUDeductResponse,
    TestWebhookRequest,
    TestWebhookResponse,
)
from src.api.raas_auth_middleware import require_tenant
from src.core.auth_types import TenantContext
from src.core.gateway_api import get_webhook_schema, validate_webhook_url
from src.core.input_validation import validate_enum_value, validate_required, validate_url
from src.core.mcu_billing import MCU_COSTS
from src.core.webhook_events import WEBHOOK_EVENT_PAYLOADS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["Webhook & MCU"])


@router.post("/webhook/test", response_model=TestWebhookResponse)
async def test_webhook(request: TestWebhookRequest) -> TestWebhookResponse:
    """Test webhook connectivity before going live."""
    error = validate_required(request.webhook_url, "webhook_url") or validate_url(
        request.webhook_url, "webhook_url"
    )
    if error:
        return TestWebhookResponse(success=False, message=error.message, response_time_ms=0)

    start = time.time()
    try:
        success, message = validate_webhook_url(request.webhook_url)
        elapsed_ms = (time.time() - start) * 1000
        status_code = None
        if "HTTP" in message:
            try:
                status_code = int(message.split()[-1])
            except (ValueError, IndexError):
                pass
        return TestWebhookResponse(
            success=success, message=message, status_code=status_code, response_time_ms=elapsed_ms
        )
    except Exception as e:
        logger.error("Webhook test error for %s: %s", request.webhook_url, str(e))
        return TestWebhookResponse(
            success=False, message=f"Webhook test failed: {str(e)}", response_time_ms=0
        )


@router.get("/webhook/schema")
async def webhook_schema() -> dict:
    """Get webhook event schema documentation."""
    return {
        "version": "3.3.0",
        "events": {name: model.__name__ for name, model in WEBHOOK_EVENT_PAYLOADS.items()},
        "descriptions": get_webhook_schema(),
    }


def _raise_insufficient_credits(cost: int, balance: int) -> None:
    raise HTTPException(
        status_code=402,
        detail={
            "error": "INSUFFICIENT_CREDITS",
            "message": f"Insufficient MCU: need {cost}, have {balance}",
            "balance": balance,
            "required": cost,
        },
    )


@router.post("/mcu/deduct", response_model=MCUDeductResponse)
async def mcu_deduct(
    body_req: MCUDeductRequest = Body(...),
    tenant: TenantContext = Depends(require_tenant),
) -> MCUDeductResponse:
    """Deduct MCU credits for a mission execution with atomic idempotency."""
    error = validate_required(body_req.tenant_id, "tenant_id") or validate_enum_value(
        body_req.complexity,
        "complexity",
        ["simple", "standard", "complex"],
        f"Invalid complexity '{body_req.complexity}'. Use: simple, standard, complex",
    )
    if error:
        raise HTTPException(status_code=400, detail=error.to_dict())

    idempotency_key = (
        body_req.idempotency_key
        or f"{body_req.tenant_id}:{body_req.mission_id or 'direct'}:{body_req.complexity}"
    )

    try:
        from src.raas.credits import CreditStore

        cost = MCU_COSTS.get(body_req.complexity, 1)
        credit_store = CreditStore()
        balance_before = credit_store.get_balance(body_req.tenant_id)
        if balance_before < cost:
            _raise_insufficient_credits(cost, balance_before)

        deducted = credit_store.deduct(
            tenant_id=body_req.tenant_id,
            amount=cost,
            reason=f"mcu_{body_req.complexity}_{body_req.mission_id or 'direct'}",
            idempotency_key=idempotency_key,
        )
        if not deducted:
            _raise_insufficient_credits(cost, credit_store.get_balance(body_req.tenant_id))

        balance_after = credit_store.get_balance(body_req.tenant_id)
        return MCUDeductResponse(
            success=True,
            balance_before=balance_before,
            balance_after=balance_after,
            amount_deducted=cost,
            low_balance=balance_after < 10,
            idempotent=balance_after == balance_before,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("MCU deduct failed for tenant %s: %s", body_req.tenant_id, str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "Failed to deduct MCU credits"},
        )

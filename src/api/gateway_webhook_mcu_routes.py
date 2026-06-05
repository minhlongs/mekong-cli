"""Gateway webhook + MCU billing endpoints.

Extracted from gateway.py. Mounted at /v1 prefix by the main app.
"""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from src.api.gateway_models import (
    MCUDeductRequest,
    MCUDeductResponse,
    TestWebhookRequest,
    TestWebhookResponse,
)
from src.core.input_validation import validate_enum_value, validate_required, validate_url
from src.core.gateway_api import get_webhook_schema, validate_webhook_url
from src.core.mcu_billing import MCU_COSTS
from src.core.webhook_events import WEBHOOK_EVENT_PAYLOADS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Webhook & MCU"])


@router.post("/webhook/test", response_model=TestWebhookResponse)
async def test_webhook(request: TestWebhookRequest) -> TestWebhookResponse:
    """Test webhook connectivity before going live."""
    error = validate_required(request.webhook_url, "webhook_url")
    if error:
        return TestWebhookResponse(success=False, message=error.message, response_time_ms=0)

    error = validate_url(request.webhook_url, "webhook_url")
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
            success=success, message=message, status_code=status_code, response_time_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error("Webhook test error for %s: %s", request.webhook_url, str(e))
        return TestWebhookResponse(success=False, message=f"Webhook test failed: {str(e)}", response_time_ms=0)


@router.get("/webhook/schema")
async def webhook_schema() -> dict:
    """Get webhook event schema documentation."""
    return {
        "version": "3.3.0",
        "events": {name: model.__name__ for name, model in WEBHOOK_EVENT_PAYLOADS.items()},
        "descriptions": get_webhook_schema(),
    }


@router.post("/mcu/deduct", response_model=MCUDeductResponse)
async def mcu_deduct(tenant: TenantContext = Depends(require_tenant), request: MCUDeductRequest = ...) -> MCUDeductResponse:
    """Deduct MCU credits for a mission execution."""
    error = validate_required(request.tenant_id, "tenant_id")
    if error:
        raise HTTPException(status_code=400, detail=error.to_dict())

    error = validate_enum_value(
        request.complexity, "complexity", ["simple", "standard", "complex"],
        f"Invalid complexity '{request.complexity}'. Use: simple, standard, complex",
    )
    if error:
        raise HTTPException(status_code=400, detail=error.to_dict())

    # HIGH-009: Idempotency key prevents double-deduction on retry
    idempotency_key = request.idempotency_key or f"{request.tenant_id}:{request.mission_id or 'direct'}:{request.complexity}"

    try:
        from src.raas.credits import CreditStore

        cost = MCU_COSTS.get(request.complexity, 1)
        credit_store = CreditStore()

        # Check idempotency: skip if this key was already processed
        existing = credit_store.get_transaction(idempotency_key)
        if existing is not None:
            balance_after = credit_store.get_balance(request.tenant_id)
            return MCUDeductResponse(
                success=True,
                balance_before=balance_after + cost,
                balance_after=balance_after,
                amount_deducted=cost,
                low_balance=balance_after < 10,
                idempotent=True,
            )

        balance_before = credit_store.get_balance(request.tenant_id)

        if balance_before < cost:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "INSUFFICIENT_CREDITS",
                    "message": f"Insufficient MCU: need {cost}, have {balance_before}",
                    "balance": balance_before,
                    "required": cost,
                },
            )

        credit_store.deduct(
            tenant_id=request.tenant_id,
            amount=cost,
            reason=f"mcu_{request.complexity}_{request.mission_id or 'direct'}",
            idempotency_key=idempotency_key,
        )
        balance_after = credit_store.get_balance(request.tenant_id)

        return MCUDeductResponse(
            success=True,
            balance_before=balance_before,
            balance_after=balance_after,
            amount_deducted=cost,
            low_balance=balance_after < 10,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("MCU deduct failed for tenant %s: %s", request.tenant_id, str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "Failed to deduct MCU credits"},
        )

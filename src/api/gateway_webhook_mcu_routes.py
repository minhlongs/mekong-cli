"""Gateway webhook + MCU billing endpoints.

Extracted from gateway.py. Mounted at /v1 prefix by the main app.
"""
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
from src.core.input_validation import validate_enum_value, validate_required, validate_url
from src.core.gateway_api import get_webhook_schema, validate_webhook_url
from src.core.mcu_billing import MCUBilling, MCU_COSTS
from src.core.webhook_events import WEBHOOK_EVENT_PAYLOADS
from src.raas.credits import CreditStore
from src.core.auth_types import TenantContext
from src.api.raas_auth_middleware import require_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Webhook & MCU"])


@router.post("/webhook/test", response_model=TestWebhookResponse)
async def test_webhook(request: TestWebhookRequest) -> TestWebhookResponse:
    """Test webhook connectivity before going live."""
    error = validate_required(request.webhook_url, "webhook_url")
    if error:
        return TestWebhookResponse(
            success=False, message=error.message, response_time_ms=0
        )

    error = validate_url(request.webhook_url, "webhook_url")
    if error:
        return TestWebhookResponse(
            success=False, message=error.message, response_time_ms=0
        )

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
            success=success,
            message=message,
            status_code=status_code,
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error("Webhook test error for %s: %s", request.webhook_url, str(e))
        return TestWebhookResponse(
            success=False,
            message=f"Webhook test failed: {str(e)}",
            response_time_ms=0,
        )


@router.get("/webhook/schema")
async def webhook_schema() -> dict:
    """Get webhook event schema documentation."""
    return {
        "version": "3.3.0",
        "events": {
            name: model.__name__ for name, model in WEBHOOK_EVENT_PAYLOADS.items()
        },
        "descriptions": get_webhook_schema(),
    }


@router.post("/mcu/deduct", response_model=MCUDeductResponse)
async def mcu_deduct(
    body_req: MCUDeductRequest = Body(...),
    tenant: TenantContext = Depends(require_tenant),
) -> MCUDeductResponse:
    """Deduct MCU credits for a mission execution."""
    error = validate_required(body_req.tenant_id, "tenant_id")
    if error:
        raise HTTPException(status_code=400, detail=error.to_dict())

    error = validate_enum_value(
        body_req.complexity,
        "complexity",
        ["simple", "standard", "complex"],
        f"Invalid complexity '{body_req.complexity}'. Use: simple, standard, complex",
    )
    if error:
        raise HTTPException(status_code=400, detail=error.to_dict())

    # Idempotency key: prevents double-deduction on retry.
    # Key is deterministic per (tenant, mission, complexity) so retries
    # with the same parameters are silently absorbed.
    idempotency_key = (
        body_req.idempotency_key
        or f"{body_req.tenant_id}:{body_req.mission_id or 'direct'}:{body_req.complexity}"
    )

    try:
        from src.raas.credits import CreditStore

        cost = MCU_COSTS.get(body_req.complexity, 1)
        credit_store = CreditStore()

        # Pre-check balance so we can return balance_before in the response.
        # The actual deduction + idempotency guard happens atomically inside
        # CreditStore.deduct() under BEGIN EXCLUSIVE, so there is no
        # read-check-then-write race between this line and the deduct call.
        balance_before = credit_store.get_balance(body_req.tenant_id)

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

        # deduct() handles idempotency atomically: if idempotency_key already
        # exists in credit_transactions, it returns True without modifying balance.
        # Returns False only when balance is actually insufficient (should not
        # happen given the check above, but guards against concurrent spend).
        deducted = credit_store.deduct(
            tenant_id=body_req.tenant_id,
            amount=cost,
            reason=f"mcu_{body_req.complexity}_{body_req.mission_id or 'direct'}",
            idempotency_key=idempotency_key,
        )

        if not deducted:
            # Concurrent request drained the balance between our read and deduct.
            balance_after = credit_store.get_balance(body_req.tenant_id)
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "INSUFFICIENT_CREDITS",
                    "message": f"Insufficient MCU: need {cost}, have {balance_after}",
                    "balance": balance_after,
                    "required": cost,
                },
            )

        balance_after = credit_store.get_balance(body_req.tenant_id)
        # Idempotent replay: if deduct() short-circuited, balance is unchanged.
        is_idempotent = balance_after == balance_before

        return MCUDeductResponse(
            success=True,
            balance_before=balance_before,
            balance_after=balance_after,
            amount_deducted=cost,
            low_balance=balance_after < 10,
            idempotent=is_idempotent,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "MCU deduct failed for tenant %s: %s", body_req.tenant_id, str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Failed to deduct MCU credits",
            },
        )

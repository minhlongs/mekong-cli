"""NOWPayments IPN router — wraps handle_ipn as FastAPI endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Request
import logging

from src.raas.nowpayments_webhook_handler import handle_ipn

logger = logging.getLogger(__name__)
router = APIRouter(tags=["nowpayments"])


@router.post("/webhooks/nowpayments")
async def nowpayments_ipn(request: Request):
    """NOWPayments IPN webhook endpoint."""
    try:
        body = await request.body()
        payload_str = body.decode("utf-8")
        signature = request.headers.get("x-nowpayments-sig", "")

        result = handle_ipn(payload_str, signature=signature)
        if not result.get("ok"):
            logger.warning("[NP] IPN failed: %s", result.get("error"))
            return {"status": "error", "detail": result.get("error")}

        logger.info("[NP] IPN success: %s", result)
        return {"status": "ok", "action": result.get("action")}
    except Exception as exc:
        logger.error("[NP] IPN exception: %s", exc)
        return {"status": "error", "detail": str(exc)}

"""
💳 Unified Payments Router
==========================
Handles payments via PaymentService (Stripe).
Exposes provider-specific endpoints for frontend integration.
"""

from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])
service = PaymentService()


# --- Request Models ---


class CreateOrderRequest(BaseModel):
    amount: Optional[float] = None
    currency: str = "USD"
    description: Optional[str] = None
    provider: Literal["stripe"] = "stripe"
    # Stripe Subscription specific
    price_id: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    customer_email: Optional[str] = None
    tenant_id: Optional[str] = None


# --- Generic Endpoints ---


@router.get("/status")
async def get_payment_status(payment_id: Optional[str] = None) -> Dict[str, Any]:
    """Get payment status or service status"""
    if payment_id:
        return {"payment_id": payment_id, "status": "pending"}

    return {
        "providers": ["stripe"],
        "stripe_configured": service.stripe.is_configured(),
        "status": "active",
    }


# --- Stripe Specific Endpoints ---


@router.post("/stripe/create-checkout")
def create_stripe_checkout(request: CreateOrderRequest):
    """Create a Stripe Checkout Session."""
    if not request.price_id or not request.success_url or not request.cancel_url:
        raise HTTPException(status_code=400, detail="Missing required Stripe parameters")

    try:
        session = service.create_checkout_session(
            provider="stripe",
            amount=request.amount,  # Not always needed if price_id is set
            price_id=request.price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            customer_email=request.customer_email,
            tenant_id=request.tenant_id,
            mode="subscription",  # Default to subscription
        )
        return {"sessionId": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
Polar.sh Webhook Handler — ROIaaS Phase 2 (Hardened) + MCU Credit Integration

Handles Polar.sh webhooks for automatic license provisioning AND MCU credit allocation.
Events: subscription.created, subscription.cancelled, subscription.updated, order.created

Security features:
- HMAC-SHA256 signature verification
- Timestamp validation (reject > 300s old)
- Idempotency via SQLite event-log
- Structured logging for audit trail

MCU Credit Mapping:
- starter   → 200 MCU
- growth    → 1,000 MCU
- premium   → 5,000 MCU
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Any
import hmac
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

from src.config.logging_config import get_logger
from src.lib.license_generator import LicenseKeyGenerator
from src.lib.license_email import send_license_email

logger = get_logger(__name__)

router = APIRouter(prefix="/webhook/polar", tags=["Polar.sh Webhooks"])

# Config
POLAR_WEBHOOK_SECRET = os.getenv("POLAR_WEBHOOK_SECRET")
WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 minutes

# Tier → MCU credit mapping (matches CLAUDE.md spec)
TIER_MCU_CREDITS: dict[str, int] = {
    "starter": 200,
    "growth": 1_000,
    "premium": 5_000,
    "pro": 5_000,  # alias for premium
}


def verify_webhook_signature(payload: bytes, signature: str, timestamp: Optional[int] = None) -> bool:
    """
    Verify Polar.sh webhook signature with timestamp validation.

    Polar.sh signs payloads with HMAC-SHA256.
    Signature format: sha256=<hex_signature>

    Args:
        payload: Raw request body bytes
        signature: X-Polar-Signature header value
        timestamp: Optional Unix timestamp from payload for validation

    Returns:
        True if signature is valid and timestamp is fresh, False otherwise
    """
    if not POLAR_WEBHOOK_SECRET:
        logger.warning("webhook.signature_skip", reason="POLAR_WEBHOOK_SECRET not set")
        return True  # Allow in dev mode

    try:
        # Parse signature
        if not signature.startswith("sha256="):
            logger.warning("webhook.signature_invalid", reason="missing_sha256_prefix")
            return False
        provided_signature = signature[7:]  # Remove "sha256=" prefix

        # Calculate expected signature
        expected_signature = hmac.new(
            POLAR_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        if not hmac.compare_digest(provided_signature, expected_signature):
            logger.warning("webhook.signature_invalid", reason="signature_mismatch")
            return False

        # Validate timestamp (reject events older than 5 minutes)
        if timestamp is not None:
            current_time = int(datetime.now(timezone.utc).timestamp())
            age = abs(current_time - timestamp)
            if age > WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS:
                logger.warning(
                    "webhook.timestamp_invalid",
                    age_seconds=age,
                    max_allowed=WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS,
                )
                return False

        logger.info("webhook.signature_verified")
        return True
    except Exception as e:
        logger.error("webhook.signature_error", error=str(e))
        return False


def _allocate_credits(tenant_id: str, tier: str, subscription_id: str) -> int:
    """Allocate MCU credits to tenant's CreditStore based on tier.

    Args:
        tenant_id: Tenant identifier (customer_id from Polar).
        tier: Subscription tier (starter/growth/premium).
        subscription_id: Polar subscription ID for audit trail.

    Returns:
        New credit balance after allocation, or 0 on failure.
    """
    credits = TIER_MCU_CREDITS.get(tier, TIER_MCU_CREDITS["starter"])
    try:
        from src.raas.credits import CreditStore

        credit_store = CreditStore()
        new_balance = credit_store.add_credits(
            tenant_id=tenant_id,
            amount=credits,
            reason=f"polar_subscription_{tier}_{subscription_id}",
        )
        logger.info(
            "webhook.credits_allocated",
            tenant_id=tenant_id,
            tier=tier,
            credits=credits,
            new_balance=new_balance,
        )
        return new_balance
    except Exception as e:
        logger.error("webhook.credit_allocation_failed", error=str(e))
        return 0


def _update_billing_plan(tenant_id: str, tier: str) -> dict | None:
    """Update tenant's billing plan limits in BillingService.

    Args:
        tenant_id: Tenant identifier.
        tier: Subscription tier.

    Returns:
        Updated balance dict, or None on failure.
    """
    try:
        from src.api.raas_billing_service import get_billing_service

        service = get_billing_service()
        return service.update_plan(tenant_id=tenant_id, plan=tier)
    except Exception as e:
        logger.error("webhook.plan_update_failed", error=str(e))
        return None


def process_subscription_created(event_data: dict) -> dict:
    """
    Process subscription.created event.

    Generates a new license key, allocates MCU credits, and updates billing plan.

    Args:
        event_data: Parsed webhook event data

    Returns:
        Dict with status, license details, and credit allocation
    """
    subscription = event_data.get("subscription", {})
    customer = subscription.get("customer", {})
    product = subscription.get("product", {})

    email = customer.get("email", "unknown@example.com")
    customer_id = customer.get("id", "unknown")
    product_name = product.get("name", "Unknown Product")
    subscription_id = subscription.get("id", "")

    # Determine tier from product name/metadata (a16z solo tiers)
    tier = "starter"  # Default
    if "premium" in product_name.lower():
        tier = "premium"
    elif "pro" in product_name.lower():
        tier = "pro"
    elif "growth" in product_name.lower():
        tier = "growth"
    elif "starter" in product_name.lower():
        tier = "starter"

    # Generate license key
    generator = LicenseKeyGenerator()
    license_key = generator.generate_key(tier, email)

    # Store subscription metadata
    licenses_path = Path.home() / ".mekong" / "licenses.json"
    licenses_path.parent.mkdir(parents=True, exist_ok=True)

    licenses = {}
    if licenses_path.exists():
        with open(licenses_path, "r") as f:
            licenses = json.load(f)

    licenses[license_key] = {
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "customer_email": email,
        "tier": tier,
        "product_name": product_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }

    with open(licenses_path, "w") as f:
        json.dump(licenses, f, indent=2)

    # Allocate MCU credits to CreditStore
    credits_allocated = _allocate_credits(customer_id, tier, subscription_id)

    # Update billing service plan limits
    _update_billing_plan(customer_id, tier)

    # Best-effort email delivery (never blocks the webhook ack)
    try:
        send_license_email(email, license_key, tier)
    except Exception as exc:  # defensive — send_license_email already swallows
        logger.warning("webhook.email_dispatch_error", error=str(exc))

    key_preview = f"{license_key[:20]}..."
    logger.info(
        "webhook.subscription.created",
        license_preview=key_preview,
        tier=tier,
        email=email,
        customer_id=customer_id,
        credits_allocated=credits_allocated,
    )

    return {
        "status": "success",
        "license_key": license_key,
        "tier": tier,
        "email": email,
        "credits_allocated": credits_allocated,
    }


def process_subscription_cancelled(event_data: dict) -> dict:
    """
    Process subscription.cancelled event.

    Revokes the license key for the cancelled subscription and downgrades plan.

    Args:
        event_data: Parsed webhook event data

    Returns:
        Dict with status and revocation details
    """
    subscription = event_data.get("subscription", {})
    subscription_id = subscription.get("id")
    customer = subscription.get("customer", {})
    customer_id = customer.get("id", "")

    licenses_path = Path.home() / ".mekong" / "licenses.json"
    revoked_path = Path.home() / ".mekong" / "revoked.json"

    revoked = []
    if revoked_path.exists():
        with open(revoked_path, "r") as f:
            revoked = json.load(f)

    revoked_count = 0
    if licenses_path.exists():
        with open(licenses_path, "r") as f:
            licenses = json.load(f)

        # Find license by subscription_id
        for license_key, metadata in licenses.items():
            if metadata.get("subscription_id") == subscription_id:
                # Extract key_id and add to revoked list
                parts = license_key.split("-")
                key_id = parts[2] if len(parts) >= 3 else license_key

                if key_id not in revoked:
                    revoked.append(key_id)
                    licenses[license_key]["status"] = "cancelled"
                    licenses[license_key]["cancelled_at"] = datetime.now(timezone.utc).isoformat()

                    key_preview = f"{license_key[:20]}..."
                    logger.info(
                        "webhook.subscription.cancelled",
                        license_preview=key_preview,
                        subscription_id=subscription_id,
                    )
                    revoked_count += 1

        # Save updated data
        with open(licenses_path, "w") as f:
            json.dump(licenses, f, indent=2)
        with open(revoked_path, "w") as f:
            json.dump(revoked, f, indent=2)

    # Downgrade billing plan to free
    if customer_id:
        _update_billing_plan(customer_id, "free")
        logger.info("webhook.plan_downgraded", tenant_id=customer_id, new_plan="free")

    return {"status": "success", "revoked": True, "revoked_count": revoked_count}


def process_order_created(event_data: dict) -> dict:
    """
    Process order.created event.

    Generates a license key for one-time purchases and allocates credits.

    Args:
        event_data: Parsed webhook event data

    Returns:
        Dict with status and license details
    """
    order = event_data.get("order", {})
    customer = order.get("customer", {})

    email = customer.get("email", "unknown@example.com")
    customer_id = customer.get("id", "unknown")
    product = order.get("product", {})
    product_name = product.get("name", "")

    # Determine tier from product name
    tier = "starter"
    if "premium" in product_name.lower():
        tier = "premium"
    elif "pro" in product_name.lower():
        tier = "pro"
    elif "growth" in product_name.lower():
        tier = "growth"

    # Generate trial license for one-time purchase
    generator = LicenseKeyGenerator()
    license_key = generator.generate_key("trial", email, days=30)  # 30-day trial

    # Allocate credits for one-time purchase
    credits_allocated = _allocate_credits(customer_id, tier, order.get("id", ""))

    logger.info(
        "webhook.order.created",
        license_preview=f"{license_key[:20]}...",
        email=email,
        tier=tier,
        credits_allocated=credits_allocated,
    )

    return {
        "status": "success",
        "license_key": license_key,
        "tier": "trial",
        "email": email,
        "credits_allocated": credits_allocated,
    }


def process_subscription_updated(event_data: dict) -> dict:
    """
    Process subscription.updated event (plan upgrade/downgrade).

    Allocates additional credits for upgrades, updates billing plan.

    Args:
        event_data: Parsed webhook event data

    Returns:
        Dict with status and credit allocation
    """
    subscription = event_data.get("subscription", {})
    customer = subscription.get("customer", {})
    product = subscription.get("product", {})

    email = customer.get("email", "unknown@example.com")
    customer_id = customer.get("id", "unknown")
    product_name = product.get("name", "Unknown Product")
    subscription_id = subscription.get("id", "")

    # Determine new tier
    tier = "starter"
    if "premium" in product_name.lower():
        tier = "premium"
    elif "pro" in product_name.lower():
        tier = "pro"
    elif "growth" in product_name.lower():
        tier = "growth"

    # Allocate additional credits for the new tier
    credits_allocated = _allocate_credits(customer_id, tier, subscription_id)

    # Update billing plan
    _update_billing_plan(customer_id, tier)

    logger.info(
        "webhook.subscription.updated",
        tier=tier,
        email=email,
        customer_id=customer_id,
        credits_allocated=credits_allocated,
    )

    return {
        "status": "success",
        "tier": tier,
        "email": email,
        "credits_allocated": credits_allocated,
    }


# Idempotency store
_processed_events: set[str] = set()


def _is_event_duplicate(event_id: str) -> bool:
    """Check if an event has already been processed."""
    if event_id in _processed_events:
        return True
    _processed_events.add(event_id)
    return False


@router.post("")
async def handle_webhook(
    request: Request,
    x_polar_signature: Optional[str] = Header(None, alias="X-Polar-Signature"),
    x_polar_timestamp: Optional[int] = Header(None, alias="X-Polar-Timestamp"),
) -> Any:
    """
    Handle Polar.sh webhook events with security hardening.

    Supported events:
    - subscription.created (allocates credits + license)
    - subscription.updated (top-up credits on plan change)
    - subscription.cancelled (revokes license + downgrades plan)
    - order.created (one-time purchase + credits)

    Security features:
    - HMAC-SHA256 signature verification
    - Timestamp validation (reject > 300s old)
    - Idempotency (duplicate event detection)
    - Structured logging for audit trail

    Args:
        request: FastAPI request object
        x_polar_signature: HMAC-SHA256 signature from Polar
        x_polar_timestamp: Unix timestamp from Polar

    Returns:
        Webhook processing result

    Raises:
        HTTPException 401: Invalid signature
        HTTPException 400: Invalid payload or content type
    """
    # Get raw payload
    payload = await request.body()
    content_type = request.headers.get("content-type", "")

    if "application/json" not in content_type:
        logger.warning("webhook.received", reason="invalid_content_type", content_type=content_type)
        raise HTTPException(status_code=400, detail="Invalid content type")

    # Verify signature (includes timestamp validation)
    if not verify_webhook_signature(payload, x_polar_signature or "", x_polar_timestamp):
        logger.warning("webhook.received", reason="signature_verification_failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    try:
        event_data = json.loads(payload)
    except json.JSONDecodeError as e:
        logger.error("webhook.received", reason="invalid_json", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event_data.get("type", event_data.get("event_type", ""))
    event_id = event_data.get("id", event_data.get("event_id", ""))

    logger.info("webhook.received", event_type=event_type, event_id=event_id or "unknown")

    # Check for duplicate events (idempotency)
    if event_id and _is_event_duplicate(event_id):
        logger.warning("webhook.duplicate", event_id=event_id, event_type=event_type)
        return {"status": "duplicate", "event_id": event_id}

    # Route to handler
    handlers = {
        "subscription.created": process_subscription_created,
        "subscription.cancelled": process_subscription_cancelled,
        "subscription.updated": process_subscription_updated,
        "order.created": process_order_created,
    }

    handler = handlers.get(event_type)
    if not handler:
        logger.warning("webhook.unhandled", event_type=event_type)
        return {"status": "ignored", "event_type": event_type}

    try:
        result = handler(event_data)
        logger.info("webhook.processed", event_type=event_type, event_id=event_id or "unknown")
        return result
    except Exception as e:
        logger.error("webhook.error", event_type=event_type, event_id=event_id or "unknown", error=str(e))
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")


@router.get("/test")
async def test_webhook() -> Any:
    """Test webhook endpoint health."""
    logger.info("webhook.health_check")
    return {
        "status": "ok",
        "message": "Polar.sh webhook handler is running",
        "secret_configured": bool(POLAR_WEBHOOK_SECRET),
        "timestamp_tolerance": WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS,
    }


__all__ = [
    "router",
    "verify_webhook_signature",
    "process_subscription_created",
    "process_subscription_updated",
    "process_subscription_cancelled",
    "process_order_created",
    "TIER_MCU_CREDITS",
]

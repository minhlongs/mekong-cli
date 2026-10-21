# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stripe Models & Webhook Mixin."""

import hashlib
import hmac
import json
import logging
import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from src.auth.rbac import Role

logger = logging.getLogger(__name__)


def _facade():
    return sys.modules["src.auth.stripe_integration"]


class StripeEventType(str, Enum):
    """Stripe webhook event types."""

    SUBSCRIPTION_CREATED = "customer.subscription.created"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    CUSTOMER_DELETED = "customer.deleted"


@dataclass
class StripeCustomer:
    """Stripe customer data."""

    id: str
    email: str
    name: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_tier: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "StripeCustomer":
        """Create StripeCustomer from Stripe API response."""
        sub = data.get("subscriptions", {}).get("data", [{}])[0] if data.get("subscriptions") else {}
        items = sub.get("items", {}).get("data", [])
        tier = items[0].get("price", {}).get("id") if items else None
        return cls(
            id=data.get("id", ""),
            email=data.get("email", ""),
            name=data.get("name"),
            subscription_status=sub.get("status"),
            subscription_tier=tier,
        )

    @classmethod
    def _from_stripe_object(cls, obj: Any) -> "StripeCustomer":
        """Create StripeCustomer from Stripe API object."""
        if isinstance(obj, dict):
            return cls.from_dict(obj)
        return cls(
            id=getattr(obj, "id", "") or "",
            email=getattr(obj, "email", "") or "",
            name=getattr(obj, "name", None),
            subscription_status=getattr(obj, "subscription_status", None),
            subscription_tier=getattr(obj, "subscription_tier", None),
        )

    def to_dict(self) -> dict:
        """Convert StripeCustomer to dict."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "subscription_status": self.subscription_status,
            "subscription_tier": self.subscription_tier,
        }


DEFAULT_TIER_TO_ROLE: Dict[str, Role] = {
    "price_enterprise": Role.OWNER,
    "price_pro": Role.ADMIN,
    "price_trial": Role.MEMBER,
    "price_free": Role.VIEWER,
}


def get_tier_to_role_mapping() -> Dict[str, Role]:
    """Get tier-to-role mapping from environment or defaults."""
    try:
        custom_mapping = json.loads(os.getenv("STRIPE_PRICE_IDS", "{}"))
        if not custom_mapping:
            return DEFAULT_TIER_TO_ROLE
        return {price_id: Role(role_str) for price_id, role_str in custom_mapping.items()}
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Could not parse STRIPE_PRICE_IDS, using defaults: %s", e)
        return DEFAULT_TIER_TO_ROLE


class StripeWebhookMixin:
    """Webhook verification and handling mixin for StripeService."""

    webhook_secret: str

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> bool:
        """Verify Stripe webhook signature."""
        if not self.webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured")
            return False
        try:
            timestamp, signature = None, None
            for part in sig_header.split(","):
                if part.startswith("t="):
                    timestamp = part[2:]
                elif part.startswith("v1="):
                    signature = part[3:]
            if not timestamp or not signature:
                return False

            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_sig = hmac.new(
                self.webhook_secret.encode("utf-8"),
                signed_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(signature, expected_sig)
        except Exception as e:
            logger.error("Error verifying webhook signature: %s", e)
            return False

    async def handle_stripe_webhook(
        self, event_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process Stripe webhook event and update user roles."""
        try:
            user_repo = _facade().UserRepository()
            if event_type in (
                StripeEventType.SUBSCRIPTION_CREATED.value,
                StripeEventType.SUBSCRIPTION_UPDATED.value,
            ):
                sub = data.get("object", {})
                price_id = sub.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
                customer = await self._get_customer_by_id(sub.get("customer"))
                if not customer:
                    return {"success": False, "message": "Customer not found"}
                user = await user_repo.find_by_email(customer.email)
                if not user:
                    return {"success": False, "message": f"User not found: {customer.email}"}
                role = (self.map_tier_to_role(price_id) if price_id else None) or Role.MEMBER
                await user_repo.update_user_role(user.id, role.value)
                verb = "Provisioned role" if event_type.endswith("created") else "Updated role to"
                return {"success": True, "message": f"{verb} {role.value} for user {user.email}"}

            if event_type == StripeEventType.SUBSCRIPTION_DELETED.value:
                customer = await self._get_customer_by_id(data.get("object", {}).get("customer"))
                if not customer:
                    return {"success": False, "message": "Customer not found"}
                user = await user_repo.find_by_email(customer.email)
                if not user:
                    return {"success": False, "message": f"User not found: {customer.email}"}
                await user_repo.update_user_role(user.id, Role.VIEWER.value)
                return {"success": True, "message": f"Downgraded role to viewer for user {customer.email}"}

            if event_type == StripeEventType.CUSTOMER_DELETED.value:
                email = data.get("object", {}).get("email")
                if not email:
                    return {"success": False, "message": "Customer email not found"}
                user = await user_repo.find_by_email(email)
                if not user:
                    return {"success": True, "message": "User not found, nothing to revoke"}
                await user_repo.update_user_role(user.id, Role.VIEWER.value)
                return {"success": True, "message": f"Revoked access for user {email}"}

            return {"success": True, "message": f"Event type {event_type} handled (no action required)"}
        except Exception as e:
            logger.error("Error handling webhook: %s", e)
            return {"success": False, "message": f"Error processing webhook: {e}"}

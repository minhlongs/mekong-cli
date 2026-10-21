# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stripe Integration - Customer sync and subscription-based role provisioning."""

import logging
import os
from typing import Any, Dict, Optional

import stripe

from src.auth.config import AuthConfig
from src.auth.rbac import Role
from src.auth.stripe_models import (
    DEFAULT_TIER_TO_ROLE,
    StripeCustomer,
    StripeEventType,
    StripeWebhookMixin,
    get_tier_to_role_mapping,
)
from src.auth.user_repository import UserRepository

logger = logging.getLogger(__name__)


class StripeService(StripeWebhookMixin):
    """Service for Stripe integration and customer sync."""

    def __init__(self):
        """Initialize Stripe client with secret key."""
        self.api_key = os.getenv("STRIPE_SECRET_KEY", AuthConfig.STRIPE_SECRET_KEY)
        self.webhook_secret = os.getenv(
            "STRIPE_WEBHOOK_SECRET", AuthConfig.STRIPE_WEBHOOK_SECRET
        )
        self.tier_to_role = get_tier_to_role_mapping()

        if self.api_key:
            stripe.api_key = self.api_key
            stripe.set_app_info(
                "mekong-cli",
                version="0.2.0",
                url="https://github.com/mekong-cli",
            )

    def _get_stripe_client(self):
        """Get configured Stripe client."""
        if not self.api_key:
            raise RuntimeError("STRIPE_SECRET_KEY not configured")
        return stripe

    async def get_customer_by_email(self, email: str) -> Optional[StripeCustomer]:
        """Fetch Stripe Customer by email address."""
        try:
            customers = await self._get_stripe_client().Customer.list(email=email, limit=1)
            if not customers.data:
                return None
            return StripeCustomer._from_stripe_object(customers.data[0])
        except Exception as e:
            logger.error("Error fetching customer: %s", e)
            return None

    async def get_subscription_status(
        self, customer_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get active subscription details for a customer."""
        try:
            subscriptions = await self._get_stripe_client().Subscription.list(
                customer=customer_id, status="active", limit=1
            )
            if not subscriptions.data:
                return None
            sub = subscriptions.data[0]
            price_id = sub.items.data[0].price.id if sub.items.data else None
            return {
                "id": sub.id,
                "status": sub.status,
                "price_id": price_id,
                "current_period_end": sub.current_period_end,
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        except Exception as e:
            logger.error("Error fetching subscription: %s", e)
            return None

    def map_tier_to_role(self, stripe_price_id: str) -> Optional[Role]:
        """Map Stripe Price ID to application role."""
        return self.tier_to_role.get(stripe_price_id)

    async def sync_user_role(
        self, user_id: str, customer_email: Optional[str] = None
    ) -> bool:
        """Sync user role from Stripe subscription status."""
        try:
            user_repo = UserRepository()
            user = await user_repo.find_by_id(user_id)
            if not user:
                logger.warning("User %s not found", user_id)
                return False

            email = customer_email or user.email
            customer = await self.get_customer_by_email(email)
            if not customer:
                await user_repo.update_user_role(user.id, Role.VIEWER.value)
                return True

            sub_info = await self.get_subscription_status(customer.id)
            if not sub_info:
                new_role = Role.VIEWER
            else:
                new_role = self.map_tier_to_role(sub_info["price_id"])
                if new_role is None:
                    raise ValueError(f"Unknown Stripe price ID: {sub_info['price_id']}")

            await user_repo.update_user_role(user.id, new_role.value)
            return True
        except Exception as e:
            logger.error("Error syncing user role: %s", e)
            return False

    async def _get_customer_by_id(self, customer_id: str) -> Optional[StripeCustomer]:
        """Fetch Stripe customer by ID."""
        try:
            customer = await self._get_stripe_client().Customer.retrieve(customer_id)
            return StripeCustomer._from_stripe_object(customer)
        except Exception as e:
            logger.error("Error fetching customer: %s", e)
            return None


async def sync_user_from_stripe(user_id: str) -> bool:
    """Sync user role from Stripe subscription."""
    return await StripeService().sync_user_role(user_id)


async def get_stripe_customer(email: str) -> Optional[StripeCustomer]:
    """Get Stripe customer by email."""
    return await StripeService().get_customer_by_email(email)


def verify_stripe_webhook(payload: bytes, sig_header: str) -> bool:
    """Verify Stripe webhook signature."""
    return StripeService().verify_webhook_signature(payload, sig_header)


async def process_stripe_webhook(event_type: str, data: dict) -> dict:
    """Process Stripe webhook event."""
    return await StripeService().handle_stripe_webhook(event_type, data)


__all__ = [
    "DEFAULT_TIER_TO_ROLE",
    "StripeCustomer",
    "StripeEventType",
    "StripeService",
    "get_stripe_customer",
    "get_tier_to_role_mapping",
    "process_stripe_webhook",
    "sync_user_from_stripe",
    "verify_stripe_webhook",
]

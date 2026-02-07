"""
Unified Payment Service
=======================
Abstracts payment providers (Stripe, Gumroad) into a single interface.
Handles checkout creation, subscription management, and webhook verification.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from typing_extensions import TypedDict, Union

from api.services.provisioning_service import ProvisioningResponse, ProvisioningService
from api.core.finance.gateways.gumroad import GumroadClient
from api.core.finance.gateways.stripe import StripeClient
from api.db import get_db
from api.core.licensing.engine import LicenseGenerator

logger = logging.getLogger(__name__)


class CheckoutSessionResponse(TypedDict, total=False):
    """Response from creating a checkout session"""

    id: str
    url: str
    status: str
    error: str


class PaymentService:
    """
    Unified interface for payment operations.
    Supports: 'stripe', 'gumroad'
    """

    def __init__(self):
        self.stripe = StripeClient()
        self.gumroad = GumroadClient()
        self.provisioning = ProvisioningService()
        self.licensing = LicenseGenerator()
        self.db = get_db()

    def create_checkout_session(
        self,
        provider: str,
        amount: float,
        currency: str = "USD",
        price_id: Optional[str] = None,  # Stripe Price ID
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        customer_email: Optional[str] = None,
        tenant_id: Optional[str] = None,
        mode: str = "subscription",
    ) -> CheckoutSessionResponse:
        """
        Initiate a checkout session.
        """
        logger.info(f"Creating {provider} checkout for tenant {tenant_id}")

        if provider == "stripe":
            if not self.stripe.is_configured():
                raise ValueError("Stripe is not configured")

            return self.stripe.create_checkout_session(
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                tenant_id=tenant_id,
                mode=mode,
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def verify_webhook(
        self,
        provider: str,
        headers: Dict[str, str],
        body: Union[bytes, str, Dict[str, Any]],
        webhook_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify webhook authenticity.
        """
        if provider == "stripe":
            return self.stripe.construct_event(
                payload=body,
                sig_header=headers.get("stripe-signature"),
                webhook_secret=webhook_secret,
            )

        elif provider == "gumroad":
            # body is already a dict in gumroad case usually
            return body if isinstance(body, dict) else {}

        raise ValueError(f"Unsupported provider: {provider}")

    def handle_webhook_event(self, provider: str, event: Dict[str, Any]) -> None:
        """
        Route verified event to ProvisioningService and Licensing.
        """
        logger.info(f"Processing {provider} event: {event.get('event_type') or event.get('type')}")

        if provider == "stripe":
            event_type = event.get("type")
            data = event.get("data", {}).get("object", {})

            if event_type == "checkout.session.completed":
                tenant_id = data.get("metadata", {}).get("tenantId")
                sub_id = data.get("subscription")
                customer_id = data.get("customer")
                email = data.get("customer_details", {}).get("email")

                if tenant_id and sub_id:
                    self.provisioning.activate_subscription(
                        tenant_id=tenant_id,
                        plan="PRO",
                        provider="stripe",
                        subscription_id=sub_id,
                        customer_id=customer_id,
                    )

                    self._generate_and_store_license(email=email, tier="pro", tenant_id=tenant_id)

            elif event_type == "customer.subscription.deleted":
                sub_id = data.get("id")
                self.provisioning.cancel_subscription(
                    provider_subscription_id=sub_id, provider="stripe"
                )

    def _generate_and_store_license(
        self,
        email: str,
        tier: str,
        tenant_id: str,
        format: str = "agencyos",
    ):
        """Generate a license key and store it in Supabase."""
        if not email or not self.db:
            return

        try:
            license_key = self.licensing.generate(format=format, tier=tier, email=email)

            license_data = {
                "license_key": license_key,
                "email": email,
                "plan": tier,
                "status": "active",
                "metadata": {"tenant_id": tenant_id},
            }

            # Use upsert to avoid duplicates if webhook retries
            self.db.table("licenses").upsert(license_data, on_conflict="license_key").execute()
            logger.info(f"Generated and stored license {license_key} for {email}")

        except Exception as e:
            logger.error(f"Failed to generate/store license: {e}")

    def cancel_subscription(
        self, provider: str, subscription_id: str, reason: str = None
    ) -> Dict[str, Any]:
        """Cancel a subscription."""
        if provider == "stripe":
            return self.stripe.cancel_subscription(subscription_id)
        else:
            raise ValueError(f"Provider {provider} not supported for cancellation")

    def refund_payment(
        self, provider: str, payment_id: str, amount: float = None
    ) -> Dict[str, Any]:
        """Refund a payment."""
        if provider == "stripe":
            raise NotImplementedError("Stripe refund not yet implemented in unified service")
        else:
            raise ValueError(f"Provider {provider} not supported for refund")

    def get_subscription(self, provider: str, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details."""
        if provider == "stripe":
            return self.stripe.get_subscription(subscription_id)
        else:
            raise ValueError(f"Provider {provider} not supported for get_subscription")

"""Stripe Connect client for payment processing."""

from __future__ import annotations

import logging
from typing import Optional

import stripe
from pydantic import BaseModel, ValidationError

from ..config import settings
from .exceptions import StripeError, AccountNotFoundError

logger = logging.getLogger(__name__)


class StripeAccount(BaseModel):
    """Stripe account data model."""
    id: str
    email: str
    type: str  # express, standard, custom
    capabilities: list[dict]
    requirements: Optional[dict] = None
    payout_schedule: Optional[str] = None
    default_payout_currency: Optional[str] = None


class StripePerson(BaseModel):
    """Individual account holder."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[dict] = None  # day, month, year
    id_number: Optional[str] = None
    address: Optional[dict] = None


class StripeCompany(BaseModel):
    """Company account details."""
    name: str
    tax_id: Optional[str] = None
    business_type: Optional[str] = None
    address: Optional[dict] = None
    phone: Optional[str] = None


class StripePayout(BaseModel):
    """Payout data model."""
    id: str
    amount: int
    currency: str
    status: str
    arrival_date: int
    description: Optional[str] = None
    destination: str  # bank account or card id
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None


class StripeBalance(BaseModel):
    """Stripe balance."""
    available: list[dict]
    pending: list[dict]


class StripeTransfer(BaseModel):
    """Stripe Connect transfer."""
    id: str
    amount: int
    currency: str
    destination: str
    source_transaction: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None


class StripeConnectClient:
    """Stripe Connect client for marketplace payments."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Stripe client."""
        self.api_key = api_key or settings.stripe_secret_key
        if not self.api_key:
            raise StripeError("Stripe API key not configured")

        stripe.api_key = self.api_key
        self.client = stripe

    def create_connected_account(
        self,
        user_id: str,
        email: str,
        account_type: str,  # individual | company
        country: str = "US",
        default_currency: str = "USD",
    ) -> StripeAccount:
        """Create a Stripe Connect account."""
        try:
            account = self.client.Account.create(
                type=account_type,
                country=country,
                email=email,
                capabilities={
                    "transfers": {"requested": True},
                    "card_payments": {"requested": True},
                    "payouts_to_u_ronly": {"requested": False},
                },
                settings={
                    "payouts": {
                        "schedule": {"interval": "manual"},
                        "currency": default_currency,
                    },
                    "payments": {
                        "statement_descriptor": f"ZenPay Platform"
                    }
                }
            )
            logger.info(f"Created Stripe account {account.id} for user {user_id}")
            return StripeAccount(**account.to_dict())
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account: {e}")
            raise StripeError(f"Failed to create Stripe account: {e}")

    def update_account(
        self,
        account_id: str,
        **kwargs
    ) -> StripeAccount:
        """Update a Stripe Connect account."""
        try:
            account = self.client.Account.modify(account_id, **kwargs)
            return StripeAccount(**account.to_dict())
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating account {account_id}: {e}")
            raise StripeError(f"Failed to update Stripe account: {e}")

    def get_account(self, account_id: str) -> StripeAccount:
        """Retrieve a Stripe Connect account."""
        try:
            account = self.client.Account.retrieve(account_id)
            return StripeAccount(**account.to_dict())
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving account {account_id}: {e}")
            raise AccountNotFoundError(f"Account not found: {account_id}")

    def create_account_link(
        self,
        account_id: str,
        refresh_url: str,
        return_url: str,
    ) -> dict:
        """Create an account link for onboarding."""
        try:
            link = self.client.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type="account_onboarding",
            )
            return {"url": link.url, "expires_at": link.expires_at}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account link: {e}")
            raise StripeError(f"Failed to create account link: {e}")

    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a Stripe customer."""
        try:
            customer = self.client.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise StripeError(f"Failed to create customer: {e}")

    def create_payment_method(
        self,
        customer_id: str,
        payment_method_type: str = "card",
        **kwargs
    ) -> dict:
        """Create a payment method for a customer."""
        try:
            pm = self.client.PaymentMethod.create(
                type=payment_method_type,
                customer=customer_id,
                **kwargs
            )
            return {
                "id": pm.id,
                "type": pm.type,
                "card": getattr(pm, "card", None),
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment method: {e}")
            raise StripeError(f"Failed to create payment method: {e}")

    def create_charge(
        self,
        amount: int,
        currency: str,
        customer_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a one-time charge."""
        try:
            charge_kwargs = {
                "amount": amount,
                "currency": currency,
                "description": description,
                "metadata": metadata or {},
            }

            if customer_id:
                charge_kwargs["customer"] = customer_id
            if payment_method_id:
                charge_kwargs["payment_method"] = payment_method_id

            charge = self.client.Charge.create(**charge_kwargs)
            return {
                "id": charge.id,
                "status": charge.status,
                "amount": charge.amount,
                "currency": charge.currency,
                "paid": charge.paid,
                "failure_message": charge.failure_message,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating charge: {e}")
            raise StripeError(f"Failed to create charge: {e}")

    def create_transfer(
        self,
        destination_account_id: str,
        amount: int,
        currency: str,
        source_transaction_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> StripeTransfer:
        """Transfer funds to a connected account."""
        try:
            transfer = self.client.Transfer.create(
                destination=destination_account_id,
                amount=amount,
                currency=currency,
                source_transaction=source_transaction_id,
                description=description,
            )
            return StripeTransfer(**transfer.to_dict())
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating transfer: {e}")
            raise StripeError(f"Failed to create transfer: {e}")

    def create_payout(
        self,
        account_id: str,
        amount: int,
        currency: str,
        method: str = "standard",  # standard | instant
        destination: Optional[str] = None,
    ) -> StripePayout:
        """Create a payout from a connected account."""
        try:
            payout = self.client.Payout.create(
                account=account_id,
                amount=amount,
                currency=currency,
                method=method,
                destination=destination,
            )
            return StripePayout(**payout.to_dict())
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payout: {e}")
            raise StripeError(f"Failed to create payout: {e}")

    def get_balance(self, account_id: Optional[str] = None) -> StripeBalance:
        """Get Stripe balance."""
        try:
            balance = self.client.Balance.retrieve(stripe_account=account_id)
            return StripeBalance(**balance.to_dict())
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting balance: {e}")
            raise StripeError(f"Failed to get balance: {e}")

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
    ) -> float:
        """Get exchange rate via Stripe."""
        try:
            rates = self.client.Rates.list(limit=100)
            for rate in rates.auto_paging_iter():
                if rate.currency == from_currency and rate.to_currency == to_currency:
                    return rate.rates[to_currency]
            raise StripeError(f"Exchange rate not found: {from_currency} -> {to_currency}")
        except Exception as e:
            logger.error(f"Stripe error getting exchange rate: {e}")
            raise StripeError(f"Failed to get exchange rate: {e}")

    def retrieve_payment_intent(self, pi_id: str) -> dict:
        """Retrieve a PaymentIntent."""
        try:
            pi = self.client.PaymentIntent.retrieve(pi_id)
            return pi.to_dict()
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment intent: {e}")
            raise StripeError(f"Failed to retrieve payment intent: {e}")

    def confirm_payment_intent(self, pi_id: str, **kwargs) -> dict:
        """Confirm a PaymentIntent."""
        try:
            pi = self.client.PaymentIntent.confirm(pi_id, **kwargs)
            return pi.to_dict()
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment intent: {e}")
            raise StripeError(f"Failed to confirm payment intent: {e}")

    def create_refund(
        self,
        charge_id: str,
        amount: Optional[int] = None,
        reason: str = "requested_by_customer",
    ) -> dict:
        """Create a refund."""
        try:
            refund = self.client.Refund.create(
                charge=charge_id,
                amount=amount,
                reason=reason,
            )
            return refund.to_dict()
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            raise StripeError(f"Failed to create refund: {e}")

    def get_account_requirements(self, account_id: str) -> dict:
        """Get account requirements for KYC."""
        try:
            account = self.client.Account.retrieve(account_id)
            return {
                "current": account.requirements.currently_due or [],
                "past_due": account.requirements.past_due or [],
                "disabled": account.requirements.disabled_reason,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting requirements: {e}")
            raise StripeError(f"Failed to get account requirements: {e}")

    def webhook_signature_verify(self, payload: bytes, signature: str) -> dict:
        """Verify and parse Stripe webhook signature."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.stripe_webhook_secret
            )
            return event.to_dict()
        except (stripe.error.SignatureVerificationError, ValueError) as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise StripeError(f"Invalid webhook signature: {e}")


# Global client instance
stripe_client: Optional[StripeConnectClient] = None


def get_stripe_client() -> StripeConnectClient:
    """Get or create the global Stripe client."""
    global stripe_client
    if stripe_client is None:
        stripe_client = StripeConnectClient()
    return stripe_client

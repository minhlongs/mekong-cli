# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stripe Billing Adapter for Nightly Reconciliation."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StripeReconciliationAdapter:
    """Adapter for fetching Stripe billing data for reconciliation."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.getenv("STRIPE_SECRET_KEY")
        self._initialized = False
        self._stripe: Any = None

        if not self._api_key:
            logger.warning("STRIPE_SECRET_KEY not set - Stripe reconciliation disabled")

    async def initialize(self) -> bool:
        """Initialize Stripe client."""
        if not self._api_key:
            return False

        try:
            import stripe  # type: ignore[import-not-found]
            stripe.api_key = self._api_key
            self._stripe = stripe
            self._initialized = True
            logger.info("Stripe client initialized")
            return True
        except ImportError:
            logger.error("Stripe package not installed. Run: pip install stripe")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Stripe: {e}")
            return False

    async def get_invoices_for_period(
        self,
        customer_email: str,
        period_start: date,
        period_end: date,
    ) -> List[Dict[str, Any]]:
        """Get Stripe invoices for a customer within a date range."""
        if not self._initialized:
            if not await self.initialize():
                return []

        try:
            customers = self._stripe.Customer.list(email=customer_email, limit=1)
            if not customers.data:
                logger.warning(f"No Stripe customer found for {customer_email}")
                return []

            customer_id = customers.data[0].id
            invoices = self._stripe.Invoice.list(
                customer=customer_id,
                created={
                    "gte": int(period_start.timestamp()),  # type: ignore[attr-defined]
                    "lte": int(period_end.timestamp()),  # type: ignore[attr-defined]
                },
                limit=100,
            )

            invoice_data = []
            for invoice in invoices.data:
                invoice_data.append({
                    "id": invoice.id,
                    "invoice_pdf": invoice.invoice_pdf,
                    "hosted_invoice_url": invoice.hosted_invoice_url,
                    "amount_due": invoice.amount_due / 100,
                    "amount_paid": invoice.amount_paid / 100,
                    "status": invoice.status,
                    "created": datetime.fromtimestamp(invoice.created),
                    "period_start": datetime.fromtimestamp(invoice.period_start),
                    "period_end": datetime.fromtimestamp(invoice.period_end),
                    "line_items": [
                        {
                            "description": item.description,
                            "amount": item.amount / 100 if item.amount else 0,
                            "quantity": item.quantity,
                            "unit_amount": item.unit_amount / 100 if item.unit_amount else None,
                            "type": item.type,
                        }
                        for item in invoice.lines.data
                    ],
                })

            logger.info(f"Found {len(invoice_data)} invoices for {customer_email}")
            return invoice_data

        except Exception as e:
            logger.error(f"Failed to fetch Stripe invoices: {e}")
            return []

    async def get_usage_record_summary(
        self,
        subscription_item_id: str,
        period_start: date,
        period_end: date,
    ) -> Optional[Dict[str, Any]]:
        """Get Stripe usage record summary for a subscription item."""
        if not self._initialized:
            if not await self.initialize():
                return None

        try:
            usage_records = self._stripe.SubscriptionItem.list_usage_records(
                subscription_item_id,
                limit=100,
            )
            total_quantity = sum(record.quantity for record in usage_records.data)
            return {
                "subscription_item_id": subscription_item_id,
                "total_quantity": total_quantity,
                "records_count": len(usage_records.data),
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to fetch usage records: {e}")
            return None

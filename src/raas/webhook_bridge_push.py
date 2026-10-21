# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Async push transport mixin for WebhookBridge."""

from __future__ import annotations

import os
import time
from typing import List, Optional

from .usage_event_schema import WebhookEvent
from .webhook_bridge_models import BillingProvider, WebhookConfig, WebhookResult


class WebhookBridgePushMixin:
    """HTTP transport methods for pushing usage events to Stripe, Polar, and Gateway."""

    config: WebhookConfig

    def generate_idempotency_key(self, event: WebhookEvent) -> str: ...
    def is_duplicate(self, idempotency_key: str) -> bool: ...
    def mark_sent(self, idempotency_key: str) -> None: ...

    async def push_to_stripe(
        self, event: WebhookEvent, subscription_item_id: str
    ) -> WebhookResult:
        """Push usage event to Stripe."""
        import requests

        start_time = time.perf_counter()
        idempotency_key = self.generate_idempotency_key(event)
        if self.is_duplicate(idempotency_key):
            return WebhookResult(
                success=False, provider=BillingProvider.STRIPE,
                event_id=event.id, error="Duplicate event (idempotency key exists)",
            )

        url = f"{self.config.stripe_api_base}/usage_records"
        headers = {
            "Authorization": f"Bearer {self.config.stripe_api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Idempotency-Key": idempotency_key,
        }
        data = {
            "subscription_item": subscription_item_id,
            "quantity": event.usage_data.get("total_tokens", 0),
            "timestamp": int(event.created_at.timestamp()),
            "action": "set",
        }
        last_error = None
        for retry in range(self.config.max_retries):
            try:
                resp = requests.post(url, headers=headers, data=data, timeout=self.config.timeout_seconds)
                if resp.status_code in (200, 201):
                    self.mark_sent(idempotency_key)
                    return WebhookResult(
                        success=True, provider=BillingProvider.STRIPE, event_id=event.id,
                        status_code=resp.status_code, elapsed_ms=(time.perf_counter() - start_time) * 1000,
                    )
                last_error = f"Stripe returned {resp.status_code}: {resp.text}"
            except requests.RequestException as e:
                last_error = f"Request failed: {str(e)}"
            if retry < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay_ms * (2**retry) / 1000.0)

        return WebhookResult(
            success=False, provider=BillingProvider.STRIPE, event_id=event.id,
            error=last_error, retries=self.config.max_retries,
            elapsed_ms=(time.perf_counter() - start_time) * 1000,
        )

    async def push_to_polar(
        self, event: WebhookEvent, benefit_id: Optional[str] = None
    ) -> WebhookResult:
        """Push usage event to Polar."""
        import requests

        start_time = time.perf_counter()
        idempotency_key = self.generate_idempotency_key(event)
        if self.is_duplicate(idempotency_key):
            return WebhookResult(
                success=False, provider=BillingProvider.POLAR,
                event_id=event.id, error="Duplicate event (idempotency key exists)",
            )

        url = f"{self.config.polar_api_base}/benefits/usage"
        headers = {
            "Authorization": f"Bearer {self.config.polar_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "benefit_id": benefit_id or event.usage_data.get("benefit_id"),
            "customer_id": event.tenant_id,
            "used": event.usage_data.get("total_tokens", 0),
            "unit": event.usage_data.get("unit", "tokens"),
            "reported_at": event.created_at.isoformat(),
        }
        last_error = None
        for retry in range(self.config.max_retries):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout_seconds)
                if resp.status_code in (200, 201):
                    self.mark_sent(idempotency_key)
                    return WebhookResult(
                        success=True, provider=BillingProvider.POLAR, event_id=event.id,
                        status_code=resp.status_code, elapsed_ms=(time.perf_counter() - start_time) * 1000,
                    )
                last_error = f"Polar returned {resp.status_code}: {resp.text}"
            except requests.RequestException as e:
                last_error = f"Request failed: {str(e)}"
            if retry < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay_ms * (2**retry) / 1000.0)

        return WebhookResult(
            success=False, provider=BillingProvider.POLAR, event_id=event.id,
            error=last_error, retries=self.config.max_retries,
            elapsed_ms=(time.perf_counter() - start_time) * 1000,
        )

    async def push_to_gateway(
        self, events: List[WebhookEvent], gateway_url: Optional[str] = None
    ) -> List[WebhookResult]:
        """Push webhook events to RaaS Gateway for relay."""
        import requests

        base = gateway_url or os.getenv("RAAS_GATEWAY_URL", "https://raas.mekongmind.com")
        url = f"{base}/v1/billing/webhook-relay"
        token = os.getenv("RAAS_LICENSE_KEY")
        if not token:
            return [
                WebhookResult(
                    success=False, provider=BillingProvider.STRIPE,
                    event_id=e.id, error="No RAAS_LICENSE_KEY for gateway auth",
                )
                for e in events
            ]

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"events": [e.to_dict() for e in events], "count": len(events)}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            ok = resp.status_code in (200, 201)
            err = None if ok else f"Gateway returned {resp.status_code}"
            return [
                WebhookResult(
                    success=ok, provider=BillingProvider(e.type),
                    event_id=e.id, status_code=resp.status_code, error=err,
                )
                for e in events
            ]
        except requests.RequestException as exc:
            return [
                WebhookResult(
                    success=False, provider=BillingProvider(e.type),
                    event_id=e.id, error=f"Gateway request failed: {str(exc)}",
                )
                for e in events
            ]

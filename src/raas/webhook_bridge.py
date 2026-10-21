# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Webhook Bridge - Stripe/Polar Billing Integration

Bridges usage metrics from RaaS Gateway to billing providers:
- Stripe Usage Records (for Stripe subscriptions)
- Polar Usage Reports (for Polar benefit tracking)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .usage_event_schema import WebhookEvent
from .webhook_bridge_models import BillingProvider, WebhookConfig, WebhookResult
from .webhook_bridge_push import WebhookBridgePushMixin


class WebhookBridge(WebhookBridgePushMixin):
    """
    Webhook Bridge for billing provider integration.

    Transforms usage events into provider-specific formats
    and pushes to billing systems asynchronously.
    """

    def __init__(self, config: Optional[WebhookConfig] = None) -> None:
        self.config = config or self._load_config()
        self.logger = logging.getLogger(__name__)
        self._idempotency_cache: Dict[str, datetime] = {}

    def _load_config(self) -> WebhookConfig:
        """Load configuration from environment variables."""
        return WebhookConfig(
            stripe_api_key=os.getenv("STRIPE_SECRET_KEY"),
            polar_api_key=os.getenv("POLAR_API_KEY"),
        )

    def build_stripe_event(
        self,
        tenant_id: str,
        usage_data: Dict[str, Any],
    ) -> WebhookEvent:
        """Build Stripe Usage Record event."""
        return WebhookEvent(
            type=BillingProvider.STRIPE.value,
            tenant_id=tenant_id,
            usage_data=usage_data,
        )

    def build_polar_event(
        self,
        tenant_id: str,
        usage_data: Dict[str, Any],
    ) -> WebhookEvent:
        """Build Polar Usage Report event."""
        return WebhookEvent(
            type=BillingProvider.POLAR.value,
            tenant_id=tenant_id,
            usage_data=usage_data,
        )

    def generate_idempotency_key(self, event: WebhookEvent) -> str:
        """Generate idempotency key for event deduplication."""
        key_data = json.dumps(
            {
                "type": event.type,
                "tenant_id": event.tenant_id,
                "created_at": event.created_at.isoformat(),
                "usage_hash": hashlib.sha256(
                    json.dumps(event.usage_data, sort_keys=True).encode()
                ).hexdigest(),
            },
            sort_keys=True,
        )
        return hashlib.sha256(key_data.encode("utf-8")).hexdigest()

    def is_duplicate(self, idempotency_key: str) -> bool:
        """Check if event is a duplicate."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        self._idempotency_cache = {
            k: v for k, v in self._idempotency_cache.items() if v > cutoff
        }
        return idempotency_key in self._idempotency_cache

    def mark_sent(self, idempotency_key: str) -> None:
        """Mark event as sent."""
        self._idempotency_cache[idempotency_key] = datetime.now(timezone.utc)

    def transform_hourly_buckets(
        self,
        buckets: List[Dict[str, Any]],
        provider: BillingProvider,
    ) -> List[WebhookEvent]:
        """Transform hourly buckets to webhook events."""
        events: List[WebhookEvent] = []
        for bucket in buckets:
            events.append(
                WebhookEvent(
                    type=provider.value,
                    tenant_id=bucket.get("tenant_id", "unknown"),
                    usage_data={
                        "hour_bucket": bucket.get("hour_bucket"),
                        "total_tokens": bucket.get("total_tokens", 0),
                        "event_count": bucket.get("event_count", 0),
                        "events_by_type": bucket.get("events_by_type", {}),
                    },
                )
            )
        return events


# Global instance
_bridge: Optional[WebhookBridge] = None


def get_bridge(config: Optional[WebhookConfig] = None) -> WebhookBridge:
    """Get global webhook bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = WebhookBridge(config)
    return _bridge


def reset_bridge() -> None:
    """Reset global bridge instance (for testing)."""
    global _bridge
    _bridge = None


__all__ = [
    "BillingProvider",
    "WebhookBridge",
    "WebhookConfig",
    "WebhookEvent",
    "WebhookResult",
    "get_bridge",
    "reset_bridge",
]

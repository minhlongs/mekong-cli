# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Sync Webhook Mixin — Phase 6 webhook, analytics, and batch sync for SyncClient

Provides:
- register_webhook: Register CLI with webhook system
- push_analytics: Push anonymized analytics to AgencyOS dashboard
- sync_usage_batch: Batch sync of usage events via /v2/usage
- get_webhook_status: Webhook configuration status
- get_analytics_status: Analytics pipeline status
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from src.core.gateway_client import GatewayError

logger = logging.getLogger(__name__)


class SyncWebhookMixin:
    """Mixin for Phase 6 webhook, analytics, and batch sync operations."""

    def register_webhook(
        self,
        push_to_billing: bool = True,
        provider: Optional[str] = None,
    ) -> dict[str, Any]:
        """Register CLI instance with webhook system for usage events."""
        try:
            tenant_id = self._get_tenant_id()
            if not tenant_id:
                return {"success": False, "error": "No tenant ID available"}

            is_valid, error = self.validate_license()
            if not is_valid:
                return {"success": False, "error": error or "License invalid"}

            license_key = os.getenv("RAAS_LICENSE_KEY", "")
            response = self.gateway.post(
                "/v1/webhooks/register",
                json={
                    "tenant_id": tenant_id,
                    "license_key": license_key,
                    "client_type": "cli",
                    "push_to_billing": push_to_billing,
                    "provider": provider,
                },
            )
            return {
                "success": True,
                "provider": response.data.get("provider", "billing"),
                "webhook_url": response.data.get("webhook_url"),
            }

        except GatewayError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Registration failed: {str(e)}"}

    def push_analytics(self) -> dict[str, Any]:
        """Push anonymized analytics to AgencyOS dashboard."""
        try:
            tenant_id = self._get_tenant_id()
            if not tenant_id:
                return {"success": False, "error": "No tenant ID available"}

            summary = self.get_usage_summary()
            analytics = {
                "tenant_id": tenant_id,
                "client_type": "cli",
                "cli_version": self._get_cli_version(),
                "total_requests": summary.total_requests,
                "total_payload_size": summary.total_payload_size,
                "hours_active": summary.hours_active,
                "endpoint_count": len(summary.endpoints),
                "unique_endpoints": list(summary.endpoints.keys())[:10],
            }

            license_key = os.getenv("RAAS_LICENSE_KEY", "")
            self.gateway.post(
                "/v1/analytics/push",
                json=analytics,
                headers={"Authorization": f"Bearer {license_key}"},
            )
            return {"success": True, "dashboard_url": "https://mekongmind.com/analytics"}

        except GatewayError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Analytics push failed: {str(e)}"}

    def sync_usage_batch(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Sync batch of usage events to RaaS Gateway via /v2/usage.

        Args:
            events: List of usage event dicts (event_id, event_type, timestamp, endpoint, metadata)

        Returns:
            Dict with success, synced_count, error
        """
        try:
            is_valid, error = self.validate_license()
            if not is_valid:
                return {"success": False, "error": error or "License invalid"}

            tenant_id = self._get_tenant_id()
            license_key = os.getenv("RAAS_LICENSE_KEY", "")

            response = self.gateway.post(
                "/v2/usage",
                json={"tenant_id": tenant_id, "license_key": license_key, "events": events},
                headers={
                    "Authorization": f"Bearer {license_key}",
                    "X-Idempotency-Key": events[0].get("event_id") if events else None,
                },
            )
            return {
                "success": True,
                "synced_count": len(events),
                "rate_limit_remaining": response.rate_limit_remaining,
            }

        except GatewayError as e:
            if e.status_code == 429:
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "rate_limit_reset_in": 60,
                }
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Batch sync failed: {str(e)}"}

    def get_webhook_status(self) -> dict[str, Any]:
        """Get webhook configuration status."""
        try:
            license_key = os.getenv("RAAS_LICENSE_KEY", "")
            response = self.gateway.get(
                "/v1/webhooks/status",
                headers={"Authorization": f"Bearer {license_key}"},
            )
            return {
                "configured": response.data.get("configured", False),
                "providers": response.data.get("providers", []),
                "last_delivery": response.data.get("last_delivery"),
            }
        except Exception:
            return {"configured": False}

    def get_analytics_status(self) -> dict[str, Any]:
        """Get analytics pipeline status."""
        try:
            license_key = os.getenv("RAAS_LICENSE_KEY", "")
            response = self.gateway.get(
                "/v1/analytics/status",
                headers={"Authorization": f"Bearer {license_key}"},
            )
            return {
                "healthy": response.data.get("healthy", False),
                "dashboard_url": response.data.get(
                    "dashboard_url", "https://mekongmind.com/analytics"
                ),
                "last_push": response.data.get("last_push"),
                "events_pushed": response.data.get("events_pushed", 0),
            }
        except Exception:
            return {"healthy": False, "error": "Analytics not configured"}

"""
Sync Encrypted Mixin — Phase 5 encrypted sync methods for SyncClient

Provides:
- fetch_entitlements: Retrieve license entitlements from gateway
- sync_metrics_encrypted: AES-256-GCM encrypted payload sync
- _push_to_billing_async: Async billing provider relay
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional

from src.core.gateway_client import GatewayError
from src.raas.usage_event_schema import SyncRequest
from src.raas.webhook_bridge import BillingProvider

from .models import SyncResult

logger = logging.getLogger(__name__)


class SyncEncryptedMixin:
    """Mixin for Phase 5 encrypted sync operations."""

    def fetch_entitlements(self, license_key: Optional[str] = None) -> dict[str, Any]:
        """Fetch license entitlements from RaaS Gateway."""
        try:
            response = self.gateway.get(
                "/v1/license/entitlements",
                headers={
                    "Authorization": f"Bearer {license_key or os.getenv('RAAS_LICENSE_KEY', '')}"
                },
            )
            return {
                "tenant_id": response.data.get("tenant_id"),
                "tier": response.data.get("tier"),
                "features": response.data.get("features", []),
                "rate_limit": response.data.get("rateLimit", 60),
                "max_payload_size": response.data.get("maxPayloadSize", 1048576),
                "retention_days": response.data.get("retentionDays", 30),
                "expires_at": response.data.get("expiresAt"),
            }
        except GatewayError as e:
            return {"error": str(e), "tenant_id": None, "tier": "free", "features": []}
        except Exception as e:
            return {
                "error": f"Failed to fetch entitlements: {str(e)}",
                "tenant_id": None,
                "tier": "free",
                "features": [],
            }

    def _build_encrypted_payload(
        self,
        events: list[dict[str, Any]],
        license_key: str,
        tenant_id: str,
        summary,
    ) -> SyncRequest:
        """Build encrypted sync request payload."""
        return self.encryptor.encrypt_sync_request(
            events=events,
            license_key=license_key,
            tenant_id=tenant_id,
            summary=summary,
        )

    def sync_metrics_encrypted(
        self,
        license_key: Optional[str] = None,
        dry_run: bool = False,
        push_to_billing: bool = True,
    ) -> SyncResult:
        """Synchronize usage metrics with AES-256-GCM encrypted payload."""
        start_time = time.perf_counter()
        license_key = license_key or os.getenv("RAAS_LICENSE_KEY", "")

        is_valid, error = self.validate_license()
        if not is_valid:
            return SyncResult(
                success=False, synced_count=0, total_payload_size=0,
                error=error, elapsed_ms=(time.perf_counter() - start_time) * 1000,
            )

        tenant_id = self._get_tenant_id()
        if not tenant_id:
            return SyncResult(
                success=False, synced_count=0, total_payload_size=0,
                error="Cannot determine tenant ID from license",
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
            )

        summary = self._get_phase5_summary()
        events = self._build_events_list()

        if dry_run:
            return SyncResult(
                success=True, synced_count=len(events),
                total_payload_size=len(json.dumps(events)),
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
                gateway_response={"dry_run": True, "event_count": len(events)},
            )

        sync_request = self._build_encrypted_payload(events, license_key, tenant_id, summary)

        try:
            response = self.gateway.post(
                "/v1/usage/sync",
                json={
                    "license_key": license_key,
                    "tenant_id": tenant_id,
                    "encrypted_payload": sync_request.encrypted_payload.dict(),
                    "summary": summary.dict(),
                    "checksum": sync_request.checksum,
                    "synced_at": sync_request.synced_at.isoformat(),
                },
            )

            if push_to_billing:
                self._push_to_billing_async(events, tenant_id)

            return SyncResult(
                success=True, synced_count=len(events),
                total_payload_size=len(json.dumps(events)),
                rate_limit_remaining=response.rate_limit_remaining,
                gateway_response=response.data,
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
            )

        except GatewayError as e:
            if e.status_code == 429:
                return SyncResult(
                    success=False, synced_count=0, total_payload_size=0,
                    error="Rate limit exceeded", rate_limit_reset_in=60,
                    elapsed_ms=(time.perf_counter() - start_time) * 1000,
                )
            return SyncResult(
                success=False, synced_count=0, total_payload_size=0,
                error=str(e), elapsed_ms=(time.perf_counter() - start_time) * 1000,
            )
        except Exception as e:
            return SyncResult(
                success=False, synced_count=0, total_payload_size=0,
                error=f"Sync failed: {str(e)}",
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
            )

    async def _push_to_billing_async(
        self,
        events: list[dict[str, Any]],
        tenant_id: str,
    ) -> None:
        """Push usage events to billing providers asynchronously."""
        hourly_buckets = self._build_hourly_buckets()

        stripe_events = self.webhook_bridge.transform_hourly_buckets(
            hourly_buckets, BillingProvider.STRIPE
        )
        polar_events = self.webhook_bridge.transform_hourly_buckets(
            hourly_buckets, BillingProvider.POLAR
        )

        if stripe_events:
            asyncio.create_task(self.webhook_bridge.push_to_gateway(stripe_events))
        if polar_events:
            asyncio.create_task(self.webhook_bridge.push_to_gateway(polar_events))

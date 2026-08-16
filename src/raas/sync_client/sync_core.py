# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Sync Core — RaaS SyncClient base class + composed final class

Orchestrates:
- License validation and tenant helpers
- Core sync_metrics and get_sync_status
- Delegates Phase 5 encrypted sync to SyncEncryptedMixin
- Delegates Phase 6 webhook/analytics to SyncWebhookMixin

Public API is unchanged: SyncClient(gateway_client, telemetry, encryptor, webhook_bridge)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

from src.core.gateway_client import GatewayClient, GatewayError
from src.core.telemetry_reporter import TelemetryReporter
from src.lib.raas_gate_validator import RaasGateValidator as _RaasGateValidatorBase
from src.raas.payload_encryptor import PayloadEncryptor, get_encryptor
from src.raas.webhook_bridge import WebhookBridge, get_bridge

from .models import SyncResult, UsageSummary
from .metrics_aggregator import (
    build_usage_summary,
    build_hourly_buckets,
    build_phase5_summary,
    build_events_list,
)
from .sync_encrypted_mixin import SyncEncryptedMixin
from .sync_webhook_mixin import SyncWebhookMixin

logger = logging.getLogger(__name__)


class _SyncClientBase:
    """
    Base SyncClient with core license/summary/sync_metrics functionality.

    Attributes and methods here are shared by all mixin layers.
    """

    def __init__(
        self,
        gateway_client: Optional[GatewayClient] = None,
        telemetry: Optional[TelemetryReporter] = None,
        encryptor: Optional[PayloadEncryptor] = None,
        webhook_bridge: Optional[WebhookBridge] = None,
    ):
        # Look up GatewayClient and RaasGateValidator via the package namespace so that
        # patch("src.raas.sync_client.GatewayClient") and
        # patch("src.raas.sync_client.RaasGateValidator") are respected in tests.
        import sys
        _pkg = sys.modules.get("src.raas.sync_client")
        _GatewayCls = (getattr(_pkg, "GatewayClient", None) if _pkg else None) or GatewayClient
        _ValidatorCls = (getattr(_pkg, "RaasGateValidator", None) if _pkg else None) or _RaasGateValidatorBase

        self.gateway = gateway_client or _GatewayCls()
        self.telemetry = telemetry or TelemetryReporter()
        self.validator = _ValidatorCls()
        self.encryptor = encryptor or get_encryptor()
        self.webhook_bridge = webhook_bridge or get_bridge()
        self._license_valid: Optional[bool] = None
        self._tenant_id: Optional[str] = None

    # ------------------------------------------------------------------ #
    # License & tenant helpers                                            #
    # ------------------------------------------------------------------ #

    def validate_license(self) -> tuple[bool, Optional[str]]:
        """Validate RAAS_LICENSE_KEY. Returns (is_valid, error_message)."""
        is_valid, error = self.validator.validate()
        self._license_valid = is_valid
        return is_valid, error

    def _get_tenant_id(self) -> Optional[str]:
        """Get tenant ID from validated license."""
        if self._tenant_id:
            return self._tenant_id
        result = self.validator.get_last_result()
        if result:
            self._tenant_id = result.get("tenant_id")
        return self._tenant_id

    def _get_cli_version(self) -> str:
        """Get CLI version for analytics."""
        try:
            from importlib.metadata import version
            return version("mekong-cli")
        except Exception:
            return "0.2.0-dev"

    # ------------------------------------------------------------------ #
    # Usage summary & hourly aggregation helpers                          #
    # ------------------------------------------------------------------ #

    def get_usage_summary(self) -> UsageSummary:
        """Get summary of local usage metrics."""
        return build_usage_summary(self.telemetry)

    def _build_hourly_buckets(self) -> list[dict[str, Any]]:
        """Build hourly bucket metrics for RaaS Gateway."""
        return build_hourly_buckets(self.telemetry)

    def _get_phase5_summary(self):
        """Get Phase 5 compatible usage summary."""
        return build_phase5_summary(self.telemetry)

    def _build_events_list(self) -> list[dict[str, Any]]:
        """Build list of usage events from telemetry."""
        return build_events_list(self.telemetry)

    # ------------------------------------------------------------------ #
    # Core sync                                                            #
    # ------------------------------------------------------------------ #

    def sync_metrics(
        self,
        license_key: Optional[str] = None,
        dry_run: bool = False,
    ) -> SyncResult:
        """Synchronize local usage metrics with RaaS Gateway."""
        start_time = time.perf_counter()

        is_valid, error = self.validate_license()
        if not is_valid:
            return SyncResult(
                success=False, synced_count=0, total_payload_size=0,
                error=error, elapsed_ms=(time.perf_counter() - start_time) * 1000,
            )

        summary = self.get_usage_summary()

        if dry_run:
            return SyncResult(
                success=True, synced_count=summary.total_requests,
                total_payload_size=summary.total_payload_size,
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
                gateway_response={"dry_run": True, "summary": summary.__dict__},
            )

        hourly_buckets = self._build_hourly_buckets()
        if not hourly_buckets:
            return SyncResult(
                success=True, synced_count=0, total_payload_size=0,
                gateway_response={"message": "No metrics to sync"},
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
            )

        try:
            response = self.gateway.post(
                "/v1/usage/sync",
                json={
                    "license_key": license_key or os.getenv("RAAS_LICENSE_KEY"),
                    "metrics": hourly_buckets,
                    "summary": {
                        "total_requests": summary.total_requests,
                        "total_payload_size": summary.total_payload_size,
                        "hours_active": summary.hours_active,
                    },
                },
            )
            return SyncResult(
                success=True, synced_count=summary.total_requests,
                total_payload_size=summary.total_payload_size,
                rate_limit_remaining=response.rate_limit_remaining,
                gateway_response=response.data,
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
            )

        except GatewayError as e:
            if e.status_code == 429:
                return SyncResult(
                    success=False, synced_count=0, total_payload_size=0,
                    error="Rate limit exceeded. Please wait before syncing.",
                    rate_limit_reset_in=60,
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

    def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status without uploading."""
        is_valid, error = self.validate_license()
        summary = self.get_usage_summary()
        circuit_status = self.gateway.get_circuit_status()

        return {
            "license_valid": is_valid,
            "license_error": error,
            "metrics_count": summary.total_requests,
            "total_payload_size": summary.total_payload_size,
            "hours_active": summary.hours_active,
            "peak_hour": summary.peak_hour,
            "peak_requests": summary.peak_requests,
            "endpoints": summary.endpoints,
            "methods": summary.methods,
            "circuit_breakers": circuit_status,
        }


class SyncClient(SyncEncryptedMixin, SyncWebhookMixin, _SyncClientBase):
    """
    RaaS Sync Client for usage metrics synchronization.

    Composes:
    - _SyncClientBase: Core license validation, sync_metrics, get_sync_status
    - SyncEncryptedMixin: Phase 5 encrypted sync, entitlements
    - SyncWebhookMixin: Phase 6 webhooks, analytics, batch sync

    MRO ensures _SyncClientBase.__init__ is called.
    """

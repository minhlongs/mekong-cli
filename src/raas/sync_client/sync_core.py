# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sync Core — RaaS SyncClient base class + composed final class."""

from __future__ import annotations

import logging
import os
import sys
import time
from typing import Any, Optional

from src.core.gateway_client import GatewayClient, GatewayError
from src.core.telemetry_reporter import TelemetryReporter
from src.lib.raas_gate_validator import RaasGateValidator as _RaasGateValidatorBase
from src.raas.payload_encryptor import PayloadEncryptor, get_encryptor
from src.raas.webhook_bridge import WebhookBridge, get_bridge

from .metrics_aggregator import (
    build_events_list,
    build_hourly_buckets,
    build_phase5_summary,
    build_usage_summary,
)
from .models import SyncResult, UsageSummary
from .sync_encrypted_mixin import SyncEncryptedMixin
from .sync_webhook_mixin import SyncWebhookMixin

logger = logging.getLogger(__name__)


class _SyncClientBase:
    """Base SyncClient with core license/summary/sync_metrics functionality."""

    def __init__(
        self,
        gateway_client: Optional[GatewayClient] = None,
        telemetry: Optional[TelemetryReporter] = None,
        encryptor: Optional[PayloadEncryptor] = None,
        webhook_bridge: Optional[WebhookBridge] = None,
    ):
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

    def validate_license(self) -> tuple[bool, Optional[str]]:
        """Validate RAAS_LICENSE_KEY. Returns (is_valid, error_message)."""
        is_valid, error = self.validator.validate()
        self._license_valid = is_valid
        return is_valid, error

    def _get_tenant_id(self) -> Optional[str]:
        if self._tenant_id:
            return self._tenant_id
        result = self.validator.get_last_result()
        if result:
            self._tenant_id = result.get("tenant_id")
        return self._tenant_id

    def _get_cli_version(self) -> str:
        try:
            from importlib.metadata import version

            return version("mekong-cli")
        except Exception:
            return "0.2.0-dev"

    def get_usage_summary(self) -> UsageSummary:
        return build_usage_summary(self.telemetry)

    def _build_hourly_buckets(self) -> list[dict[str, Any]]:
        return build_hourly_buckets(self.telemetry)

    def _get_phase5_summary(self):
        return build_phase5_summary(self.telemetry)

    def _build_events_list(self) -> list[dict[str, Any]]:
        return build_events_list(self.telemetry)

    def sync_metrics(
        self, license_key: Optional[str] = None, dry_run: bool = False
    ) -> SyncResult:
        """Synchronize local usage metrics with RaaS Gateway."""
        start_time = time.perf_counter()
        elapsed = lambda: (time.perf_counter() - start_time) * 1000  # noqa: E731

        is_valid, error = self.validate_license()
        if not is_valid:
            return SyncResult(
                success=False, synced_count=0, total_payload_size=0, error=error, elapsed_ms=elapsed()
            )

        summary = self.get_usage_summary()
        if dry_run:
            return SyncResult(
                success=True, synced_count=summary.total_requests,
                total_payload_size=summary.total_payload_size, elapsed_ms=elapsed(),
                gateway_response={"dry_run": True, "summary": summary.__dict__},
            )

        hourly_buckets = self._build_hourly_buckets()
        if not hourly_buckets:
            return SyncResult(
                success=True, synced_count=0, total_payload_size=0,
                gateway_response={"message": "No metrics to sync"}, elapsed_ms=elapsed(),
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
                gateway_response=response.data, elapsed_ms=elapsed(),
            )
        except GatewayError as e:
            if e.status_code == 429:
                return SyncResult(
                    success=False, synced_count=0, total_payload_size=0,
                    error="Rate limit exceeded. Please wait before syncing.",
                    rate_limit_reset_in=60, elapsed_ms=elapsed(),
                )
            return SyncResult(success=False, synced_count=0, total_payload_size=0, error=str(e), elapsed_ms=elapsed())
        except Exception as e:
            return SyncResult(
                success=False, synced_count=0, total_payload_size=0,
                error=f"Sync failed: {str(e)}", elapsed_ms=elapsed(),
            )

    def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status without uploading."""
        is_valid, error = self.validate_license()
        summary = self.get_usage_summary()
        return {
            "license_valid": is_valid, "license_error": error,
            "metrics_count": summary.total_requests, "total_payload_size": summary.total_payload_size,
            "hours_active": summary.hours_active, "peak_hour": summary.peak_hour,
            "peak_requests": summary.peak_requests, "endpoints": summary.endpoints,
            "methods": summary.methods, "circuit_breakers": self.gateway.get_circuit_status(),
        }


class SyncClient(SyncEncryptedMixin, SyncWebhookMixin, _SyncClientBase):
    """RaaS Sync Client for usage metrics synchronization."""

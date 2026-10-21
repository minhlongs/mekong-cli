# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""HTTP transport and sync orchestration for RaaS Billing Sync Service."""

from __future__ import annotations

import json
import sys
import time
from typing import Any, Optional

import httpx

from src.raas.billing_sync_models import SyncConfig, SyncResult, UsageRecord


def _mod() -> Any:
    return sys.modules.get("src.raas.billing_sync")


class BillingSyncTransportMixin:
    """Gateway transport, retry backoff, and sync orchestration methods."""

    config: SyncConfig
    api_key: Optional[str]
    _logger: Any

    def _get_connection(self) -> Any: ...
    def fetch_unsynced_records(
        self, limit: Optional[int] = None
    ) -> list[UsageRecord]: ...
    def generate_idempotency_key(self, records: list[UsageRecord]) -> str: ...
    def build_payload(self, records: list[UsageRecord]) -> dict[str, Any]: ...
    def mark_as_synced(self, record_ids: list[int]) -> None: ...
    def mark_sync_failed(self, record_ids: list[int], error: str) -> None: ...
    def record_sync_history(self, **kwargs: Any) -> None: ...

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff: min(base * 2^attempt, max_backoff)."""
        backoff = self.config.base_backoff_seconds * (2**attempt)
        return min(backoff, self.config.max_backoff_seconds)

    def send_to_gateway(
        self, payload: dict[str, Any], idempotency_key: str
    ) -> tuple[bool, Optional[dict], Optional[str]]:
        """Send payload to RaaS Gateway with retry logic."""
        if not self.api_key:
            return False, None, "API key not configured"

        mod = _mod()
        httpx_mod = getattr(mod, "httpx", httpx) if mod else httpx
        time_mod = getattr(mod, "time", time) if mod else time
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Idempotency-Key": idempotency_key,
        }
        last_error: Optional[str] = None

        for attempt in range(self.config.max_retries):
            try:
                with httpx_mod.Client(
                    timeout=self.config.request_timeout_seconds
                ) as client:
                    resp = client.post(
                        self.config.gateway_url, json=payload, headers=headers
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "accepted":
                            return True, data, None
                        last_error = (
                            f"Unexpected response status: {data.get('status')}"
                        )
                    elif resp.status_code == 429:
                        last_error = "Rate limit exceeded"
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        time_mod.sleep(min(retry_after, 60))
                        continue
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                        if 400 <= resp.status_code < 500:
                            return False, None, last_error
            except (httpx_mod.TimeoutException, httpx_mod.RequestError) as e:
                last_error = f"Request failed: {str(e)}"
            except Exception as e:
                return False, None, f"Unexpected error: {str(e)}"

            if attempt < self.config.max_retries - 1:
                time_mod.sleep(self._calculate_backoff(attempt))

        return False, None, last_error

    def sync_to_gateway(self, limit: Optional[int] = None) -> SyncResult:
        """Main sync method - fetch, build, send, mark."""
        mod = _mod()
        time_mod = getattr(mod, "time", time) if mod else time
        start_time = time_mod.time()
        records = self.fetch_unsynced_records(limit)
        if not records:
            return SyncResult(
                success=True,
                records_synced=0,
                records_failed=0,
                total_payload_size=0,
                elapsed_ms=(time_mod.time() - start_time) * 1000,
                gateway_response={"message": "No unsynced records"},
            )

        idempotency_key = self.generate_idempotency_key(records)
        payload = self.build_payload(records)
        payload_size = len(json.dumps(payload))
        success, resp, error = self.send_to_gateway(payload, idempotency_key)
        elapsed_ms = (time_mod.time() - start_time) * 1000

        if success and resp:
            self.mark_as_synced([r.id for r in records])
            self.record_sync_history(
                idempotency_key=idempotency_key,
                records_count=len(records),
                payload_size=payload_size,
                status="success",
                gateway_response=resp,
            )
            return SyncResult(
                success=True,
                records_synced=len(records),
                records_failed=0,
                total_payload_size=payload_size,
                elapsed_ms=elapsed_ms,
                gateway_response=resp,
                idempotency_key=idempotency_key,
            )

        self.record_sync_history(
            idempotency_key=idempotency_key,
            records_count=len(records),
            payload_size=payload_size,
            status="failed",
            error=error,
        )
        self.mark_sync_failed([r.id for r in records], error or "Unknown error")
        return SyncResult(
            success=False,
            records_synced=0,
            records_failed=len(records),
            total_payload_size=payload_size,
            elapsed_ms=elapsed_ms,
            error=error,
            idempotency_key=idempotency_key,
        )


__all__ = ["BillingSyncTransportMixin"]

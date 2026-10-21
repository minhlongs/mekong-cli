# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""src.core.gateway_client — RaaS Gateway Client package."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import requests

from ..raas_audit_logger import get_audit_logger
from ..raas_auth import RaaSAuthClient, get_auth_client
from ..rate_limit_client import RateLimitClient
from ..telemetry_reporter import TelemetryReporter
from .auth import get_auth_header
from .circuit_breaker import CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT, get_available_gateway, record_failure, record_success
from .mock import mock_request
from .models import CircuitState, GatewayError, GatewayResponse

GATEWAY_URLS: list[Optional[str]] = [
    os.getenv("RAAS_GATEWAY_URL", "https://api.cashclaw.cc"),
    os.getenv("RAAS_GATEWAY_URL_SECONDARY", "https://api.cashclaw.cc"),
    os.getenv("RAAS_GATEWAY_URL_TERTIARY"),
]


class GatewayClient:
    """Unified Gateway Client for RaaS with Circuit Breaker Pattern."""

    DEFAULT_GATEWAY_URL = "https://api.cashclaw.cc"

    def __init__(self, gateway_url: Optional[str] = None, auth_client: Optional[RaaSAuthClient] = None) -> None:
        self.gateway_url = gateway_url or os.getenv("RAAS_GATEWAY_URL", self.DEFAULT_GATEWAY_URL)
        self.auth = auth_client or get_auth_client()
        self.rate_limit = RateLimitClient()
        self.telemetry = TelemetryReporter()
        self.audit = get_audit_logger()
        self._session = requests.Session()
        self.local_test_mode = os.getenv("RAAS_LOCAL_TEST", "").lower() == "true"
        self._circuit_states: dict[str, CircuitState] = {u: CircuitState() for u in GATEWAY_URLS if u}
        self._current_gateway_idx: int = 0

    def _get_available_gateway(self) -> Optional[tuple[int, str]]:
        return get_available_gateway(GATEWAY_URLS, self._circuit_states)

    def _record_failure(self, gateway_idx: int, gateway_url: str) -> None:
        record_failure(gateway_url, self._circuit_states)

    def _record_success(self, gateway_idx: int, gateway_url: str) -> None:
        record_success(gateway_url, self._circuit_states)

    def _get_auth_header(self) -> tuple[dict[str, str], Optional[str]]:
        return get_auth_header(self.auth)

    def _mock_request(self, method: str, path: str) -> GatewayResponse:
        return mock_request(method, path)

    def _handle_http_response(
        self, response: Any, gateway_idx: int, gateway_url: str, path: str,
        method: str, kwargs: dict[str, Any], tenant_id: Optional[str], start_time: float,
    ) -> GatewayResponse:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if response.status_code == 429:
            self.rate_limit.handle_429(response)
            raise GatewayError("Rate limit exceeded", status_code=429)
        try:
            data = response.json()
        except ValueError:
            data = {"text": response.text}
        rem = response.headers.get("X-RateLimit-Remaining")
        self._record_success(gateway_idx, gateway_url)
        self._emit_telemetry(path, method, response.status_code, kwargs, tenant_id, gateway_url)
        self._emit_audit(path, method, response.status_code, tenant_id, gateway_url)
        if response.status_code >= 400:
            raise GatewayError(data.get("error", "Gateway error"), status_code=response.status_code)
        return GatewayResponse(
            status_code=response.status_code, data=data, headers=dict(response.headers),
            elapsed_ms=elapsed_ms, rate_limit_remaining=int(rem) if rem else None, gateway_url=gateway_url,
        )

    def request(self, method: str, path: str, headers: Optional[dict[str, str]] = None, **kwargs: Any) -> GatewayResponse:
        if self.local_test_mode:
            return self._mock_request(method, path)
        if not self.rate_limit.can_proceed():
            self.rate_limit.wait_for_reset()
        gw = self._get_available_gateway()
        if gw:
            gateway_idx, current_url = gw
            self._current_gateway_idx = gateway_idx
        else:
            current_url, gateway_idx = self.gateway_url, 0
        req_headers, tenant_id = self._get_auth_header()
        req_headers = {**req_headers, **(headers or {})}
        start = time.perf_counter()
        try:
            resp = self._session.request(method, f"{current_url}{path}", headers=req_headers, timeout=kwargs.pop("timeout", 30), **kwargs)
            return self._handle_http_response(resp, gateway_idx, current_url, path, method, kwargs, tenant_id, start)
        except requests.RequestException as exc:
            self._record_failure(gateway_idx, current_url)
            failover = self._get_available_gateway()
            if failover and failover[0] != gateway_idx:
                logging.warning("FAILOVER: %s → %s (error: %s)", current_url, failover[1], exc)
                return self._retry_with_gateway(failover[0], failover[1], method, path, req_headers, tenant_id, start, **kwargs)
            self.telemetry.record_call(endpoint=path, method=method, status_code=0, payload_size=0, error=str(exc), tenant_id=tenant_id, gateway_url=current_url)
            raise GatewayError(f"Gateway unreachable: {exc}", status_code=0) from exc

    def _retry_with_gateway(
        self, gateway_idx: int, gateway_url: str, method: str, path: str,
        headers: dict[str, str], tenant_id: Optional[str], start_time: float, **kwargs: Any,
    ) -> GatewayResponse:
        try:
            resp = self._session.request(method, f"{gateway_url}{path}", headers=headers, timeout=kwargs.pop("timeout", 30), **kwargs)
            return self._handle_http_response(resp, gateway_idx, gateway_url, path, method, kwargs, tenant_id, start_time)
        except requests.RequestException as exc:
            self._record_failure(gateway_idx, gateway_url)
            raise GatewayError(f"Gateway failover failed: {exc}", status_code=0) from exc

    def _emit_telemetry(self, path, method, status_code, kwargs, tenant_id, gateway_url):
        self.telemetry.record_call(endpoint=path, method=method, status_code=status_code, payload_size=len(kwargs.get("json", {})), tenant_id=tenant_id, gateway_url=gateway_url)

    def _emit_audit(self, path, method, status_code, tenant_id, gateway_url):
        self.audit.log_event(event="gateway_call", metadata={"endpoint": path, "method": method, "status_code": status_code, "tenant_id": tenant_id, "gateway_url": gateway_url})

    def get(self, path: str, **kwargs: Any) -> GatewayResponse:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> GatewayResponse:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> GatewayResponse:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> GatewayResponse:
        return self.request("DELETE", path, **kwargs)

    def health_check(self) -> bool:
        try:
            gw = self._get_available_gateway()
            return self.get(f"{gw[1] if gw else self.gateway_url}/health").status_code == 200
        except Exception as exc:
            logging.debug("Gateway health check failed: %s", exc)
            return False

    def get_circuit_status(self) -> dict[str, dict[str, object]]:
        now = time.time()
        return {
            url: {
                "state": "open" if st.circuit_open else ("half-open" if st.failure_count > 0 else "closed"),
                "failure_count": st.failure_count, "last_failure": st.last_failure_time,
                "recovery_allowed": not st.circuit_open or (now - st.last_failure_time >= CIRCUIT_RECOVERY_TIMEOUT),
            }
            for url, st in self._circuit_states.items()
        }

    def reset_circuits(self) -> None:
        for st in self._circuit_states.values():
            st.failure_count, st.circuit_open, st.last_failure_time, st.success_count = 0, False, 0.0, 0

    def flush_telemetry(self) -> None:
        self.telemetry.flush()


_gateway_client: Optional[GatewayClient] = None


def get_gateway_client() -> GatewayClient:
    global _gateway_client
    if _gateway_client is None:
        _gateway_client = GatewayClient()
    return _gateway_client


__all__ = ["GatewayClient", "GatewayError", "GatewayResponse", "CircuitState", "CIRCUIT_FAILURE_THRESHOLD", "CIRCUIT_RECOVERY_TIMEOUT", "GATEWAY_URLS", "get_gateway_client", "get_auth_client", "RateLimitClient", "TelemetryReporter", "get_audit_logger"]

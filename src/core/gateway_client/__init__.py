"""
src.core.gateway_client — RaaS Gateway Client package.

Public API (backward-compatible with the original flat module):

    from src.core.gateway_client import (
        GatewayClient, GatewayError, GatewayResponse,
        CircuitState, CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT,
        get_gateway_client,
    )

Implementation is split across sub-modules:
- models.py          — data-classes and exceptions
- circuit_breaker.py — trip/recovery helpers
- auth.py            — JWT/API-key header construction
- mock.py            — offline test-mode responses
- client.py          — GatewayClient class (imported below)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import requests

# Sub-module imports (patchable names live in THIS namespace)
from ..raas_audit_logger import get_audit_logger
from ..raas_auth import RaaSAuthClient, get_auth_client
from ..rate_limit_client import RateLimitClient
from ..telemetry_reporter import TelemetryReporter
from .auth import get_auth_header
from .circuit_breaker import (
    CIRCUIT_FAILURE_THRESHOLD,
    CIRCUIT_RECOVERY_TIMEOUT,
    get_available_gateway,
    record_failure,
    record_success,
)
from .mock import mock_request
from .models import CircuitState, GatewayError, GatewayResponse

# Ordered failover list; None entries are skipped at runtime
GATEWAY_URLS: list[Optional[str]] = [
    os.getenv("RAAS_GATEWAY_URL", "https://api.cashclaw.cc"),
    os.getenv("RAAS_GATEWAY_URL_SECONDARY", "https://api.cashclaw.cc"),
    os.getenv("RAAS_GATEWAY_URL_TERTIARY"),  # Optional tertiary
]


class GatewayClient:
    """
    Unified Gateway Client for RaaS with Circuit Breaker Pattern.

    All CLI requests to AgencyOS services route through here.

    Circuit Breaker States:
    - CLOSED: Normal operation, failures increment counter
    - OPEN: Gateway disabled, skip to next available
    - HALF-OPEN: Testing recovery after timeout
    """

    DEFAULT_GATEWAY_URL = "https://api.cashclaw.cc"

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        auth_client: Optional[RaaSAuthClient] = None,
    ) -> None:
        """
        Initialise GatewayClient.

        Phase 6.3: ``RAAS_LOCAL_TEST=true`` enables mock-only mode.

        Args:
            gateway_url: Override primary gateway URL.
            auth_client: Optional pre-built auth client.
        """
        self.gateway_url = gateway_url or os.getenv(
            "RAAS_GATEWAY_URL", self.DEFAULT_GATEWAY_URL
        )
        self.auth = auth_client or get_auth_client()
        self.rate_limit = RateLimitClient()
        self.telemetry = TelemetryReporter()
        self.audit = get_audit_logger()
        self._session = requests.Session()
        self.local_test_mode = os.getenv("RAAS_LOCAL_TEST", "").lower() == "true"

        self._circuit_states: dict[str, CircuitState] = {}
        self._current_gateway_idx: int = 0
        for url in GATEWAY_URLS:
            if url:
                self._circuit_states[url] = CircuitState()

    # ------------------------------------------------------------------
    # Circuit breaker delegation
    # ------------------------------------------------------------------

    def _get_available_gateway(self) -> Optional[tuple[int, str]]:
        """Return next usable gateway or None if all circuits are open."""
        return get_available_gateway(GATEWAY_URLS, self._circuit_states)

    def _record_failure(self, gateway_idx: int, gateway_url: str) -> None:
        record_failure(gateway_url, self._circuit_states)

    def _record_success(self, gateway_idx: int, gateway_url: str) -> None:
        record_success(gateway_url, self._circuit_states)

    # ------------------------------------------------------------------
    # Auth / mock delegation
    # ------------------------------------------------------------------

    def _get_auth_header(self) -> tuple[dict[str, str], Optional[str]]:
        return get_auth_header(self.auth)

    def _mock_request(self, method: str, path: str) -> GatewayResponse:
        return mock_request(method, path)

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> GatewayResponse:
        """
        Make an authenticated request through the gateway.

        Phase 6.3: Returns mock if ``RAAS_LOCAL_TEST=true``.
        Circuit Breaker: Auto-failover to secondary/tertiary on failures.

        Raises:
            GatewayError: On HTTP 4xx/5xx or network failure.
        """
        if self.local_test_mode:
            return self._mock_request(method, path)

        if not self.rate_limit.can_proceed():
            self.rate_limit.wait_for_reset()

        gateway_info = self._get_available_gateway()
        if gateway_info:
            gateway_idx, current_url = gateway_info
            self._current_gateway_idx = gateway_idx
        else:
            current_url = self.gateway_url
            gateway_idx = 0

        url = f"{current_url}{path}"
        request_headers, tenant_id = self._get_auth_header()
        request_headers = {**request_headers, **(headers or {})}

        start = time.perf_counter()
        try:
            response = self._session.request(
                method, url, headers=request_headers,
                timeout=kwargs.pop("timeout", 30), **kwargs,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 429:
                self.rate_limit.handle_429(response)
                raise GatewayError("Rate limit exceeded", status_code=429)

            try:
                data = response.json()
            except ValueError:
                data = {"text": response.text}

            remaining = response.headers.get("X-RateLimit-Remaining")
            rate_limit_remaining = int(remaining) if remaining else None

            self._record_success(gateway_idx, current_url)
            self._emit_telemetry(path, method, response.status_code, kwargs, tenant_id, current_url)
            self._emit_audit(path, method, response.status_code, tenant_id, current_url)

            if response.status_code >= 400:
                raise GatewayError(
                    data.get("error", "Gateway error"),
                    status_code=response.status_code,
                )

            return GatewayResponse(
                status_code=response.status_code, data=data,
                headers=dict(response.headers), elapsed_ms=elapsed_ms,
                rate_limit_remaining=rate_limit_remaining, gateway_url=current_url,
            )

        except requests.RequestException as exc:
            self._record_failure(gateway_idx, current_url)
            failover_info = self._get_available_gateway()
            if failover_info and failover_info[0] != gateway_idx:
                logging.warning("FAILOVER: %s → %s (error: %s)", current_url, failover_info[1], exc)
                return self._retry_with_gateway(
                    failover_info[0], failover_info[1],
                    method, path, request_headers, tenant_id, start, **kwargs,
                )
            self.telemetry.record_call(
                endpoint=path, method=method, status_code=0, payload_size=0,
                error=str(exc), tenant_id=tenant_id, gateway_url=current_url,
            )
            raise GatewayError(f"Gateway unreachable: {exc}", status_code=0) from exc

    def _retry_with_gateway(
        self,
        gateway_idx: int,
        gateway_url: str,
        method: str,
        path: str,
        headers: dict[str, str],
        tenant_id: Optional[str],
        start_time: float,
        **kwargs: Any,
    ) -> GatewayResponse:
        """Retry on a failover gateway. Raises GatewayError on failure."""
        url = f"{gateway_url}{path}"
        try:
            response = self._session.request(
                method, url, headers=headers,
                timeout=kwargs.pop("timeout", 30), **kwargs,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if response.status_code == 429:
                self.rate_limit.handle_429(response)
                raise GatewayError("Rate limit exceeded", status_code=429)

            try:
                data = response.json()
            except ValueError:
                data = {"text": response.text}

            remaining = response.headers.get("X-RateLimit-Remaining")
            rate_limit_remaining = int(remaining) if remaining else None

            self._record_success(gateway_idx, gateway_url)
            self._emit_telemetry(path, method, response.status_code, kwargs, tenant_id, gateway_url)
            self._emit_audit(path, method, response.status_code, tenant_id, gateway_url)

            if response.status_code >= 400:
                raise GatewayError(
                    data.get("error", "Gateway error"),
                    status_code=response.status_code,
                )

            return GatewayResponse(
                status_code=response.status_code, data=data,
                headers=dict(response.headers), elapsed_ms=elapsed_ms,
                rate_limit_remaining=rate_limit_remaining, gateway_url=gateway_url,
            )
        except requests.RequestException as exc:
            self._record_failure(gateway_idx, gateway_url)
            raise GatewayError(f"Gateway failover failed: {exc}", status_code=0) from exc

    # ------------------------------------------------------------------
    # Telemetry / audit helpers (private)
    # ------------------------------------------------------------------

    def _emit_telemetry(self, path, method, status_code, kwargs, tenant_id, gateway_url):
        self.telemetry.record_call(
            endpoint=path, method=method, status_code=status_code,
            payload_size=len(kwargs.get("json", {})),
            tenant_id=tenant_id, gateway_url=gateway_url,
        )

    def _emit_audit(self, path, method, status_code, tenant_id, gateway_url):
        self.audit.log_event(
            event="gateway_call",
            metadata={"endpoint": path, "method": method,
                      "status_code": status_code, "tenant_id": tenant_id,
                      "gateway_url": gateway_url},
        )

    # ------------------------------------------------------------------
    # Convenience HTTP methods
    # ------------------------------------------------------------------

    def get(self, path: str, **kwargs: Any) -> GatewayResponse:
        """GET request."""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> GatewayResponse:
        """POST request."""
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> GatewayResponse:
        """PUT request."""
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> GatewayResponse:
        """DELETE request."""
        return self.request("DELETE", path, **kwargs)

    # ------------------------------------------------------------------
    # Operational helpers
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Ping gateway health endpoint; return True on HTTP 200."""
        try:
            gateway_info = self._get_available_gateway()
            url = gateway_info[1] if gateway_info else self.gateway_url
            response = self.get(f"{url}/health")
            return response.status_code == 200
        except Exception as exc:
            logging.debug("Gateway health check failed: %s", exc)
            return False

    def get_circuit_status(self) -> dict[str, dict[str, object]]:
        """Return circuit breaker status for all known gateways."""
        now = time.time()
        status: dict[str, dict[str, object]] = {}
        for url, state in self._circuit_states.items():
            if state.circuit_open:
                s = "open"
            elif state.failure_count > 0:
                s = "half-open"
            else:
                s = "closed"
            status[url] = {
                "state": s,
                "failure_count": state.failure_count,
                "last_failure": state.last_failure_time,
                "recovery_allowed": (
                    not state.circuit_open
                    or (now - state.last_failure_time >= CIRCUIT_RECOVERY_TIMEOUT)
                ),
            }
        return status

    def reset_circuits(self) -> None:
        """Reset all circuit breakers to closed state."""
        for state in self._circuit_states.values():
            state.failure_count = 0
            state.circuit_open = False
            state.last_failure_time = 0.0
            state.success_count = 0

    def flush_telemetry(self) -> None:
        """Flush pending telemetry to the gateway."""
        self.telemetry.flush()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_gateway_client: Optional[GatewayClient] = None


def get_gateway_client() -> GatewayClient:
    """Return (or lazily create) the process-wide GatewayClient singleton."""
    global _gateway_client
    if _gateway_client is None:
        _gateway_client = GatewayClient()
    return _gateway_client


__all__ = [
    "GatewayClient",
    "GatewayError",
    "GatewayResponse",
    "CircuitState",
    "CIRCUIT_FAILURE_THRESHOLD",
    "CIRCUIT_RECOVERY_TIMEOUT",
    "GATEWAY_URLS",
    "get_gateway_client",
    # Dependencies re-exported so test patches on this namespace work
    "get_auth_client",
    "RateLimitClient",
    "TelemetryReporter",
    "get_audit_logger",
]

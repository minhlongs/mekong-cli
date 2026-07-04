"""
Unit tests for GatewayClient — covers uncovered branches from 56% baseline.

Targets:
- GatewayResponse / CircuitState dataclasses
- GatewayError exception
- __init__ (gateway_url, auth_client defaults, circuit states initialised)
- _get_available_gateway (all closed, one open recovered, all open)
- _record_failure (increments, trips circuit at threshold)
- _record_success (resets failure_count, full recovery after 2 successes)
- _get_auth_header (JWT token, mk_ key, no token)
- request() local_test_mode → _mock_request
- request() happy path (200)
- request() 429 rate limit
- request() 4xx/5xx raises GatewayError
- request() network exception → failover → retry
- request() all circuits open → primary used as last resort
- _retry_with_gateway (success, 429, network failure)
- get/post/put/delete convenience methods
- health_check (success, failure)
- get_circuit_status
- reset_circuits
- flush_telemetry
- _mock_request (/v1/usage path, generic path)
- get_gateway_client singleton
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.core.gateway_client import (
    GatewayClient,
    GatewayError,
    GatewayResponse,
    CircuitState,
    CIRCUIT_FAILURE_THRESHOLD,
    CIRCUIT_RECOVERY_TIMEOUT,
    get_gateway_client,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(status_code=200, json_data=None, headers=None, text=""):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {"status": "ok"}
    mock_resp.headers = headers or {}
    mock_resp.text = text
    return mock_resp


def _make_client(local_test=False) -> GatewayClient:
    """Build GatewayClient with all deps mocked."""
    mock_auth = MagicMock()
    mock_auth._load_credentials.return_value = {}
    mock_auth.validate_credentials.return_value = MagicMock(valid=False, tenant=None)

    mock_rate = MagicMock()
    mock_rate.can_proceed.return_value = True

    mock_telemetry = MagicMock()
    mock_audit = MagicMock()

    with patch("src.core.gateway_client.get_auth_client", return_value=mock_auth), \
         patch("src.core.gateway_client.RateLimitClient", return_value=mock_rate), \
         patch("src.core.gateway_client.TelemetryReporter", return_value=mock_telemetry), \
         patch("src.core.gateway_client.get_audit_logger", return_value=mock_audit), \
         patch.dict("os.environ", {"RAAS_LOCAL_TEST": "true" if local_test else ""}):
        client = GatewayClient(
            gateway_url="https://primary.test",
            auth_client=mock_auth,
        )
        client.rate_limit = mock_rate
        client.telemetry = mock_telemetry
        client.audit = mock_audit

    return client


# ---------------------------------------------------------------------------
# GatewayError
# ---------------------------------------------------------------------------

class TestGatewayError:
    def test_message_and_status(self):
        err = GatewayError("gateway down", status_code=503)
        assert str(err) == "gateway down"
        assert err.status_code == 503

    def test_default_status_code(self):
        err = GatewayError("err")
        assert err.status_code == 0


# ---------------------------------------------------------------------------
# CircuitState dataclass
# ---------------------------------------------------------------------------

class TestCircuitState:
    def test_defaults(self):
        s = CircuitState()
        assert s.failure_count == 0
        assert s.circuit_open is False
        assert s.last_failure_time == 0.0
        assert s.success_count == 0


# ---------------------------------------------------------------------------
# GatewayResponse dataclass
# ---------------------------------------------------------------------------

class TestGatewayResponse:
    def test_fields(self):
        r = GatewayResponse(
            status_code=200,
            data={"k": "v"},
            headers={"x": "y"},
            elapsed_ms=12.3,
            rate_limit_remaining=99,
            gateway_url="https://test",
        )
        assert r.status_code == 200
        assert r.data["k"] == "v"
        assert r.rate_limit_remaining == 99
        assert r.gateway_url == "https://test"


# ---------------------------------------------------------------------------
# __init__ / circuit states
# ---------------------------------------------------------------------------

class TestGatewayClientInit:
    def test_circuit_states_initialized(self):
        client = _make_client()
        # All non-None GATEWAY_URLS should have circuit state
        for url, state in client._circuit_states.items():
            assert isinstance(state, CircuitState)

    def test_local_test_mode_env(self):
        with patch.dict("os.environ", {"RAAS_LOCAL_TEST": "true"}):
            client = _make_client(local_test=True)
        assert client.local_test_mode is True

    def test_default_gateway_url(self):
        with patch.dict("os.environ", {}, clear=False):
            client = _make_client()
        assert "primary.test" in client.gateway_url


# ---------------------------------------------------------------------------
# _get_available_gateway
# ---------------------------------------------------------------------------

class TestGetAvailableGateway:
    def test_returns_first_available(self):
        client = _make_client()
        # All circuits closed → returns first non-None URL
        result = client._get_available_gateway()
        assert result is not None
        idx, url = result
        assert isinstance(url, str)

    def test_skips_open_circuit_within_timeout(self):
        client = _make_client()
        # Trip first gateway circuit
        primary = list(client._circuit_states.keys())[0]
        state = client._circuit_states[primary]
        state.circuit_open = True
        state.last_failure_time = time.time()  # recent failure

        result = client._get_available_gateway()
        # Should skip primary and use next available (if any)
        if result:
            _, url = result
            assert url != primary or len(client._circuit_states) == 1

    def test_recovers_after_timeout(self):
        client = _make_client()
        for url, state in client._circuit_states.items():
            state.circuit_open = True
            state.last_failure_time = time.time() - (CIRCUIT_RECOVERY_TIMEOUT + 1)

        result = client._get_available_gateway()
        assert result is not None
        # Circuit should now be half-open (closed)
        _, url = result
        assert client._circuit_states[url].circuit_open is False

    def test_returns_none_when_all_open(self):
        client = _make_client()
        for state in client._circuit_states.values():
            state.circuit_open = True
            state.last_failure_time = time.time()  # recent → not recovered

        result = client._get_available_gateway()
        assert result is None


# ---------------------------------------------------------------------------
# _record_failure
# ---------------------------------------------------------------------------

class TestRecordFailure:
    def test_increments_failure_count(self):
        client = _make_client()
        url = "https://test.url"
        client._record_failure(0, url)
        assert client._circuit_states[url].failure_count == 1

    def test_trips_circuit_at_threshold(self):
        client = _make_client()
        url = "https://test.url"
        client._circuit_states[url] = CircuitState()
        for _ in range(CIRCUIT_FAILURE_THRESHOLD):
            client._record_failure(0, url)
        assert client._circuit_states[url].circuit_open is True

    def test_does_not_trip_below_threshold(self):
        client = _make_client()
        url = "https://test.url"
        client._circuit_states[url] = CircuitState()
        for _ in range(CIRCUIT_FAILURE_THRESHOLD - 1):
            client._record_failure(0, url)
        assert client._circuit_states[url].circuit_open is False

    def test_resets_success_count(self):
        client = _make_client()
        url = "https://test.url"
        client._circuit_states[url] = CircuitState(success_count=5)
        client._record_failure(0, url)
        assert client._circuit_states[url].success_count == 0


# ---------------------------------------------------------------------------
# _record_success
# ---------------------------------------------------------------------------

class TestRecordSuccess:
    def test_resets_failure_count(self):
        client = _make_client()
        url = "https://test.url"
        client._circuit_states[url] = CircuitState(failure_count=2)
        client._record_success(0, url)
        assert client._circuit_states[url].failure_count == 0

    def test_closes_open_circuit(self):
        client = _make_client()
        url = "https://test.url"
        client._circuit_states[url] = CircuitState(circuit_open=True, failure_count=3)
        client._record_success(0, url)
        assert client._circuit_states[url].circuit_open is False

    def test_full_recovery_after_two_successes(self):
        """After first success circuit closes; second success bumps success_count to 2 then resets to 0."""
        client = _make_client()
        url = "https://test.url"
        # Start with open circuit and failures
        client._circuit_states[url] = CircuitState(circuit_open=True, failure_count=3)
        # First success: enters branch (circuit_open=True), resets failures, closes circuit, success_count=1
        client._record_success(0, url)
        assert client._circuit_states[url].circuit_open is False
        assert client._circuit_states[url].success_count == 1
        # Re-open to trigger branch again for second success
        client._circuit_states[url].circuit_open = True
        # Second success: enters branch again, success_count becomes 2 → reset to 0
        client._record_success(0, url)
        assert client._circuit_states[url].success_count == 0

    def test_no_op_when_healthy(self):
        """Clean circuit with no failures → no mutation."""
        client = _make_client()
        url = "https://test.url"
        client._circuit_states[url] = CircuitState()
        client._record_success(0, url)
        # Still clean
        assert client._circuit_states[url].failure_count == 0


# ---------------------------------------------------------------------------
# _get_auth_header
# ---------------------------------------------------------------------------

class TestGetAuthHeader:
    def test_no_token_returns_basic_headers(self):
        client = _make_client()
        client.auth._load_credentials.return_value = {}
        with patch.dict("os.environ", {"RAAS_LICENSE_KEY": ""}):
            headers, tenant_id = client._get_auth_header()
        assert "Content-Type" in headers
        assert "Authorization" not in headers
        assert tenant_id is None

    def test_jwt_token_adds_authorization_header(self):
        client = _make_client()
        client.auth._load_credentials.return_value = {"token": "header.payload.sig"}
        client.auth.validate_credentials.return_value = MagicMock(
            valid=True, tenant=MagicMock(tenant_id="t-123")
        )
        headers, tenant_id = client._get_auth_header()
        assert headers["Authorization"] == "Bearer header.payload.sig"
        assert "X-JWT-Attribution" in headers
        assert tenant_id == "t-123"

    def test_mk_key_uses_tenant_id_header(self):
        """mk_ keys (no dot) use X-RaaS-Tenant-ID instead of JWT Attribution."""
        client = _make_client()
        client.auth._load_credentials.return_value = {"token": "mk_no_dot_here"}
        client.auth.validate_credentials.return_value = MagicMock(
            valid=True, tenant=MagicMock(tenant_id="t-456")
        )
        headers, tenant_id = client._get_auth_header()
        assert headers["Authorization"] == "Bearer mk_no_dot_here"
        assert "X-RaaS-Tenant-ID" in headers
        assert "X-JWT-Attribution" not in headers

    def test_env_license_key_used_when_no_creds(self):
        client = _make_client()
        client.auth._load_credentials.return_value = {}
        client.auth.validate_credentials.return_value = MagicMock(valid=False, tenant=None)
        with patch.dict("os.environ", {"RAAS_LICENSE_KEY": "env_key.jwt"}):
            headers, _ = client._get_auth_header()
        assert "Authorization" in headers


# ---------------------------------------------------------------------------
# request() — local test mode
# ---------------------------------------------------------------------------

class TestRequestLocalTestMode:
    def test_local_mode_returns_mock(self):
        client = _make_client(local_test=True)
        client.local_test_mode = True
        response = client.request("GET", "/v1/cook")
        assert response.status_code == 200
        assert response.data.get("mock") is True

    def test_local_mode_usage_path(self):
        client = _make_client(local_test=True)
        client.local_test_mode = True
        response = client.request("GET", "/v1/usage")
        assert "metrics" in response.data
        assert response.data["tenant_id"] == "local_mock"


# ---------------------------------------------------------------------------
# request() — live path
# ---------------------------------------------------------------------------

class TestRequestLive:
    def _patched_client(self, session_mock):
        client = _make_client()
        client.local_test_mode = False
        client._session = session_mock
        client.auth._load_credentials.return_value = {}
        with patch.dict("os.environ", {"RAAS_LICENSE_KEY": ""}):
            pass
        return client

    def test_200_returns_gateway_response(self):
        session = MagicMock()
        session.request.return_value = _make_response(200, {"result": "ok"}, {"X-RateLimit-Remaining": "50"})
        client = self._patched_client(session)
        client.auth._load_credentials.return_value = {}

        with patch.object(client, "_get_auth_header", return_value=({"Content-Type": "application/json"}, None)):
            response = client.request("GET", "/v1/health")

        assert response.status_code == 200
        assert response.data["result"] == "ok"
        assert response.rate_limit_remaining == 50

    def test_200_no_rate_limit_header(self):
        session = MagicMock()
        session.request.return_value = _make_response(200, {"ok": True}, {})
        client = self._patched_client(session)

        with patch.object(client, "_get_auth_header", return_value=({"Content-Type": "application/json"}, None)):
            response = client.request("GET", "/v1/health")

        assert response.rate_limit_remaining is None

    def test_429_raises_gateway_error(self):
        session = MagicMock()
        mock_resp = _make_response(429, {})
        session.request.return_value = mock_resp
        client = self._patched_client(session)

        with patch.object(client, "_get_auth_header", return_value=({}, None)):
            with pytest.raises(GatewayError) as exc_info:
                client.request("POST", "/v1/cook")

        assert exc_info.value.status_code == 429

    def test_4xx_raises_gateway_error(self):
        session = MagicMock()
        session.request.return_value = _make_response(403, {"error": "forbidden"})
        client = self._patched_client(session)

        with patch.object(client, "_get_auth_header", return_value=({}, None)):
            with pytest.raises(GatewayError) as exc_info:
                client.request("GET", "/v1/data")

        assert exc_info.value.status_code == 403

    def test_non_json_response_wrapped_in_text(self):
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("not json")
        mock_resp.text = "plain text response"
        mock_resp.headers = {}
        session.request.return_value = mock_resp
        client = self._patched_client(session)

        with patch.object(client, "_get_auth_header", return_value=({}, None)):
            response = client.request("GET", "/v1/health")

        assert response.data == {"text": "plain text response"}

    def test_network_exception_triggers_failover(self):
        """On RequestException, try next gateway; if no other, raise GatewayError."""
        session = MagicMock()
        session.request.side_effect = requests.ConnectionError("refused")
        client = self._patched_client(session)

        # Remove all circuit states except primary so no failover possible
        client._circuit_states = {"https://primary.test": CircuitState()}

        with patch.object(client, "_get_auth_header", return_value=({}, None)), \
             patch.object(client, "_get_available_gateway", side_effect=[
                 (0, "https://primary.test"),  # first call → primary
                 None,                          # second call → no failover
             ]):
            with pytest.raises(GatewayError):
                client.request("GET", "/v1/health")

    def test_rate_limit_wait_called(self):
        session = MagicMock()
        session.request.return_value = _make_response(200, {})
        client = self._patched_client(session)
        client.rate_limit.can_proceed.return_value = False

        with patch.object(client, "_get_auth_header", return_value=({}, None)):
            client.request("GET", "/v1/health")

        client.rate_limit.wait_for_reset.assert_called_once()

    def test_all_circuits_open_uses_primary(self):
        """When all circuits open, falls back to primary gateway."""
        session = MagicMock()
        session.request.return_value = _make_response(200, {})
        client = self._patched_client(session)

        with patch.object(client, "_get_available_gateway", return_value=None), \
             patch.object(client, "_get_auth_header", return_value=({}, None)):
            response = client.request("GET", "/v1/health")

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# _retry_with_gateway
# ---------------------------------------------------------------------------

class TestRetryWithGateway:
    def test_retry_success(self):
        session = MagicMock()
        session.request.return_value = _make_response(200, {"ok": True})
        client = _make_client()
        client._session = session

        response = client._retry_with_gateway(
            1, "https://secondary.test", "GET", "/v1/health",
            {"Content-Type": "application/json"}, None,
            time.perf_counter(),
        )
        assert response.status_code == 200
        assert response.gateway_url == "https://secondary.test"

    def test_retry_429_raises(self):
        session = MagicMock()
        session.request.return_value = _make_response(429, {})
        client = _make_client()
        client._session = session

        with pytest.raises(GatewayError) as exc_info:
            client._retry_with_gateway(
                1, "https://secondary.test", "POST", "/v1/cook",
                {}, None, time.perf_counter(),
            )
        assert exc_info.value.status_code == 429

    def test_retry_network_error_raises(self):
        session = MagicMock()
        session.request.side_effect = requests.ConnectionError("no route")
        client = _make_client()
        client._session = session

        with pytest.raises(GatewayError):
            client._retry_with_gateway(
                1, "https://secondary.test", "GET", "/v1/health",
                {}, None, time.perf_counter(),
            )

    def test_retry_4xx_raises(self):
        session = MagicMock()
        session.request.return_value = _make_response(500, {"error": "server error"})
        client = _make_client()
        client._session = session

        with pytest.raises(GatewayError) as exc_info:
            client._retry_with_gateway(
                1, "https://secondary.test", "GET", "/v1/health",
                {}, None, time.perf_counter(),
            )
        assert exc_info.value.status_code == 500

    def test_retry_non_json_response(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("not json")
        mock_resp.text = "ok text"
        mock_resp.headers = {}

        session = MagicMock()
        session.request.return_value = mock_resp
        client = _make_client()
        client._session = session

        response = client._retry_with_gateway(
            1, "https://secondary.test", "GET", "/v1/health",
            {}, None, time.perf_counter(),
        )
        assert response.data == {"text": "ok text"}


# ---------------------------------------------------------------------------
# Convenience HTTP methods
# ---------------------------------------------------------------------------

class TestConvenienceMethods:
    def _client_with_mock_request(self):
        client = _make_client()
        mock_resp = GatewayResponse(
            status_code=200, data={"ok": True},
            headers={}, elapsed_ms=1.0,
        )
        client.request = MagicMock(return_value=mock_resp)
        return client, mock_resp

    def test_get(self):
        client, expected = self._client_with_mock_request()
        result = client.get("/v1/resource", params={"k": "v"})
        client.request.assert_called_once_with("GET", "/v1/resource", params={"k": "v"})
        assert result == expected

    def test_post(self):
        client, expected = self._client_with_mock_request()
        result = client.post("/v1/resource", json={"a": 1})
        client.request.assert_called_once_with("POST", "/v1/resource", json={"a": 1})
        assert result == expected

    def test_put(self):
        client, expected = self._client_with_mock_request()
        result = client.put("/v1/resource", json={"b": 2})
        client.request.assert_called_once_with("PUT", "/v1/resource", json={"b": 2})
        assert result == expected

    def test_delete(self):
        client, expected = self._client_with_mock_request()
        result = client.delete("/v1/resource")
        client.request.assert_called_once_with("DELETE", "/v1/resource")
        assert result == expected


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_health_check_success(self):
        client = _make_client()
        mock_resp = GatewayResponse(
            status_code=200, data={}, headers={}, elapsed_ms=1.0
        )
        client.get = MagicMock(return_value=mock_resp)
        assert client.health_check() is True

    def test_health_check_failure(self):
        client = _make_client()
        client.get = MagicMock(side_effect=GatewayError("down"))
        assert client.health_check() is False


# ---------------------------------------------------------------------------
# get_circuit_status
# ---------------------------------------------------------------------------

class TestGetCircuitStatus:
    def test_circuit_status_closed(self):
        client = _make_client()
        url = "https://test.url"
        client._circuit_states = {url: CircuitState()}
        status = client.get_circuit_status()
        assert status[url]["state"] == "closed"
        assert status[url]["failure_count"] == 0

    def test_circuit_status_open(self):
        client = _make_client()
        url = "https://test.url"
        client._circuit_states = {url: CircuitState(circuit_open=True, failure_count=3,
                                                     last_failure_time=time.time())}
        status = client.get_circuit_status()
        assert status[url]["state"] == "open"

    def test_circuit_status_half_open(self):
        client = _make_client()
        url = "https://test.url"
        client._circuit_states = {url: CircuitState(circuit_open=False, failure_count=2)}
        status = client.get_circuit_status()
        assert status[url]["state"] == "half-open"


# ---------------------------------------------------------------------------
# reset_circuits
# ---------------------------------------------------------------------------

class TestResetCircuits:
    def test_reset_clears_all_state(self):
        client = _make_client()
        for state in client._circuit_states.values():
            state.failure_count = 5
            state.circuit_open = True
            state.last_failure_time = 999.0
            state.success_count = 3

        client.reset_circuits()

        for state in client._circuit_states.values():
            assert state.failure_count == 0
            assert state.circuit_open is False
            assert state.last_failure_time == 0.0
            assert state.success_count == 0


# ---------------------------------------------------------------------------
# flush_telemetry
# ---------------------------------------------------------------------------

class TestFlushTelemetry:
    def test_calls_telemetry_flush(self):
        client = _make_client()
        client.flush_telemetry()
        client.telemetry.flush.assert_called_once()


# ---------------------------------------------------------------------------
# _mock_request
# ---------------------------------------------------------------------------

class TestMockRequest:
    def test_mock_usage_endpoint(self):
        client = _make_client(local_test=True)
        client.local_test_mode = True
        response = client._mock_request("GET", "/v1/usage/stats")
        assert response.status_code == 200
        assert "metrics" in response.data
        assert response.gateway_url == "local_mock"

    def test_mock_generic_endpoint(self):
        client = _make_client(local_test=True)
        client.local_test_mode = True
        response = client._mock_request("POST", "/v1/cook")
        assert response.status_code == 200
        assert response.data["local_test_mode"] is True
        assert response.rate_limit_remaining == 500


# ---------------------------------------------------------------------------
# get_gateway_client singleton
# ---------------------------------------------------------------------------

class TestGetGatewayClientSingleton:
    def test_returns_same_instance(self):
        import src.core.gateway_client as gc_module
        # Reset singleton
        gc_module._gateway_client = None

        with patch("src.core.gateway_client.get_auth_client", return_value=MagicMock()), \
             patch("src.core.gateway_client.RateLimitClient", return_value=MagicMock()), \
             patch("src.core.gateway_client.TelemetryReporter", return_value=MagicMock()), \
             patch("src.core.gateway_client.get_audit_logger", return_value=MagicMock()):
            c1 = get_gateway_client()
            c2 = get_gateway_client()

        assert c1 is c2
        gc_module._gateway_client = None  # cleanup

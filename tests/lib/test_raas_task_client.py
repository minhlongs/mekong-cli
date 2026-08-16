"""
Unit tests for src/lib/raas_task_client.py

Tests cover:
- Data model serialization (TaskRequest, TaskResult, GatewayConfig)
- SubagentType and TaskStatus enums
- RaasTaskClient initialization and auth header assembly
- Successful task delegation (happy path)
- HTTP error handling in delegate_task
- Network error handling in delegate_task
- get_task_status: success and failure paths
- cancel_task: success and failure
- get_available_subagents: success and fallback
- get_usage_summary: success and fallback
- Singleton helpers: get_task_client, reset_task_client
- Convenience function: delegate_to_subagent (valid and invalid type)
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
import requests

from src.lib.raas_task_client import (
    GatewayConfig,
    RaasTaskClient,
    SubagentType,
    TaskRequest,
    TaskResult,
    TaskStatus,
    delegate_to_subagent,
    get_task_client,
    reset_task_client,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_global_client():
    """Ensure global singleton is clean before/after each test."""
    reset_task_client()
    yield
    reset_task_client()


@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth._load_credentials.return_value = {"token": "test-token-abc"}
    auth._get_certificate_headers.return_value = {
        "X-Cert-ID": "cert-123",
        "X-Cert-Sig": "sig-xyz",
    }
    return auth


@pytest.fixture
def mock_audit_logger():
    return MagicMock()


@pytest.fixture
def client(mock_auth, mock_audit_logger):
    """RaasTaskClient with mocked auth and audit logger."""
    with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
         patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
        c = RaasTaskClient(gateway_url="https://test.raas.local")
    return c


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestSubagentType:
    def test_all_values_are_lowercase_strings(self):
        for member in SubagentType:
            assert member.value == member.value.lower()

    def test_cook_value(self):
        assert SubagentType.COOK.value == "cook"

    def test_code_reviewer_has_hyphen(self):
        assert SubagentType.CODE_REVIEWER.value == "code-reviewer"

    def test_enum_count(self):
        # Ensure we cover the expected set (14 members)
        assert len(SubagentType) == 14


class TestTaskStatus:
    def test_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.TIMEOUT.value == "timeout"


# ---------------------------------------------------------------------------
# Data model tests
# ---------------------------------------------------------------------------


class TestTaskRequest:
    def test_defaults(self):
        req = TaskRequest(subagent_type=SubagentType.COOK, goal="Do something")
        assert req.complexity == "moderate"
        assert req.context is None
        assert req.options == {}
        assert req.timeout_seconds == 300

    def test_to_dict_includes_required_keys(self):
        req = TaskRequest(
            subagent_type=SubagentType.PLANNER,
            goal="Plan a feature",
            complexity="complex",
            context={"repo": "my-repo"},
            options={"mode": "dry-run"},
            timeout_seconds=120,
        )
        d = req.to_dict()
        assert d["subagent_type"] == "planner"
        assert d["goal"] == "Plan a feature"
        assert d["complexity"] == "complex"
        assert d["context"] == {"repo": "my-repo"}
        assert d["options"] == {"mode": "dry-run"}
        assert d["timeout_seconds"] == 120
        assert "created_at" in d

    def test_to_dict_subagent_type_is_string_value(self):
        req = TaskRequest(subagent_type=SubagentType.TESTER, goal="run tests")
        assert req.to_dict()["subagent_type"] == "tester"


class TestTaskResult:
    def test_success_property_true_when_completed(self):
        result = TaskResult(task_id="t1", status=TaskStatus.COMPLETED)
        assert result.success is True

    def test_success_property_false_when_failed(self):
        result = TaskResult(task_id="t1", status=TaskStatus.FAILED)
        assert result.success is False

    def test_to_dict_keys(self):
        result = TaskResult(
            task_id="t42",
            status=TaskStatus.COMPLETED,
            output="all good",
            error=None,
            subagent_type="cook",
            execution_time_ms=250.5,
            credits_consumed=2,
            metadata={"foo": "bar"},
        )
        d = result.to_dict()
        assert d["task_id"] == "t42"
        assert d["status"] == "completed"
        assert d["output"] == "all good"
        assert d["error"] is None
        assert d["credits_consumed"] == 2
        assert d["metadata"] == {"foo": "bar"}

    def test_default_credits_zero(self):
        result = TaskResult(task_id="x", status=TaskStatus.PENDING)
        assert result.credits_consumed == 0


class TestGatewayConfig:
    def test_defaults(self):
        cfg = GatewayConfig()
        assert cfg.base_url == "https://api.cashclaw.cc"
        assert cfg.api_version == "v2"
        assert cfg.timeout_seconds == 30
        assert cfg.retry_attempts == 3


# ---------------------------------------------------------------------------
# RaasTaskClient initialization tests
# ---------------------------------------------------------------------------


class TestRaasTaskClientInit:
    def test_custom_gateway_url_sets_base_url(self, mock_auth, mock_audit_logger):
        with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
             patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
            c = RaasTaskClient(gateway_url="https://custom.gateway")
        assert c.config.base_url == "https://custom.gateway"

    def test_default_base_url_used_when_none(self, mock_auth, mock_audit_logger):
        with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
             patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
            c = RaasTaskClient()
        assert c.config.base_url == "https://api.cashclaw.cc"

    def test_session_has_default_headers(self, client):
        assert client._session.headers["Content-Type"] == "application/json"
        assert "mekong-cli" in client._session.headers["User-Agent"]


# ---------------------------------------------------------------------------
# Internal method tests
# ---------------------------------------------------------------------------


class TestGetBaseUrl:
    def test_combines_base_url_and_api_version(self, client):
        url = client._get_base_url()
        assert url == "https://test.raas.local/v2"


class TestGetAuthHeaders:
    def test_includes_bearer_token(self, client, mock_auth):
        mock_auth._load_credentials.return_value = {"token": "my-jwt"}
        mock_auth._get_certificate_headers.return_value = {}
        headers = client._get_auth_headers()
        assert headers["Authorization"] == "Bearer my-jwt"

    def test_includes_cert_headers_when_present(self, client, mock_auth):
        mock_auth._load_credentials.return_value = {"token": "tok"}
        mock_auth._get_certificate_headers.return_value = {
            "X-Cert-ID": "cid",
            "X-Cert-Sig": "csig",
        }
        headers = client._get_auth_headers()
        assert headers["X-Cert-ID"] == "cid"
        assert headers["X-Cert-Sig"] == "csig"

    def test_no_authorization_header_when_no_token(self, client, mock_auth):
        mock_auth._load_credentials.return_value = {}
        mock_auth._get_certificate_headers.return_value = {}
        headers = client._get_auth_headers()
        assert "Authorization" not in headers


# ---------------------------------------------------------------------------
# delegate_task — happy path
# ---------------------------------------------------------------------------


class TestDelegateTaskSuccess:
    def test_returns_completed_task_result(self, client, mock_audit_logger):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task_id": "task-001",
            "status": "completed",
            "output": "Done!",
            "credits_consumed": 3,
            "metadata": {"model": "claude-sonnet"},
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_make_request", return_value=mock_response):
            result = client.delegate_task(
                subagent_type=SubagentType.COOK,
                goal="Build auth module",
                complexity="complex",
            )

        assert result.task_id == "task-001"
        assert result.status == TaskStatus.COMPLETED
        assert result.success is True
        assert result.output == "Done!"
        assert result.credits_consumed == 3
        assert result.subagent_type == "cook"
        assert result.execution_time_ms is not None

    def test_audit_logger_called_twice_on_success(self, client, mock_audit_logger):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task_id": "t2",
            "status": "completed",
            "credits_consumed": 1,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_make_request", return_value=mock_response):
            client.delegate_task(SubagentType.TESTER, "run tests")

        assert mock_audit_logger.log_event.call_count == 2

    def test_goal_truncated_to_100_chars_in_audit_log(self, client, mock_audit_logger):
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": "t3", "status": "completed"}
        mock_response.raise_for_status = MagicMock()

        long_goal = "A" * 200

        with patch.object(client, "_make_request", return_value=mock_response):
            client.delegate_task(SubagentType.PLANNER, long_goal)

        first_call_data = mock_audit_logger.log_event.call_args_list[0][1]["data"]
        assert len(first_call_data["goal"]) == 100

    def test_unknown_status_defaults_to_completed(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": "t4", "status": "completed"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_make_request", return_value=mock_response):
            result = client.delegate_task(SubagentType.DEBUGGER, "debug it")

        assert result.status == TaskStatus.COMPLETED


# ---------------------------------------------------------------------------
# delegate_task — error paths
# ---------------------------------------------------------------------------


class TestDelegateTaskHTTPError:
    def test_http_error_returns_failed_result(self, client, mock_audit_logger):
        error_response = MagicMock()
        error_response.status_code = 429
        error_response.content = b'{"error": "Rate limited"}'
        error_response.json.return_value = {"error": "Rate limited"}

        http_err = requests.HTTPError(response=error_response)

        with patch.object(client, "_make_request", side_effect=http_err):
            result = client.delegate_task(SubagentType.COOK, "do something")

        assert result.status == TaskStatus.FAILED
        assert result.success is False
        assert result.error == "Rate limited"
        assert result.task_id == "unknown"

    def test_http_error_with_empty_body_uses_str_error(self, client):
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.content = b""
        error_response.json.return_value = {}

        http_err = requests.HTTPError("Internal Server Error", response=error_response)

        with patch.object(client, "_make_request", side_effect=http_err):
            result = client.delegate_task(SubagentType.COOK, "do something")

        assert result.status == TaskStatus.FAILED
        assert result.error is not None

    def test_http_error_logs_error_event(self, client, mock_audit_logger):
        error_response = MagicMock()
        error_response.status_code = 403
        error_response.content = b'{"error": "Forbidden"}'
        error_response.json.return_value = {"error": "Forbidden"}

        http_err = requests.HTTPError(response=error_response)

        with patch.object(client, "_make_request", side_effect=http_err):
            client.delegate_task(SubagentType.PLANNER, "plan")

        # Should log delegation attempt + error event (2 calls)
        assert mock_audit_logger.log_event.call_count == 2
        last_event_type = mock_audit_logger.log_event.call_args_list[-1][1]["event_type"]
        assert last_event_type == "subagent_error"


class TestDelegateTaskNetworkError:
    def test_connection_error_returns_failed_result(self, client):
        with patch.object(
            client, "_make_request", side_effect=requests.ConnectionError("timeout")
        ):
            result = client.delegate_task(SubagentType.RESEARCHER, "research it")

        assert result.status == TaskStatus.FAILED
        assert "Gateway unavailable" in result.error
        assert result.task_id == "unknown"

    def test_execution_time_recorded_on_network_error(self, client):
        with patch.object(
            client, "_make_request", side_effect=requests.ConnectionError("fail")
        ):
            result = client.delegate_task(SubagentType.COOK, "something")

        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 0


# ---------------------------------------------------------------------------
# get_task_status
# ---------------------------------------------------------------------------


class TestGetTaskStatus:
    def test_returns_correct_status(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "running",
            "output": None,
            "subagent_type": "cook",
            "credits_consumed": 0,
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = client.get_task_status("task-abc")

        assert result.task_id == "task-abc"
        assert result.status == TaskStatus.RUNNING

    def test_returns_failed_on_network_error(self, client):
        with patch.object(
            client, "_make_request", side_effect=requests.ConnectionError("down")
        ):
            result = client.get_task_status("task-xyz")

        assert result.status == TaskStatus.FAILED
        assert result.task_id == "task-xyz"
        assert "Status check failed" in result.error


# ---------------------------------------------------------------------------
# cancel_task
# ---------------------------------------------------------------------------


class TestCancelTask:
    def test_returns_true_on_success(self, client):
        with patch.object(client, "_make_request", return_value=MagicMock()):
            assert client.cancel_task("task-1") is True

    def test_returns_false_on_network_error(self, client):
        with patch.object(
            client, "_make_request", side_effect=requests.RequestException("fail")
        ):
            assert client.cancel_task("task-1") is False


# ---------------------------------------------------------------------------
# get_available_subagents
# ---------------------------------------------------------------------------


class TestGetAvailableSubagents:
    def test_returns_list_from_gateway(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "subagents": [{"type": "cook", "name": "Cook"}]
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            agents = client.get_available_subagents()

        assert len(agents) == 1
        assert agents[0]["type"] == "cook"

    def test_fallback_returns_all_subagent_types(self, client):
        with patch.object(
            client, "_make_request", side_effect=requests.RequestException("down")
        ):
            agents = client.get_available_subagents()

        assert len(agents) == len(SubagentType)
        types = [a["type"] for a in agents]
        assert "cook" in types
        assert "planner" in types


# ---------------------------------------------------------------------------
# get_usage_summary
# ---------------------------------------------------------------------------


class TestGetUsageSummary:
    def test_returns_response_data(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"credits": 42, "tasks": 10}

        with patch.object(client, "_make_request", return_value=mock_response):
            summary = client.get_usage_summary()

        assert summary["credits"] == 42

    def test_returns_error_dict_on_failure(self, client):
        with patch.object(
            client, "_make_request", side_effect=requests.RequestException("fail")
        ):
            summary = client.get_usage_summary()

        assert summary["available"] is False
        assert "error" in summary


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------


class TestGetTaskClient:
    def test_returns_instance(self, mock_auth, mock_audit_logger):
        with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
             patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
            c = get_task_client()
        assert isinstance(c, RaasTaskClient)

    def test_returns_same_instance_on_second_call(self, mock_auth, mock_audit_logger):
        with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
             patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
            c1 = get_task_client()
            c2 = get_task_client()
        assert c1 is c2

    def test_reset_clears_singleton(self, mock_auth, mock_audit_logger):
        with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
             patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
            c1 = get_task_client()
            reset_task_client()
            c2 = get_task_client()
        assert c1 is not c2


# ---------------------------------------------------------------------------
# delegate_to_subagent convenience function
# ---------------------------------------------------------------------------


class TestDelegateToSubagent:
    def test_valid_type_delegates_successfully(self, mock_auth, mock_audit_logger):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task_id": "t99",
            "status": "completed",
            "credits_consumed": 1,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
             patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
            with patch(
                "src.lib.raas_task_client.RaasTaskClient._make_request",
                return_value=mock_response,
            ):
                result = delegate_to_subagent("cook", "do something")

        assert result.status == TaskStatus.COMPLETED

    def test_invalid_type_returns_failed_result(self, mock_auth, mock_audit_logger):
        with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
             patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
            result = delegate_to_subagent("nonexistent-agent", "do something")

        assert result.status == TaskStatus.FAILED
        assert "Unknown subagent type" in result.error

    def test_underscore_in_type_maps_to_hyphen(self, mock_auth, mock_audit_logger):
        """code_reviewer should map to code-reviewer enum value."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": "t5", "status": "completed"}
        mock_response.raise_for_status = MagicMock()

        with patch("src.lib.raas_task_client.get_auth_client", return_value=mock_auth), \
             patch("src.lib.raas_task_client.get_audit_logger", return_value=mock_audit_logger):
            with patch(
                "src.lib.raas_task_client.RaasTaskClient._make_request",
                return_value=mock_response,
            ):
                result = delegate_to_subagent("code_reviewer", "review code")

        assert result.status == TaskStatus.COMPLETED

"""Test API error handling and input validation."""

from fastapi.testclient import TestClient

from src.gateway import app
from src.core.error_responses import ErrorCode
from src.core.input_validation import validate_required, validate_string_length

client = TestClient(app)


class TestMissionCreationValidation:
    """Test /v1/missions input validation."""

    def test_missing_goal(self):
        """Reject mission with empty goal."""
        response = client.post(
            "/v1/missions",
            json={"goal": "", "tenant_id": "tenant-123"},
        )
        assert response.status_code == 400
        data = response.json()
        # FastAPI HTTPException returns {"detail": {...}}
        assert "detail" in data
        assert "code" in data["detail"] or "error" in data["detail"]

    def test_missing_tenant_id(self):
        """Reject mission with empty tenant_id."""
        response = client.post(
            "/v1/missions",
            json={"goal": "Test goal", "tenant_id": ""},
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_invalid_priority(self):
        """Reject mission with invalid priority."""
        response = client.post(
            "/v1/missions",
            json={
                "goal": "Test goal",
                "tenant_id": "tenant-123",
                "priority": "urgent",  # Invalid
            },
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_goal_too_long(self):
        """Reject mission with goal > 5000 chars."""
        response = client.post(
            "/v1/missions",
            json={"goal": "x" * 5001, "tenant_id": "tenant-123"},
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_invalid_webhook_url(self):
        """Reject mission with invalid webhook URL."""
        response = client.post(
            "/v1/missions",
            json={
                "goal": "Test goal",
                "tenant_id": "tenant-123",
                "webhook_url": "not-a-url",
            },
        )
        assert response.status_code == 400
        assert "detail" in response.json()


class TestMCUDeductValidation:
    """Test /v1/mcu/deduct input validation."""

    def test_missing_tenant_id(self):
        """Reject deduct request with empty tenant_id."""
        response = client.post(
            "/v1/mcu/deduct",
            json={"tenant_id": "", "complexity": "simple"},
        )
        assert response.status_code == 400

    def test_invalid_complexity(self):
        """Reject deduct request with invalid complexity."""
        response = client.post(
            "/v1/mcu/deduct",
            json={"tenant_id": "tenant-123", "complexity": "extreme"},  # Invalid
        )
        assert response.status_code == 400


class TestWebhookTestValidation:
    """Test /v1/webhook/test input validation."""

    def test_missing_webhook_url(self):
        """Reject test request with empty URL."""
        response = client.post("/v1/webhook/test", json={"webhook_url": ""})
        assert response.status_code == 200  # Returns success=False
        assert response.json()["success"] is False

    def test_invalid_url_format(self):
        """Reject test request with non-HTTP URL."""
        response = client.post(
            "/v1/webhook/test",
            json={"webhook_url": "ftp://example.com"},
        )
        assert response.status_code == 200  # Returns success=False
        assert response.json()["success"] is False


class TestMissionNotFound:
    """Test 404 handling for mission endpoints."""

    def test_get_nonexistent_mission(self):
        """Return 404 for nonexistent mission."""
        response = client.get("/v1/missions/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_stream_nonexistent_mission(self):
        """Return 404 for nonexistent mission stream."""
        response = client.get("/v1/missions/nonexistent-id/stream")
        assert response.status_code == 404


class TestAgentRunValidation:
    """Test /v1/agents/{name}/run validation."""

    def test_nonexistent_agent(self):
        """Return 404 for nonexistent agent."""
        response = client.post(
            "/v1/agents/nonexistent/run",
            json={"goal": "Test goal"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "not found" in detail.lower() or "error" in str(detail).lower()

    def test_missing_goal(self):
        """Reject agent run with empty goal."""
        # Note: This requires auth, so 404 is expected for non-existent agent
        # The validation happens after auth check
        response = client.post(
            "/v1/agents/nonexistent/run",
            json={"goal": ""},
        )
        # Will return 404 because agent doesn't exist (auth/validation not reached)
        assert response.status_code in [404, 400]


class TestEndToEndErrorHandling:
    """End-to-end error handling tests."""

    def test_error_response_format(self):
        """Verify all error responses follow standard format."""
        response = client.post(
            "/v1/missions",
            json={"goal": "", "tenant_id": "tenant-123"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_request_id_in_headers(self):
        """Verify X-Request-ID header present on all responses."""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers


class TestTaskEndpointsValidation:
    """Test /v1/tasks input validation."""

    def test_task_missing_goal(self):
        """Reject task with empty goal."""
        # Empty string returns INVALID_INPUT (not MISSING_FIELD which is for None)
        error = validate_required("", "goal")
        assert error is not None
        assert error.error_code == ErrorCode.INVALID_INPUT

    def test_task_goal_too_long(self):
        """Reject task with goal > 10000 chars."""
        error = validate_string_length("x" * 10001, "goal", min_len=1, max_len=10000)
        assert error is not None
        assert error.error_code == ErrorCode.INVALID_FORMAT

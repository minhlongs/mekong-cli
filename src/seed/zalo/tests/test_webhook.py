"""Unit tests for Zalo OA Webhook Handler."""

# Test helpers conventionally skip full type annotations.
# mypy: disable-error-code="no-untyped-def,call-arg,union-attr,misc"

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.seed.zalo.webhook import ZaloWebhookHandler, create_zalo_webhook_router
from src.seed.zalo.client import ZaloOAClient
from src.seed.zalo.models import ZaloEventType, ZaloOAConfig
from src.seed.zalo.automation import ZaloAutomationEngine
from src.seed.zalo.rate_limiter import ZaloRateLimiter


@pytest.fixture
def zalo_config() -> ZaloOAConfig:
    """Create test Zalo OA config."""
    return ZaloOAConfig(
        oa_id="test_oa_id",
        secret_key="test_secret",
        access_token="test_access_token",
        webhook_secret="test_webhook_secret",
        rate_limit_per_minute=100,
    )


@pytest.fixture
def mock_client() -> MagicMock:
    """Create mock Zalo client."""
    client = MagicMock(spec=ZaloOAClient)
    client.verify_webhook_signature = MagicMock(return_value=True)
    return client


@pytest.fixture
def mock_automation() -> MagicMock:
    """Create mock automation engine."""
    automation = MagicMock(spec=ZaloAutomationEngine)
    automation.execute_rules = AsyncMock(return_value=[])
    return automation


@pytest.fixture
def mock_rate_limiter() -> MagicMock:
    """Create mock rate limiter."""
    limiter = MagicMock(spec=ZaloRateLimiter)
    limiter.check_limit = AsyncMock(return_value=(True, MagicMock(limit=100, remaining=99, reset_at=1234567890, exceeded=False)))
    return limiter


@pytest.fixture
def webhook_handler(
    zalo_config: ZaloOAConfig,
    mock_client: MagicMock,
    mock_automation: MagicMock,
    mock_rate_limiter: MagicMock,
) -> ZaloWebhookHandler:
    """Create webhook handler with mocks."""
    return ZaloWebhookHandler(zalo_config, mock_client, mock_automation, mock_rate_limiter)


@pytest.fixture
def test_app(webhook_handler: ZaloWebhookHandler) -> FastAPI:
    """Create FastAPI test app with webhook router."""
    app = FastAPI()
    app.include_router(webhook_handler.router)
    return app


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(test_app)


def make_signature(payload: dict, secret: str = "test_webhook_secret") -> str:
    """Generate HMAC-SHA256 signature matching Starlette/httpx body serialization."""
    import hashlib
    import hmac

    # httpx TestClient serializes json= via json.dumps() (default separators).
    body = json.dumps(payload).encode()
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class TestZaloWebhookHandler:
    """Tests for ZaloWebhookHandler."""

    def test_health_endpoint(self, test_client: TestClient):
        """Test webhook health endpoint."""
        response = test_client.get("/webhooks/zalo/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "zalo-webhook"}

    def test_webhook_valid_signature(self, test_client: TestClient):
        """Test webhook with valid signature."""
        payload = {
            "event_name": "message",
            "timestamp": 1234567890,
            "sender": {"user_id": "user_123", "name": "Test", "locale": "vi_VN"},
            "message": {"message_type": "text", "content": "Hello", "recipient_id": "oa_id"},
        }

        response = test_client.post(
            "/webhooks/zalo/",
            json=payload,
            headers={"X-Zalo-Signature": make_signature(payload)},
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_webhook_invalid_signature(self, test_client: TestClient):
        """Test webhook with invalid signature."""
        payload = {"event_name": "message", "timestamp": 1234567890}

        response = test_client.post(
            "/webhooks/zalo/",
            json=payload,
            headers={"X-Zalo-Signature": "invalid_signature"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid signature"

    def test_webhook_invalid_payload(self, test_client: TestClient):
        """Test webhook with invalid payload."""
        payload = {"invalid": "payload"}

        response = test_client.post(
            "/webhooks/zalo/",
            json=payload,
            headers={"X-Zalo-Signature": make_signature(payload)},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid payload"

    def test_webhook_rate_limited(self, test_client: TestClient, mock_rate_limiter: MagicMock):
        """Test webhook rate limiting."""
        from src.seed.zalo.models import RateLimitInfo
        mock_rate_limiter.check_limit.return_value = (
            False,
            RateLimitInfo(limit=100, remaining=0, reset_at=1234567890, exceeded=True),
        )

        payload = {"event_name": "message", "timestamp": 1234567890}

        response = test_client.post(
            "/webhooks/zalo/",
            json=payload,
            headers={"X-Zalo-Signature": make_signature(payload)},
        )

        assert response.status_code == 429
        assert response.json()["detail"] == "Rate limit exceeded"
        assert "X-RateLimit-Limit" in response.headers

    def test_webhook_message_event_triggers_automation(
        self, test_client: TestClient, mock_automation: MagicMock
    ):
        """Test message event triggers automation."""
        payload = {
            "event_name": "message",
            "timestamp": 1234567890,
            "sender": {"user_id": "user_123", "name": "Test", "locale": "vi_VN"},
            "message": {"message_type": "text", "content": "help", "recipient_id": "oa_id"},
        }

        response = test_client.post(
            "/webhooks/zalo/",
            json=payload,
            headers={"X-Zalo-Signature": make_signature(payload)},
        )

        assert response.status_code == 200
        mock_automation.execute_rules.assert_called_once()

    def test_webhook_follow_event(self, test_client: TestClient):
        """Test follow event."""
        payload = {
            "event_name": "follow",
            "timestamp": 1234567890,
            "follower": {
                "user_id": "user_123",
                "name": "New Follower",
                "locale": "vi_VN",
            },
        }

        response = test_client.post(
            "/webhooks/zalo/",
            json=payload,
            headers={"X-Zalo-Signature": make_signature(payload)},
        )

        assert response.status_code == 200

    def test_event_handler_registration(self, webhook_handler: ZaloWebhookHandler):
        """Test event handler registration via decorator."""
        handler_called = []

        @webhook_handler.on_event(ZaloEventType.MESSAGE)
        async def handle_message(payload):
            handler_called.append(payload)

        assert ZaloEventType.MESSAGE in webhook_handler._event_handlers
        assert len(webhook_handler._event_handlers[ZaloEventType.MESSAGE]) == 1

    def test_register_handler_programmatically(self, webhook_handler: ZaloWebhookHandler):
        """Test programmatic handler registration."""
        def handle_follow(payload):
            pass

        webhook_handler.register_handler(ZaloEventType.FOLLOW, handle_follow)

        assert ZaloEventType.FOLLOW in webhook_handler._event_handlers
        assert handle_follow in webhook_handler._event_handlers[ZaloEventType.FOLLOW]


class TestCreateZaloWebhookRouter:
    """Tests for create_zalo_webhook_router factory."""

    def test_create_router(self, zalo_config: ZaloOAConfig):
        """Test creating webhook router."""
        router = create_zalo_webhook_router(zalo_config)

        assert router is not None
        assert router.prefix == "/webhooks/zalo"
        assert "Zalo Webhooks" in router.tags

    def test_create_router_with_dependencies(
        self,
        zalo_config: ZaloOAConfig,
        mock_client: MagicMock,
        mock_automation: MagicMock,
        mock_rate_limiter: MagicMock,
    ):
        """Test creating router with all dependencies."""
        router = create_zalo_webhook_router(
            zalo_config, mock_client, mock_automation, mock_rate_limiter
        )

        assert router is not None
"""Unit tests for Zalo OA Client."""

# Test helpers conventionally skip full type annotations.
# mypy: disable-error-code="no-untyped-def,call-arg,union-attr,misc"

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.seed.zalo.client import ZaloOAClient, create_zalo_client_from_env
from src.seed.zalo.models import (
    ZaloOAConfig,
    ZaloSendMessageResponse,
    ZaloTokenResponse,
    ZaloUserProfile,
)


@pytest.fixture
def zalo_config() -> ZaloOAConfig:
    """Create test Zalo OA config."""
    return ZaloOAConfig(
        oa_id="test_oa_id",
        secret_key="test_secret",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=datetime.now() + timedelta(hours=1),
        webhook_secret="test_webhook_secret",
        rate_limit_per_minute=100,
    )


@pytest.fixture
def client(zalo_config: ZaloOAConfig) -> ZaloOAClient:
    """Create Zalo OA client with mocked HTTP."""
    return ZaloOAClient(zalo_config)


class TestZaloOAClient:
    """Tests for ZaloOAClient."""

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_valid(self, zalo_config: ZaloOAConfig):
        """Test valid HMAC signature verification."""
        payload = b'{"event_name": "message", "timestamp": 1234567890}'
        secret = "test_webhook_secret"

        # Calculate actual signature
        import hmac
        import hashlib
        actual = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        assert ZaloOAClient.verify_webhook_signature(payload, secret, actual) is True

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_invalid(self, zalo_config: ZaloOAConfig):
        """Test invalid HMAC signature verification."""
        payload = b'{"event_name": "message", "timestamp": 1234567890}'
        secret = "test_webhook_secret"
        invalid_signature = "b" * 64

        assert ZaloOAClient.verify_webhook_signature(payload, secret, invalid_signature) is False

    @pytest.mark.asyncio
    async def test_ensure_token_valid(self, client: ZaloOAClient):
        """Test token is valid and not refreshed."""
        token = await client._ensure_token()
        assert token == "test_access_token"

    @pytest.mark.asyncio
    async def test_ensure_token_expired_refresh(self, client: ZaloOAClient):
        """Test token refresh when expired."""
        client.config.token_expires_at = datetime.now() - timedelta(seconds=10)

        # Mock refresh response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            token = await client._ensure_token()

        assert token == "new_access_token"
        assert client.config.access_token == "new_access_token"
        assert client.config.refresh_token == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_send_text_message(self, client: ZaloOAClient):
        """Test sending text message."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 0,
            "message": "Success",
            "msg_id": "msg_123",
            "timestamp": 1234567890,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            response = await client.send_text("user_123", "Hello World!")

        assert isinstance(response, ZaloSendMessageResponse)
        assert response.error == 0
        assert response.msg_id == "msg_123"

    @pytest.mark.asyncio
    async def test_send_image_message(self, client: ZaloOAClient):
        """Test sending image message."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 0,
            "message": "Success",
            "msg_id": "msg_456",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            response = await client.send_image("user_123", "https://example.com/image.jpg")

        assert response.error == 0
        assert response.msg_id == "msg_456"

    @pytest.mark.asyncio
    async def test_send_carousel_message(self, client: ZaloOAClient):
        """Test sending carousel message."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 0,
            "message": "Success",
            "msg_id": "msg_789",
        }
        mock_response.raise_for_status = MagicMock()

        elements = [
            {"title": "Item 1", "image_url": "https://example.com/1.jpg", "action_url": "https://example.com/1"},
            {"title": "Item 2", "image_url": "https://example.com/2.jpg", "action_url": "https://example.com/2"},
        ]

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            response = await client.send_carousel("user_123", elements)

        assert response.error == 0
        assert response.msg_id == "msg_789"

    @pytest.mark.asyncio
    async def test_get_user_profile(self, client: ZaloOAClient):
        """Test getting user profile."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 0,
            "message": "Success",
            "data": {
                "user_id": "user_123",
                "name": "Test User",
                "gender": 1,
                "birthday": "01/01/1990",
                "phone": "0901234567",
                "avatar": "https://example.com/avatar.jpg",
                "locale": "vi_VN",
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            profile = await client.get_user_profile("user_123")

        assert isinstance(profile, ZaloUserProfile)
        assert profile.user_id == "user_123"
        assert profile.name == "Test User"

    @pytest.mark.asyncio
    async def test_generate_oauth_url(self, client: ZaloOAClient):
        """Test OAuth URL generation."""
        url = client.generate_oauth_url("https://example.com/callback", "test_state")
        assert "https://oauth.zaloapp.com/v4/permission" in url
        assert "app_id=test_oa_id" in url
        assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in url
        assert "state=test_state" in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, client: ZaloOAClient):
        """Test exchanging code for token."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            token = await client.exchange_code_for_token("auth_code", "https://example.com/callback")

        assert isinstance(token, ZaloTokenResponse)
        assert token.access_token == "new_access_token"

    @pytest.mark.asyncio
    async def test_401_retry(self, client: ZaloOAClient):
        """Test automatic retry on 401."""
        # First response: 401
        error_response = MagicMock()
        error_response.status_code = 401
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=error_response
        )

        # Second response: success
        success_response = MagicMock()
        success_response.json.return_value = {
            "error": 0,
            "message": "Success",
            "msg_id": "msg_retry",
        }
        success_response.raise_for_status = MagicMock()

        # Token refresh response (used by _refresh_access_token after 401)
        token_response = MagicMock()
        token_response.json.return_value = {
            "access_token": "refreshed_token",
            "refresh_token": "refreshed_refresh",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        token_response.raise_for_status = MagicMock()

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request, \
             patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_request.side_effect = [error_response, success_response]
            mock_get.return_value = token_response
            response = await client.send_text("user_123", "Test")

        assert response.msg_id == "msg_retry"
        assert mock_request.call_count == 2
        assert client.config.access_token == "refreshed_token"


class TestCreateZaloClientFromEnv:
    """Tests for create_zalo_client_from_env."""

    @pytest.mark.asyncio
    async def test_create_from_env(self, monkeypatch):
        """Test creating client from environment variables."""
        monkeypatch.setenv("ZALO_OA_ID", "env_oa_id")
        monkeypatch.setenv("ZALO_SECRET_KEY", "env_secret")
        monkeypatch.setenv("ZALO_WEBHOOK_SECRET", "env_webhook_secret")
        monkeypatch.setenv("ZALO_ACCESS_TOKEN", "env_access_token")
        monkeypatch.setenv("ZALO_REFRESH_TOKEN", "env_refresh_token")
        monkeypatch.setenv("ZALO_RATE_LIMIT", "200")

        client = await create_zalo_client_from_env()

        assert client.config.oa_id == "env_oa_id"
        assert client.config.secret_key == "env_secret"
        assert client.config.webhook_secret == "env_webhook_secret"
        assert client.config.access_token == "env_access_token"
        assert client.config.refresh_token == "env_refresh_token"
        assert client.config.rate_limit_per_minute == 200

        await client.close()
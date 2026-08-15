"""Zalo OA API Client with token management."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
from datetime import datetime, timedelta
from types import TracebackType
from typing import Any
from urllib.parse import urlencode

import httpx

from .models import (
    ZaloCarouselElement,
    ZaloCarouselMessage,
    ZaloImageMessage,
    ZaloOAConfig,
    ZaloOutboundMessage,
    ZaloSendMessageResponse,
    ZaloTextMessage,
    ZaloTokenResponse,
    ZaloUserProfile,
)


class ZaloOAClient:
    """Zalo Official Account API client with automatic token refresh."""

    BASE_URL = "https://openapi.zalo.me/v3.0"
    OA_BASE_URL = "https://openapi.zalo.me/v2.0/oa"

    def __init__(self, config: ZaloOAConfig):
        """Initialize Zalo OA client.

        Args:
            config: ZaloOAConfig with OA credentials and settings
        """
        self.config = config
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
        self._token_lock = asyncio.Lock()
        self._refresh_task: asyncio.Task | None = None

    async def __aenter__(self) -> ZaloOAClient:
        await self._ensure_token()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close HTTP client and cancel refresh task."""
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        await self._client.aclose()

    async def _ensure_token(self) -> str:
        """Ensure we have a valid access token, refresh if needed."""
        async with self._token_lock:
            if (
                self.config.access_token
                and self.config.token_expires_at
                and self.config.token_expires_at > datetime.now() + timedelta(seconds=60)
            ):
                return self.config.access_token

            if self.config.refresh_token:
                return await self._refresh_access_token()

            raise RuntimeError("No valid access token or refresh token available")

    async def _refresh_access_token(self) -> str:
        """Refresh access token using refresh token."""
        url = f"{self.OA_BASE_URL}/getaccesstoken"
        params = {
            "app_id": self.config.oa_id,
            "grant_type": "refresh_token",
            "refresh_token": self.config.refresh_token,
        }

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("error", 0) != 0:
            raise RuntimeError(f"Token refresh failed: {data.get('message', 'Unknown error')}")

        token_data = ZaloTokenResponse(**data)
        self.config.access_token = token_data.access_token
        self.config.refresh_token = token_data.refresh_token
        self.config.token_expires_at = datetime.now() + timedelta(seconds=token_data.expires_in - 60)

        return self.config.access_token

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        use_oa_base: bool = True,
    ) -> dict[str, Any]:
        """Make authenticated request to Zalo API."""
        token = await self._ensure_token()
        base = self.OA_BASE_URL if use_oa_base else self.BASE_URL
        url = f"{base}{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        request_params = params or {}
        request_params["access_token"] = token

        try:
            response = await self._client.request(
                method, url, params=request_params, json=json_data, headers=headers
            )
            response.raise_for_status()
            return self._as_dict(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Token expired, force refresh and retry once
                async with self._token_lock:
                    self.config.token_expires_at = datetime.now() - timedelta(seconds=1)
                token = await self._ensure_token()
                headers["Authorization"] = f"Bearer {token}"
                request_params["access_token"] = token
                response = await self._client.request(
                    method, url, params=request_params, json=json_data, headers=headers
                )
                response.raise_for_status()
                return self._as_dict(response.json())
            raise

    @staticmethod
    def _as_dict(data: Any) -> dict[str, Any]:
        """Coerce parsed JSON to a dict, raising on unexpected shapes."""
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected Zalo API response shape: {type(data).__name__}")
        return data

    async def get_user_profile(self, user_id: str) -> ZaloUserProfile:
        """Get Zalo user profile by user ID.

        Args:
            user_id: Zalo user ID

        Returns:
            ZaloUserProfile with user information
        """
        data = await self._make_request("GET", f"/getprofile?user_id={user_id}")
        if data.get("error", 0) != 0:
            raise RuntimeError(f"Get profile failed: {data.get('message', 'Unknown error')}")
        return ZaloUserProfile(**data.get("data", {}))

    async def send_message(self, message: ZaloOutboundMessage) -> ZaloSendMessageResponse:
        """Send a message to a Zalo user.

        Args:
            message: Message to send (text, image, or carousel)

        Returns:
            ZaloSendMessageResponse with message ID and status
        """
        endpoint = "/message/cs"
        payload = message.model_dump(exclude={"message_type"}, by_alias=True)
        payload["message_type"] = message.message_type

        data = await self._make_request("POST", endpoint, json_data=payload)
        return ZaloSendMessageResponse(**data)

    async def send_text(self, user_id: str, content: str) -> ZaloSendMessageResponse:
        """Send a text message.

        Args:
            user_id: Recipient user ID
            content: Text content (max 5000 chars)

        Returns:
            Send response with message ID
        """
        message = ZaloTextMessage(recipient_id=user_id, content=content)
        return await self.send_message(message)

    async def send_image(
        self, user_id: str, image_url: str, width: int | None = None, height: int | None = None
    ) -> ZaloSendMessageResponse:
        """Send an image message.

        Args:
            user_id: Recipient user ID
            image_url: HTTPS image URL
            width: Optional image width
            height: Optional image height

        Returns:
            Send response with message ID
        """
        message = ZaloImageMessage(
            recipient_id=user_id, image_url=image_url, width=width, height=height
        )
        return await self.send_message(message)

    async def send_carousel(
        self, user_id: str, elements: list[dict[str, Any]]
    ) -> ZaloSendMessageResponse:
        """Send a carousel message.

        Args:
            user_id: Recipient user ID
            elements: List of carousel elements (1-10)

        Returns:
            Send response with message ID
        """
        carousel_elements = [ZaloCarouselElement(**e) for e in elements]
        message = ZaloCarouselMessage(recipient_id=user_id, elements=carousel_elements)
        return await self.send_message(message)

    async def get_followers(self, offset: int = 0, count: int = 50) -> list[ZaloUserProfile]:
        """Get list of OA followers.

        Args:
            offset: Pagination offset
            count: Number of followers to retrieve (max 50)

        Returns:
            List of follower profiles
        """
        data = await self._make_request("GET", "/getfollowers", params={"offset": offset, "count": count})
        if data.get("error", 0) != 0:
            raise RuntimeError(f"Get followers failed: {data.get('message', 'Unknown error')}")
        followers = data.get("data", {}).get("followers", [])
        return [ZaloUserProfile(**f) for f in followers]

    async def broadcast_message(self, message: ZaloOutboundMessage) -> ZaloSendMessageResponse:
        """Broadcast a message to all followers.

        Args:
            message: Message to broadcast

        Returns:
            Send response
        """
        endpoint = "/message/broadcast"
        payload = message.model_dump(exclude={"message_type", "recipient_id"}, by_alias=True)
        payload["message_type"] = message.message_type

        data = await self._make_request("POST", endpoint, json_data=payload)
        return ZaloSendMessageResponse(**data)

    @staticmethod
    def verify_webhook_signature(payload: bytes, secret: str, signature: str) -> bool:
        """Verify HMAC-SHA256 webhook signature.

        Args:
            payload: Raw webhook payload bytes
            secret: Webhook secret key
            signature: Signature from X-Zalo-Signature header

        Returns:
            True if signature is valid
        """
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def generate_oauth_url(self, redirect_uri: str, state: str | None = None) -> str:
        """Generate Zalo OAuth authorization URL.

        Args:
            redirect_uri: OAuth redirect URI
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        params = {
            "app_id": self.config.oa_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
        }
        if state:
            params["state"] = state
        return f"https://oauth.zaloapp.com/v4/permission?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> ZaloTokenResponse:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            Token response with access and refresh tokens
        """
        url = f"{self.OA_BASE_URL}/getaccesstoken"
        params = {
            "app_id": self.config.oa_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("error", 0) != 0:
            raise RuntimeError(f"Token exchange failed: {data.get('message', 'Unknown error')}")

        return ZaloTokenResponse(**data)


# Convenience function for creating client from environment
async def create_zalo_client_from_env() -> ZaloOAClient:
    """Create ZaloOAClient from environment variables.

    Requires:
    - ZALO_OA_ID
    - ZALO_SECRET_KEY
    - ZALO_WEBHOOK_SECRET
    - ZALO_ACCESS_TOKEN (optional, will use refresh if not provided)
    - ZALO_REFRESH_TOKEN (optional)
    """
    import os

    config = ZaloOAConfig(
        oa_id=os.getenv("ZALO_OA_ID", ""),
        secret_key=os.getenv("ZALO_SECRET_KEY", ""),
        access_token=os.getenv("ZALO_ACCESS_TOKEN") or None,
        refresh_token=os.getenv("ZALO_REFRESH_TOKEN") or None,
        webhook_secret=os.getenv("ZALO_WEBHOOK_SECRET", ""),
        rate_limit_per_minute=int(os.getenv("ZALO_RATE_LIMIT", "100")),
        token_expires_at=None,
        rate_limit_window_seconds=60,
    )
    return ZaloOAClient(config)
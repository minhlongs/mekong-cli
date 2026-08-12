"""Zalo OA Webhook Handler with HMAC-SHA256 verification."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import ValidationError

from .client import ZaloOAClient
from .models import (
    ZaloEventType,
    ZaloOAConfig,
    ZaloWebhookPayload,
)
from .automation import ZaloAutomationEngine
from .rate_limiter import ZaloRateLimiter

logger = logging.getLogger(__name__)


class ZaloWebhookHandler:
    """FastAPI webhook handler for Zalo OA events."""

    def __init__(
        self,
        config: ZaloOAConfig,
        client: ZaloOAClient | None = None,
        automation: ZaloAutomationEngine | None = None,
        rate_limiter: ZaloRateLimiter | None = None,
    ):
        """Initialize webhook handler.

        Args:
            config: Zalo OA configuration
            client: Zalo OA API client
            automation: Automation engine for keyword rules
            rate_limiter: Rate limiter instance
        """
        self.config = config
        self.client = client
        self.automation = automation
        self.rate_limiter = rate_limiter
        self.router = APIRouter(prefix="/webhooks/zalo", tags=["Zalo Webhooks"])
        self._event_handlers: dict[ZaloEventType, list[Callable]] = {}
        self._register_routes()

    def _register_routes(self) -> None:
        """Register webhook routes."""

        @self.router.post("", status_code=status.HTTP_200_OK)
        async def handle_webhook(
            request: Request,
            x_zalo_signature: str = Header(..., alias="X-Zalo-Signature"),
        ) -> dict[str, str]:
            """Handle incoming Zalo OA webhook."""
            # Get raw body for signature verification
            body = await request.body()

            # Verify HMAC signature
            if not ZaloOAClient.verify_webhook_signature(
                body, self.config.webhook_secret, x_zalo_signature
            ):
                logger.warning("Invalid Zalo webhook signature")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature",
                )

            # Parse and validate payload
            try:
                payload_data = await request.json()
                payload = ZaloWebhookPayload(**payload_data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Invalid webhook payload: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid payload",
                )

            # Rate limiting per OA account
            if self.rate_limiter:
                allowed, info = await self.rate_limiter.check_limit(self.config.oa_id)
                if not allowed:
                    logger.warning(f"Rate limit exceeded for OA {self.config.oa_id}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                        headers={
                            "X-RateLimit-Limit": str(info.limit),
                            "X-RateLimit-Remaining": str(info.remaining),
                            "X-RateLimit-Reset": str(info.reset_at),
                        },
                    )

            # Process event
            await self._process_event(payload)

            return {"status": "ok"}

        @self.router.get("/health")
        async def webhook_health() -> dict[str, str]:
            """Webhook health check endpoint."""
            return {"status": "healthy", "service": "zalo-webhook"}

    async def _process_event(self, payload: ZaloWebhookPayload) -> None:
        """Process incoming webhook event."""
        logger.info(f"Processing Zalo event: {payload.event_name} at {payload.timestamp}")

        # Call registered handlers
        handlers = self._event_handlers.get(payload.event_name, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)
            except Exception as e:
                logger.error(f"Handler error for {payload.event_name}: {e}", exc_info=True)

        # Process automation rules for message events
        if payload.event_name == ZaloEventType.MESSAGE and self.automation and payload.message:
            await self._process_automation(payload)

    async def _process_automation(self, payload: ZaloWebhookPayload) -> None:
        """Process automation rules for incoming message."""
        if not payload.sender or not payload.message:
            return

        user_id = payload.sender.user_id
        message_text = ""

        if hasattr(payload.message, "content"):
            message_text = payload.message.content

        # Execute matching automation rules
        automation = self.automation
        if automation is None:
            return
        await automation.execute_rules(user_id, message_text, payload)

    def on_event(self, event_type: ZaloEventType) -> Callable:
        """Decorator to register event handler.

        Usage:
            @handler.on_event(ZaloEventType.MESSAGE)
            async def handle_message(payload):
                ...
        """

        def decorator(func: Callable) -> Callable:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(func)
            return func

        return decorator

    def register_handler(self, event_type: ZaloEventType, handler: Callable) -> None:
        """Register event handler programmatically."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)


def create_zalo_webhook_router(
    config: ZaloOAConfig,
    client: ZaloOAClient | None = None,
    automation: ZaloAutomationEngine | None = None,
    rate_limiter: ZaloRateLimiter | None = None,
) -> APIRouter:
    """Create Zalo webhook router with all dependencies.

    This is the main entry point for integrating with FastAPI gateway.
    """
    handler = ZaloWebhookHandler(config, client, automation, rate_limiter)
    return handler.router
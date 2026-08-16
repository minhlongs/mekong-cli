# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Discord webhook adapter.

Thin wrapper around Discord's webhook API using httpx.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class DiscordAdapter:
    """Sends messages and embeds to a Discord channel via webhook."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")

    def post(
        self,
        content: str,
        webhook_url: str | None = None,
        embed: dict[str, Any] | None = None,
    ) -> bool:
        """POST content (+ optional embed) to a Discord webhook.

        Args:
            content: Message text (up to 2000 chars).
            webhook_url: Override; falls back to instance / env var.
            embed: Optional Discord embed dict.

        Returns:
            True on HTTP 204, False otherwise.
        """
        url = webhook_url or self.webhook_url
        if not url:
            logger.error("[Discord] DISCORD_WEBHOOK_URL not set")
            return False

        payload: dict[str, Any] = {"content": content}
        if embed:
            payload["embeds"] = [embed]

        try:
            resp = httpx.post(url, json=payload, timeout=10)
            if resp.status_code == 204:
                logger.info("[Discord] Posted successfully")
                return True
            logger.warning("[Discord] Status %d: %s", resp.status_code, resp.text)
            return False
        except httpx.HTTPError as exc:
            logger.exception("[Discord] HTTP error: %s", exc)
            return False


__all__ = ["DiscordAdapter"]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Telegram Client."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import os
import time

import requests


@dataclass
class TelegramConfig:
    bot_token: str
    rate_limit: int = 30
    rate_window: float = 1.0
    max_retries: int = 3
    timeout: int = 30


class TelegramClient:
    """Telegram Bot API client with rate limiting."""

    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, bot_token: str | None = None, config: TelegramConfig | None = None) -> None:
        self.config = config or TelegramConfig(bot_token=bot_token or os.getenv("TELEGRAM_BOT_TOKEN", ""))
        if not self.config.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        self._rate_queue: deque[float] = deque()
        self._session = requests.Session()

    def _wait_for_rate_limit(self) -> None:
        now = time.time()
        cutoff = now - self.config.rate_window
        while self._rate_queue and self._rate_queue[0] < cutoff:
            self._rate_queue.popleft()
        if len(self._rate_queue) >= self.config.rate_limit:
            sleep_time = self.config.rate_window - (now - self._rate_queue[0])
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _request(self, method: str, data: dict[str, str]) -> dict | None:
        url = self.BASE_URL.format(token=self.config.bot_token, method=method)
        for attempt in range(self.config.max_retries):
            try:
                response = self._session.post(url, data=data, timeout=self.config.timeout)
                result = response.json()
                if result.get("ok"):
                    return result.get("result", {})
                if result.get("error_code", 0) == 429:
                    time.sleep(result.get("parameters", {}).get("retry_after", 1))
                    continue
            except requests.RequestException:
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return None

    def send_message(
        self, chat_id: str, text: str, parse_mode: str = "Markdown", disable_notification: bool = False,
    ) -> str | None:
        self._wait_for_rate_limit()
        self._rate_queue.append(time.time())
        data: dict[str, str] = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if disable_notification:
            data["disable_notification"] = "true"
        result = self._request("sendMessage", data)
        return str(result.get("message_id")) if result else None

    def send_alert(self, chat_id: str, title: str, message: str, severity: str = "info") -> str | None:
        emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
        formatted = f"{emoji.get(severity, '📢')} *{title.upper()}*\n\n{message}\n\n_Time: {time.strftime('%Y-%m-%d %H:%M:%S')}_\n_Severity: {severity}_"
        return self.send_message(chat_id, formatted, parse_mode="Markdown")

    def get_me(self) -> dict | None:
        return self._request("getMe", {})

    def send_test_message(self, chat_id: str) -> str | None:
        return self.send_message(
            chat_id, "✅ *Mekong CLI Alert System Test*\n\nBot is configured and ready to receive alerts.", parse_mode="Markdown",
        )


def send_alert(title: str, message: str, severity: str = "info", chat_id: str | None = None) -> str | None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = chat_id or os.getenv("TELEGRAM_OPS_CHANNEL_ID")
    return TelegramClient(token).send_alert(channel, title, message, severity) if (token and channel) else None


__all__ = ["TelegramClient", "TelegramConfig", "send_alert"]

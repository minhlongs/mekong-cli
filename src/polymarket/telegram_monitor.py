"""Telegram bot for remote CashClaw monitoring.

Commands:
  /status  — current P&L, open positions, capital tier
  /pause   — pause trading (set circuit breaker)
  /resume  — resume trading (clear circuit breaker)
  /pnl     — today's P&L breakdown
  /calibration — current Brier score

Alerts (automatic):
  - New trade executed
  - Daily summary
  - Circuit breaker trip
  - Calibration drift
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Optional httpx import for async HTTP
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


TELEGRAM_API = "https://api.telegram.org"


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    bot_token: str = ""
    chat_id: str = ""
    enabled: bool = False

    @classmethod
    def from_env(cls) -> TelegramConfig:
        """Load config from environment variables."""
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        return cls(
            bot_token=token,
            chat_id=chat_id,
            enabled=bool(token and chat_id),
        )


class TelegramMonitor:
    """Send alerts and receive commands via Telegram."""

    def __init__(self, config: Optional[TelegramConfig] = None) -> None:
        self.config = config or TelegramConfig.from_env()
        if not self.config.enabled:
            logger.info("Telegram monitoring disabled (no bot token/chat ID)")

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to the configured chat."""
        if not self.config.enabled:
            logger.debug("Telegram disabled, message not sent: %s", text[:50])
            return False

        if not HAS_HTTPX:
            logger.warning("httpx not installed — Telegram messages disabled")
            return False

        url = f"{TELEGRAM_API}/bot{self.config.bot_token}/sendMessage"
        payload = {
            "chat_id": self.config.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            response = httpx.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                return True
            logger.warning("Telegram API error: %d", response.status_code)
            return False
        except Exception:
            logger.exception("Failed to send Telegram message")
            return False

    def alert_trade(
        self,
        direction: str,
        market_id: str,
        size_usd: float,
        price: float,
        edge: float,
        is_paper: bool = True,
    ) -> bool:
        """Alert on new trade execution."""
        mode = "PAPER" if is_paper else "LIVE"
        text = (
            f"{'📄' if is_paper else '🔴'} *{mode} Trade*\n"
            f"Direction: `{direction}`\n"
            f"Market: `{market_id[:12]}`\n"
            f"Size: `${size_usd:.2f}`\n"
            f"Price: `{price:.4f}`\n"
            f"Edge: `{edge * 100:.1f}%`"
        )
        return self.send_message(text)

    def alert_circuit_breaker(self, reason: str) -> bool:
        """Alert on circuit breaker trip."""
        text = f"🚨 *Circuit Breaker TRIPPED*\n\nReason: {reason}\n\nTrading halted."
        return self.send_message(text)

    def alert_daily_summary(
        self,
        date: str,
        trades: int,
        pnl: float,
        win_rate: float,
        brier: float,
        capital: float,
    ) -> bool:
        """Send daily performance summary."""
        status = "✅" if pnl > 0 else "❌"
        text = (
            f"📊 *Daily Summary — {date}*\n\n"
            f"P&L: `${pnl:+.2f}` {status}\n"
            f"Trades: `{trades}`\n"
            f"Win Rate: `{win_rate * 100:.0f}%`\n"
            f"Brier: `{brier:.4f}`\n"
            f"Capital: `${capital:.2f}`"
        )
        return self.send_message(text)

    def alert_calibration_drift(self, brier: float, threshold: float) -> bool:
        """Alert on calibration drift."""
        text = (
            f"⚠️ *Calibration Drift*\n\n"
            f"Brier: `{brier:.4f}` (threshold: `{threshold:.2f}`)\n\n"
            f"Run CalibrationTuner before resuming."
        )
        return self.send_message(text)

    def send_status(
        self,
        capital: float,
        pnl: float,
        open_positions: int,
        tier_level: int,
        circuit_breaker: str,
    ) -> bool:
        """Send current status response."""
        text = (
            f"📈 *CashClaw Status*\n\n"
            f"Capital: `${capital:.2f}`\n"
            f"P&L Today: `${pnl:+.2f}`\n"
            f"Open Positions: `{open_positions}`\n"
            f"Tier: `{tier_level}`\n"
            f"Circuit Breaker: `{circuit_breaker}`"
        )
        return self.send_message(text)

    @property
    def is_enabled(self) -> bool:
        return self.config.enabled

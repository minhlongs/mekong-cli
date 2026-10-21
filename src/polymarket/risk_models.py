# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Risk management data structures and state tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.polymarket.types import CircuitBreakerState


@dataclass
class RiskConfig:
    """Risk management configuration."""
    max_position_pct: float = 0.10       # 10% of capital per position
    daily_loss_limit_pct: float = 0.05   # 5% daily loss limit
    consecutive_loss_pause: int = 3       # Pause after N consecutive losses
    pause_duration_sec: float = 3600.0   # 1 hour pause on consecutive losses
    max_brier_score: float = 0.30        # Halt if calibration drifts
    max_api_errors_per_min: int = 5      # Halt on API error storm
    paper_trading: bool = True


@dataclass
class RiskState:
    """Current risk state tracking."""
    daily_pnl: float = 0.0
    daily_trades: int = 0
    consecutive_losses: int = 0
    circuit_breaker: CircuitBreakerState = CircuitBreakerState.CLOSED
    circuit_breaker_reason: str = ""
    paused_until: Optional[float] = None
    api_errors: list[float] = field(default_factory=list)
    current_brier: float = 0.0
    date: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))

    def reset_daily(self) -> None:
        """Reset daily counters."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if self.date != today:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.date = today

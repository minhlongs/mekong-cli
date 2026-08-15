"""Risk manager — circuit breakers, daily limits, position caps."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.polymarket.types import (
    CircuitBreakerState,
    RiskCheckResult,
    Signal,
)

logger = logging.getLogger(__name__)


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


class RiskManager:
    """Central risk manager with circuit breakers."""

    def __init__(
        self,
        capital: float,
        config: Optional[RiskConfig] = None,
    ) -> None:
        self.capital = capital
        self.config = config or RiskConfig()
        self.state = RiskState()

    def check_trade(self, signal: Signal) -> RiskCheckResult:
        """Check if a trade is allowed by risk rules.

        MUST be called before EVERY trade execution.
        """
        self.state.reset_daily()

        # 1. Circuit breaker check
        if self.state.circuit_breaker == CircuitBreakerState.OPEN:
            if self.state.paused_until and time.time() < self.state.paused_until:
                return RiskCheckResult(
                    allowed=False,
                    reason=f"Circuit breaker OPEN: {self.state.circuit_breaker_reason}",
                )
            # Auto-resume after cooldown (except permanent halts)
            if "calibration" not in self.state.circuit_breaker_reason.lower():
                self._close_circuit_breaker()

        # 2. Daily loss limit (5% of capital)
        max_daily_loss = self.capital * self.config.daily_loss_limit_pct
        if self.state.daily_pnl < -max_daily_loss:
            self._trip_circuit_breaker(
                "Daily loss limit exceeded: ${:.2f}".format(abs(self.state.daily_pnl))
            )
            return RiskCheckResult(
                allowed=False,
                reason="Daily loss limit exceeded (5% of capital)",
            )

        # 3. Consecutive loss check
        if self.state.consecutive_losses >= self.config.consecutive_loss_pause:
            self._trip_circuit_breaker(
                f"{self.state.consecutive_losses} consecutive losses",
                auto_resume_sec=self.config.pause_duration_sec,
            )
            return RiskCheckResult(
                allowed=False,
                reason=f"Paused: {self.state.consecutive_losses} consecutive losses",
            )

        # 4. Position size cap (10% of capital)
        max_position = self.capital * self.config.max_position_pct
        if signal.position_size_usd > max_position:
            return RiskCheckResult(
                allowed=False,
                reason=f"Position ${signal.position_size_usd:.2f} exceeds 10% cap ${max_position:.2f}",
                max_position_size=max_position,
            )

        # 5. Calibration check
        if self.state.current_brier > self.config.max_brier_score:
            self._trip_circuit_breaker(
                f"Calibration drift: Brier {self.state.current_brier:.3f} > {self.config.max_brier_score}"
            )
            return RiskCheckResult(
                allowed=False,
                reason="Calibration drift — run CalibrationTuner",
            )

        # 6. API error storm check
        now = time.time()
        recent_errors = [t for t in self.state.api_errors if now - t < 60]
        self.state.api_errors = recent_errors
        if len(recent_errors) >= self.config.max_api_errors_per_min:
            self._trip_circuit_breaker("API error storm detected")
            return RiskCheckResult(
                allowed=False,
                reason="API error storm — too many errors in last minute",
            )

        return RiskCheckResult(
            allowed=True,
            reason="Trade approved",
            max_position_size=max_position,
        )

    def record_trade_result(self, pnl: float) -> None:
        """Record a trade result for risk tracking."""
        self.state.daily_pnl += pnl
        self.state.daily_trades += 1
        if pnl < 0:
            self.state.consecutive_losses += 1
        else:
            self.state.consecutive_losses = 0

    def record_api_error(self) -> None:
        """Record an API error for storm detection."""
        self.state.api_errors.append(time.time())

    def update_brier(self, brier_score: float) -> None:
        """Update current Brier score for calibration monitoring."""
        self.state.current_brier = brier_score

    def update_capital(self, new_capital: float) -> None:
        """Update capital for position sizing calculations."""
        self.capital = new_capital

    def _trip_circuit_breaker(
        self, reason: str, auto_resume_sec: Optional[float] = None
    ) -> None:
        """Trip the circuit breaker."""
        self.state.circuit_breaker = CircuitBreakerState.OPEN
        self.state.circuit_breaker_reason = reason
        if auto_resume_sec:
            self.state.paused_until = time.time() + auto_resume_sec
        logger.warning("Circuit breaker TRIPPED: %s", reason)

    def _close_circuit_breaker(self) -> None:
        """Close the circuit breaker (resume trading)."""
        self.state.circuit_breaker = CircuitBreakerState.CLOSED
        self.state.circuit_breaker_reason = ""
        self.state.paused_until = None
        self.state.consecutive_losses = 0
        logger.info("Circuit breaker CLOSED — trading resumed")

    def force_resume(self) -> None:
        """Manually resume trading (override circuit breaker)."""
        self._close_circuit_breaker()
        logger.info("Circuit breaker manually overridden")

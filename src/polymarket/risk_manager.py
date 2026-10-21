# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Risk manager — circuit breakers, daily limits, position caps."""

from __future__ import annotations

import logging
import time
from typing import Optional

from src.polymarket.risk_models import RiskConfig, RiskState
from src.polymarket.types import (
    CircuitBreakerState,
    RiskCheckResult,
    Signal,
)

logger = logging.getLogger(__name__)


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
        """Check if a trade is allowed by risk rules."""
        self.state.reset_daily()

        if self.state.circuit_breaker == CircuitBreakerState.OPEN:
            if self.state.paused_until and time.time() < self.state.paused_until:
                return RiskCheckResult(
                    allowed=False,
                    reason=f"Circuit breaker OPEN: {self.state.circuit_breaker_reason}",
                )
            if "calibration" not in self.state.circuit_breaker_reason.lower():
                self._close_circuit_breaker()

        max_daily_loss = self.capital * self.config.daily_loss_limit_pct
        if self.state.daily_pnl < -max_daily_loss:
            self._trip_circuit_breaker(f"Daily loss limit exceeded: ${abs(self.state.daily_pnl):.2f}")
            return RiskCheckResult(allowed=False, reason="Daily loss limit exceeded (5% of capital)")

        if self.state.consecutive_losses >= self.config.consecutive_loss_pause:
            self._trip_circuit_breaker(
                f"{self.state.consecutive_losses} consecutive losses",
                auto_resume_sec=self.config.pause_duration_sec,
            )
            return RiskCheckResult(allowed=False, reason=f"Paused: {self.state.consecutive_losses} consecutive losses")

        max_position = self.capital * self.config.max_position_pct
        if signal.position_size_usd > max_position:
            return RiskCheckResult(
                allowed=False,
                reason=f"Position ${signal.position_size_usd:.2f} exceeds 10% cap ${max_position:.2f}",
                max_position_size=max_position,
            )

        if self.state.current_brier > self.config.max_brier_score:
            self._trip_circuit_breaker(f"Calibration drift: Brier {self.state.current_brier:.3f} > {self.config.max_brier_score}")
            return RiskCheckResult(allowed=False, reason="Calibration drift — run CalibrationTuner")

        now = time.time()
        recent_errors = [t for t in self.state.api_errors if now - t < 60]
        self.state.api_errors = recent_errors
        if len(recent_errors) >= self.config.max_api_errors_per_min:
            self._trip_circuit_breaker("API error storm detected")
            return RiskCheckResult(allowed=False, reason="API error storm — too many errors in last minute")

        return RiskCheckResult(allowed=True, reason="Trade approved", max_position_size=max_position)

    def record_trade_result(self, pnl: float) -> None:
        """Record a trade result for risk tracking."""
        self.state.daily_pnl += pnl
        self.state.daily_trades += 1
        if pnl < 0:
            self.state.consecutive_losses += 1
        else:
            self.state.consecutive_losses = 0

    def record_api_error(self) -> None:
        self.state.api_errors.append(time.time())

    def update_brier(self, brier_score: float) -> None:
        self.state.current_brier = brier_score

    def update_capital(self, new_capital: float) -> None:
        self.capital = new_capital

    def _trip_circuit_breaker(self, reason: str, auto_resume_sec: Optional[float] = None) -> None:
        self.state.circuit_breaker = CircuitBreakerState.OPEN
        self.state.circuit_breaker_reason = reason
        if auto_resume_sec:
            self.state.paused_until = time.time() + auto_resume_sec
        logger.warning("Circuit breaker TRIPPED: %s", reason)

    def _close_circuit_breaker(self) -> None:
        self.state.circuit_breaker = CircuitBreakerState.CLOSED
        self.state.circuit_breaker_reason = ""
        self.state.paused_until = None
        self.state.consecutive_losses = 0
        logger.info("Circuit breaker CLOSED — trading resumed")

    def force_resume(self) -> None:
        self._close_circuit_breaker()
        logger.info("Circuit breaker manually overridden")


__all__ = ["RiskConfig", "RiskManager", "RiskState"]

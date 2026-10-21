# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Circuit Breaker — State machine for fault tolerance.

States: CLOSED (normal) → OPEN (tripped) → HALF_OPEN (testing)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from .circuit_breaker_models import (
    CircuitBreakerRegistry as CircuitBreakerRegistry,
    CircuitBreakerStats,
    CircuitState,
)

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker for protecting external services.
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 3,
        success_threshold: int = 2,
        recovery_timeout: int = 300,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure: str | None = None
        self._last_success: str | None = None
        self._last_state_change = datetime.now().isoformat()
        self._trips = 0

    @property
    def state(self) -> CircuitState:
        """Get current state, checking for automatic recovery."""
        if self._state == CircuitState.OPEN:
            last_failure_time = self._get_last_failure_time()
            if last_failure_time and (time.time() - last_failure_time) > self.recovery_timeout:
                logger.info(f"[CircuitBreaker:{self.name}] Recovery timeout elapsed → HALF_OPEN")
                self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    def can_execute(self) -> bool:
        """Check if request should be allowed."""
        current_state = self.state

        if current_state == CircuitState.CLOSED:
            return True
        if current_state == CircuitState.OPEN:
            logger.warning(f"[CircuitBreaker:{self.name}] Circuit OPEN - request blocked")
            return False

        logger.info(f"[CircuitBreaker:{self.name}] Circuit HALF_OPEN - allowing test request")
        return True

    def on_success(self) -> None:
        """Record successful request."""
        self._success_count += 1
        self._last_success = datetime.now().isoformat()

        if self._state == CircuitState.HALF_OPEN:
            if self._success_count >= self.success_threshold:
                logger.info(
                    f"[CircuitBreaker:{self.name}] Success threshold met "
                    f"({self._success_count}) → CLOSED"
                )
                self._transition_to(CircuitState.CLOSED)
                self._failure_count = 0
                self._success_count = 0
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

        logger.debug(f"[CircuitBreaker:{self.name}] Success (count={self._success_count})")

    def on_failure(self, error: str | None = None) -> None:
        """Record failed request."""
        self._failure_count += 1
        self._last_failure = datetime.now().isoformat()

        if self._state == CircuitState.HALF_OPEN:
            logger.warning(
                f"[CircuitBreaker:{self.name}] Failure during HALF_OPEN → OPEN "
                f"(trip #{self._trips + 1})"
            )
            self._transition_to(CircuitState.OPEN)
            self._trips += 1
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                logger.warning(
                    f"[CircuitBreaker:{self.name}] Failure threshold reached "
                    f"({self._failure_count}) → OPEN"
                )
                self._transition_to(CircuitState.OPEN)
                self._trips += 1
            else:
                logger.debug(
                    f"[CircuitBreaker:{self.name}] Failure "
                    f"{self._failure_count}/{self.failure_threshold}"
                )

        if error:
            logger.error(f"[CircuitBreaker:{self.name}] Failure reason: {error}")

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED."""
        logger.info(f"[CircuitBreaker:{self.name}] Manual reset")
        self._transition_to(CircuitState.CLOSED)
        self._failure_count = 0
        self._success_count = 0

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state."""
        old_state = self._state
        self._state = new_state
        self._last_state_change = datetime.now().isoformat()
        logger.info(
            f"[CircuitBreaker:{self.name}] State change: {old_state.value} → {new_state.value}"
        )

    def _get_last_failure_time(self) -> float | None:
        """Get timestamp of last failure as epoch seconds."""
        if not self._last_failure:
            return None
        try:
            return datetime.fromisoformat(self._last_failure).timestamp()
        except ValueError:
            return None

    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return CircuitBreakerStats(
            state=self.state.value,
            failure_count=self._failure_count,
            success_count=self._success_count,
            last_failure=self._last_failure,
            last_success=self._last_success,
            last_state_change=self._last_state_change,
            trips=self._trips,
        )

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name}, state={self.state.value}, "
            f"failures={self._failure_count})"
        )

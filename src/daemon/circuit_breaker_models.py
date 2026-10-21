# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Circuit Breaker Models & Registry — CircuitState, CircuitBreakerStats, and CircuitBreakerRegistry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Tripped, requests blocked
    HALF_OPEN = "half_open"  # Testing, single request allowed


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    state: str
    failure_count: int
    success_count: int
    last_failure: str | None
    last_success: str | None
    last_state_change: str
    trips: int


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    """

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create a circuit breaker by name."""
        if name not in self._breakers:
            from .circuit_breaker import CircuitBreaker

            self._breakers[name] = CircuitBreaker(name=name, **kwargs)
            logger.info(f"[CircuitBreakerRegistry] Created breaker: {name}")
        return self._breakers[name]

    def reset(self, name: str) -> bool:
        """Reset a specific circuit breaker."""
        if name in self._breakers:
            self._breakers[name].reset()
            return True
        return False

    def reset_all(self) -> int:
        """Reset all circuit breakers. Returns count reset."""
        count = len(self._breakers)
        for breaker in self._breakers.values():
            breaker.reset()
        return count

    def get_stats(self) -> dict[str, CircuitBreakerStats]:
        """Get stats for all breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    def list_breakers(self) -> list[str]:
        """List all registered breaker names."""
        return list(self._breakers.keys())

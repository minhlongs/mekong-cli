"""
Gateway data models — GatewayResponse, CircuitState, GatewayError.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class GatewayResponse:
    """Response from gateway request."""

    status_code: int
    data: Union[dict[str, object], str, None]
    headers: dict[str, str]
    elapsed_ms: float
    rate_limit_remaining: Optional[int] = None
    gateway_url: Optional[str] = None  # Track which gateway responded


@dataclass
class CircuitState:
    """Circuit breaker state for a single gateway."""

    failure_count: int = 0
    circuit_open: bool = False
    last_failure_time: float = 0.0
    success_count: int = 0  # For half-open recovery


class GatewayError(Exception):
    """Gateway request error."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code

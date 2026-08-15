"""
Circuit breaker logic for GatewayClient.

Manages per-gateway open/closed/half-open state with automatic
trip-on-threshold and recovery-after-timeout behaviour.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from .models import CircuitState

# Trip after N consecutive failures
CIRCUIT_FAILURE_THRESHOLD = 3
# Seconds before a tripped circuit allows a retry (half-open)
CIRCUIT_RECOVERY_TIMEOUT = 60


def get_available_gateway(
    gateway_urls: list[Optional[str]],
    circuit_states: dict[str, CircuitState],
) -> Optional[tuple[int, str]]:
    """
    Return the first available (non-open) gateway.

    Half-open recovery: if a circuit's timeout has elapsed, reset it to
    closed so the caller may attempt one probe request.

    Args:
        gateway_urls: Ordered list of gateway URL strings (may contain None).
        circuit_states: Mapping of URL → CircuitState.

    Returns:
        (index, url) of the first usable gateway, or None if all are open.
    """
    now = time.time()

    for i, url in enumerate(gateway_urls):
        if not url:
            continue

        state = circuit_states.get(url)
        if not state:
            continue

        if state.circuit_open:
            elapsed = now - state.last_failure_time
            if elapsed < CIRCUIT_RECOVERY_TIMEOUT:
                continue  # Still within timeout — skip
            # Timeout elapsed → allow half-open probe
            state.circuit_open = False

        return (i, url)

    return None  # All circuits open


def record_failure(
    gateway_url: str,
    circuit_states: dict[str, CircuitState],
) -> None:
    """
    Increment failure counter; trip the circuit if threshold reached.

    Args:
        gateway_url: URL of the gateway that failed.
        circuit_states: Mutable mapping updated in place.
    """
    state = circuit_states.setdefault(gateway_url, CircuitState())
    state.failure_count += 1
    state.last_failure_time = time.time()
    state.success_count = 0

    if state.failure_count >= CIRCUIT_FAILURE_THRESHOLD:
        state.circuit_open = True
        logging.warning(
            "CIRCUIT OPEN: Gateway %s (%d consecutive failures)",
            gateway_url,
            state.failure_count,
        )


def record_success(
    gateway_url: str,
    circuit_states: dict[str, CircuitState],
) -> None:
    """
    Reset failure state on success; fully recover after two consecutive wins.

    Args:
        gateway_url: URL of the gateway that succeeded.
        circuit_states: Mutable mapping updated in place.
    """
    state = circuit_states.setdefault(gateway_url, CircuitState())

    if state.circuit_open or state.failure_count > 0:
        state.failure_count = 0
        state.circuit_open = False
        state.success_count += 1

        if state.success_count >= 2:
            # Full recovery — clear success counter
            state.success_count = 0

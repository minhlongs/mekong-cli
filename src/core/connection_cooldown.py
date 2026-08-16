# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Connection-level cooldown with exponential backoff for API keys.

Tracks per-key cooldown state and applies exponential backoff on failures,
resetting to base cooldown on success.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_BASE_COOLDOWN = 5.0
DEFAULT_MAX_BACKOFF = 300.0


@dataclass
class CooldownState:
    """Tracks cooldown state for a single API key."""

    last_failure: float = 0.0
    consecutive_failures: int = 0
    current_backoff: float = 0.0


class ConnectionCooldown:
    """Per-key cooldown tracker with exponential backoff.

    Thread-safe singleton — access via :func:`get_connection_cooldown`.
    """

    def __init__(
        self,
        base_cooldown: float = DEFAULT_BASE_COOLDOWN,
        max_backoff: float = DEFAULT_MAX_BACKOFF,
    ) -> None:
        self.base_cooldown = base_cooldown
        self.max_backoff = max_backoff
        self._lock = threading.Lock()
        self._states: dict[str, CooldownState] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self, key_id: str) -> bool:
        """Return True if the key's cooldown has expired."""
        with self._lock:
            state = self._states.get(key_id)
            if state is None or state.current_backoff <= 0:
                return True
            elapsed = time.time() - state.last_failure
            return elapsed >= state.current_backoff

    def record_failure(self, key_id: str, retry_after: float | None = None) -> None:
        """Record a failure for *key_id*, updating exponential backoff.

        If *retry_after* is provided (e.g. from a Retry-After header) it
        overrides the computed backoff.
        """
        now = time.time()
        with self._lock:
            state = self._states.get(key_id)
            if state is None:
                state = CooldownState()
                self._states[key_id] = state

            state.consecutive_failures += 1
            state.last_failure = now

            if retry_after is not None and retry_after > 0:
                state.current_backoff = retry_after
            else:
                state.current_backoff = min(
                    self.base_cooldown * (2 ** (state.consecutive_failures - 1)),
                    self.max_backoff,
                )

            logger.info(
                "[ConnectionCooldown:%s] failure #%d, backoff=%.1fs",
                key_id,
                state.consecutive_failures,
                state.current_backoff,
            )

    def on_success(self, key_id: str) -> None:
        """Reset backoff to base cooldown after a successful call."""
        with self._lock:
            state = self._states.get(key_id)
            if state is not None:
                state.consecutive_failures = 0
                state.current_backoff = 0.0
                logger.info("[ConnectionCooldown:%s] success — backoff reset", key_id)

    def get_backoff(self, key_id: str) -> float:
        """Return the current backoff duration for *key_id* (0.0 if none)."""
        with self._lock:
            state = self._states.get(key_id)
            return state.current_backoff if state is not None else 0.0

    def reset(self, key_id: str) -> None:
        """Clear cooldown state for a single key."""
        with self._lock:
            self._states.pop(key_id, None)

    def reset_all(self) -> None:
        """Clear all cooldown states."""
        with self._lock:
            self._states.clear()


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

_instance: ConnectionCooldown | None = None
_instance_lock = threading.Lock()


def get_connection_cooldown() -> ConnectionCooldown:
    """Return the global ConnectionCooldown singleton (lazily created)."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = ConnectionCooldown()
    return _instance


def reset_cooldown_singleton() -> None:
    """Reset the global singleton (useful for tests)."""
    global _instance
    with _instance_lock:
        _instance = None

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Circuit breaker module (Legacy & Provider APIs)."""

from __future__ import annotations
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitOpenError(Exception):
    def __init__(self, service_name: str, retry_after: float) -> None:
        self.service_name, self.retry_after = service_name, retry_after
        super().__init__(f"Circuit open for '{service_name}'. Retry after {retry_after}s")

@dataclass
class Stats:
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    total_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0, success_threshold: int = 1, excluded_exceptions: tuple[type[Exception], ...] = ()) -> None:
        self.name, self.failure_threshold, self.recovery_timeout = name, failure_threshold, recovery_timeout
        self.success_threshold, self.excluded_exceptions = success_threshold, excluded_exceptions
        self._failure_count, self._success_count, self._state_changes = 0, 0, 0
        self._last_failure_time, self._state, self._lock = 0.0, CircuitState.CLOSED, threading.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state is CircuitState.OPEN and (time.time() - self._last_failure_time) >= self.recovery_timeout:
            self._set_state(CircuitState.HALF_OPEN)
        return self._state

    @property
    def service_name(self) -> str:
        return self.name

    @property
    def stats(self) -> Stats:
        return Stats(self._success_count, self._failure_count, self._failure_count, self._success_count + self._failure_count, self._failure_count if self._state is CircuitState.OPEN else 0, self._state_changes)

    def _set_state(self, new_state: CircuitState) -> None:
        if self._state is not new_state:
            self._state_changes += 1
        self._state = new_state

    def allow_request(self) -> bool:
        return self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN) or (time.time() - self._last_failure_time) >= self.recovery_timeout

    def on_success(self) -> None:
        with self._lock:
            self._success_count, self._failure_count = self._success_count + 1, 0
            if self._state is CircuitState.HALF_OPEN and self._success_count >= self.success_threshold:
                self._set_state(CircuitState.CLOSED)

    def on_failure(self, error: Exception | None = None) -> None:
        with self._lock:
            self._failure_count, self._last_failure_time = self._failure_count + 1, time.time()
            if self._state is CircuitState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                self._set_state(CircuitState.OPEN)

    def reset(self) -> None:
        with self._lock:
            self._failure_count, self._success_count, self._last_failure_time, self._state = 0, 0, 0.0, CircuitState.CLOSED

    def call(self, func: Callable[[], T], *, fallback: Callable[[], T] | None = None) -> T:
        if not self.allow_request():
            with self._lock:
                if self._state is CircuitState.OPEN and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                    self._set_state(CircuitState.HALF_OPEN)
                    self._success_count = 0
                if self._state is CircuitState.OPEN:
                    if fallback is not None:
                        return fallback()
                    raise CircuitOpenError(self.name, self.recovery_timeout)
        elif self._state is CircuitState.OPEN:
            with self._lock:
                self._set_state(CircuitState.HALF_OPEN)
                self._success_count = 0
        try:
            result = func()
            self.on_success()
            return result
        except Exception as error:
            if isinstance(error, self.excluded_exceptions):
                self.on_success()
                raise
            self.on_failure(error)
            raise

_breakers: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()

def get_circuit_breaker(name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0, success_threshold: int = 1) -> CircuitBreaker:
    with _registry_lock:
        if name not in _breakers:
            _breakers[name] = CircuitBreaker(name, failure_threshold, recovery_timeout, success_threshold)
        return _breakers[name]

def reset_all_breakers() -> int:
    with _registry_lock:
        count = len(_breakers)
        _breakers.clear()
        return count

@dataclass(frozen=True)
class ProviderHealth:
    consecutive_failures: int = 0
    last_failure_at: float = 0.0
    last_success_at: float = 0.0
    state: CircuitState = CircuitState.CLOSED

@dataclass
class ProviderCircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0
    _health: dict[str, ProviderHealth] = field(default_factory=dict, repr=False)

    def _key(self, provider_name: str, model_ref: str) -> str:
        return f"{provider_name}:{model_ref}"

    def health(self, provider_name: str, model_ref: str) -> ProviderHealth:
        return self._health.get(self._key(provider_name, model_ref), ProviderHealth())

    def record_success(self, provider_name: str, model_ref: str) -> None:
        key = self._key(provider_name, model_ref)
        prev = self._health.get(key)
        self._health[key] = ProviderHealth(0, prev.last_failure_at if prev else 0.0, time.time(), CircuitState.CLOSED)

    def record_failure(self, provider_name: str, model_ref: str) -> None:
        key = self._key(provider_name, model_ref)
        prev = self._health.get(key, ProviderHealth())
        failures = prev.consecutive_failures + 1
        state = CircuitState.OPEN if failures >= self.failure_threshold else CircuitState.CLOSED
        self._health[key] = ProviderHealth(failures, time.time(), prev.last_success_at, state)

    def can_attempt(self, provider_name: str, model_ref: str) -> bool:
        key = self._key(provider_name, model_ref)
        cur = self._health.get(key, ProviderHealth())
        if cur.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            return True
        if (time.time() - cur.last_failure_at) >= self.recovery_timeout_seconds:
            self._health[key] = ProviderHealth(cur.consecutive_failures, cur.last_failure_at, cur.last_success_at, CircuitState.HALF_OPEN)
            return True
        return False

    def should_degrade(self, provider_name: str, model_ref: str) -> bool:
        return not self.can_attempt(provider_name, model_ref)

    def reset(self, provider_name: str, model_ref: str) -> None:
        self._health[self._key(provider_name, model_ref)] = ProviderHealth()

__all__ = ["CircuitBreaker", "CircuitOpenError", "CircuitState", "ProviderCircuitBreaker", "ProviderHealth", "Stats", "get_circuit_breaker", "reset_all_breakers"]

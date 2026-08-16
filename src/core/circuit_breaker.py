# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Circuit breaker module.

Exposes both:
- Legacy API: CircuitBreaker, CircuitOpenError, get_circuit_breaker, reset_all_breakers
- Provider API: ProviderCircuitBreaker, ProviderHealth, CircuitState
"""

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
        self.service_name = service_name
        self.retry_after = retry_after
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
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        success_threshold: int = 1,
        excluded_exceptions: tuple[type[Exception], ...] = (),
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.excluded_exceptions = excluded_exceptions
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._state = CircuitState.CLOSED
        self._state_changes: int = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state is not CircuitState.OPEN:
            return self._state
        if (time.time() - self._last_failure_time) >= self.recovery_timeout:
            self._set_state(CircuitState.HALF_OPEN)
        return self._state

    @property
    def service_name(self) -> str:
        return self.name

    @property
    def stats(self) -> Stats:
        return Stats(
            successful_calls=self._success_count,
            failed_calls=self._failure_count,
            consecutive_failures=self._failure_count,
            total_calls=self._success_count + self._failure_count,
            rejected_calls=(
                self._failure_count if self._state is CircuitState.OPEN else 0
            ),
            state_changes=self._state_changes,
        )

    def _set_state(self, new_state: CircuitState) -> None:
        if self._state is not new_state:
            self._state_changes += 1
        self._state = new_state

    def allow_request(self) -> bool:
        if self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            return True
        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    def on_success(self) -> None:
        with self._lock:
            self._success_count += 1
            self._failure_count = 0
            if (
                self._state is CircuitState.HALF_OPEN
                and self._success_count >= self.success_threshold
            ):
                logger.info(
                    "[CircuitBreaker:%s] Closed after %d probe successes",
                    self.name,
                    self._success_count,
                )
                self._set_state(CircuitState.CLOSED)

    def on_failure(self, error: Exception | None = None) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state is CircuitState.HALF_OPEN:
                logger.warning(
                    "[CircuitBreaker:%s] HALF_OPEN failure -> OPEN (trip #%d)",
                    self.name,
                    self._failure_count,
                )
                self._set_state(CircuitState.OPEN)
                return
            if self._failure_count >= self.failure_threshold:
                logger.error(
                    "[CircuitBreaker:%s] Failure threshold reached (%d/%d) -> OPEN",
                    self.name,
                    self._failure_count,
                    self.failure_threshold,
                )
                self._set_state(CircuitState.OPEN)
            if error:
                logger.error(
                    "[CircuitBreaker:%s] Failure reason: %s", self.name, error
                )

    def reset(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._success_count = 0
            self._state = CircuitState.CLOSED
            self._last_failure_time = 0.0
            logger.info("[CircuitBreaker:%s] Reset", self.name)

    def call(self, func: Callable[[], T], *, fallback: Callable[[], T] | None = None) -> T:
        allowed = self.allow_request()
        if not allowed:
            with self._lock:
                if (
                    self._state is CircuitState.OPEN
                    and (time.time() - self._last_failure_time) >= self.recovery_timeout
                ):
                    self._set_state(CircuitState.HALF_OPEN)
                    self._success_count = 0
                    logger.info(
                        "[CircuitBreaker:%s] call()-promote -> HALF_OPEN", self.name
                    )
                if self._state is CircuitState.OPEN:
                    if fallback is not None:
                        return fallback()
                    raise CircuitOpenError(self.name, self.recovery_timeout)
        elif self._state is CircuitState.OPEN:
            # OPEN but allowed because timeout expired -> promote to HALF_OPEN
            with self._lock:
                self._set_state(CircuitState.HALF_OPEN)
                self._success_count = 0
                logger.info(
                    "[CircuitBreaker:%s] call()-promote -> HALF_OPEN", self.name
                )
        try:
            result = func()
            self.on_success()
            return result
        except Exception as error:
            if isinstance(error, self.excluded_exceptions):
                raise
            self.on_failure(error)
            raise


_breakers: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 3,
    recovery_timeout: float = 30.0,
    success_threshold: int = 1,
) -> CircuitBreaker:
    with _registry_lock:
        existing = _breakers.get(name)
        if existing is None:
            _breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
            )
            return _breakers[name]
        return existing


def reset_all_breakers() -> int:
    with _registry_lock:
        count = len(_breakers)
        _breakers.clear()
        return count


# Provider-specific circuit breaker types (Phase 4)
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
        return self._health.get(
            self._key(provider_name, model_ref), ProviderHealth()
        )

    def record_success(self, provider_name: str, model_ref: str) -> None:
        key = self._key(provider_name, model_ref)
        previous = self._health.get(key)
        self._health[key] = ProviderHealth(
            consecutive_failures=0,
            last_success_at=time.time(),
            state=CircuitState.CLOSED,
            last_failure_at=previous.last_failure_at if previous else 0.0,
        )

    def record_failure(self, provider_name: str, model_ref: str) -> None:
        key = self._key(provider_name, model_ref)
        previous = self._health.get(key, ProviderHealth())
        failures = previous.consecutive_failures + 1
        state = (
            CircuitState.OPEN
            if failures >= self.failure_threshold
            else CircuitState.CLOSED
        )
        now = time.time()
        self._health[key] = ProviderHealth(
            consecutive_failures=failures,
            last_failure_at=now,
            state=state,
            last_success_at=previous.last_success_at,
        )
        logger.warning(
            "provider=%s model=%s failure=%s state=%s",
            provider_name,
            model_ref,
            failures,
            state.value,
        )

    def can_attempt(self, provider_name: str, model_ref: str) -> bool:
        key = self._key(provider_name, model_ref)
        current = self._health.get(key, ProviderHealth())
        if current.state is CircuitState.CLOSED:
            return True
        if current.state is CircuitState.HALF_OPEN:
            return True
        age = time.time() - current.last_failure_at
        if age >= self.recovery_timeout_seconds:
            self._health[key] = ProviderHealth(
                consecutive_failures=current.consecutive_failures,
                last_failure_at=current.last_failure_at,
                last_success_at=current.last_success_at,
                state=CircuitState.HALF_OPEN,
            )
            logger.info(
                "provider=%s model=%s promoting to HALF_OPEN",
                provider_name,
                model_ref,
            )
            return True
        return False

    def should_degrade(self, provider_name: str, model_ref: str) -> bool:
        return not self.can_attempt(provider_name, model_ref)

    def reset(self, provider_name: str, model_ref: str) -> None:
        key = self._key(provider_name, model_ref)
        self._health[key] = ProviderHealth()
        logger.info(
            "provider=%s model=%s circuit reset",
            provider_name,
            model_ref,
        )


__all__ = [
    "CircuitBreaker",
    "CircuitOpenError",
    "CircuitState",
    "ProviderCircuitBreaker",
    "ProviderHealth",
    "Stats",
    "get_circuit_breaker",
    "reset_all_breakers",
]
"""Mekong CLI - Retry with Exponential Backoff.

Provides configurable exponential backoff for retrying transient failures.
Generous jitter to prevent thundering herd across concurrent workers.

Usage:
    from src.core.retry import ExponentialBackoff, call_with_retry

    backoff = ExponentialBackoff(initial=1.0, max_delay=30.0, factor=2.0)
    result = call_with_retry(
        lambda: unreliable_api.call(),
        max_attempts=4,
        backoff=backoff,
        on_retry=lambda attempt, delay: logger.info(f"retry {attempt} in {delay:.1f}s"),
    )
"""

from __future__ import annotations

import random
import time
import threading
from dataclasses import dataclass, field


@dataclass
class RetryStats:
    """Tracks outcome of a retry sequence."""

    attempts: int = 0
    succeeded: bool = False
    final_error: str | None = None
    delays: list[float] = field(default_factory=list)

    @property
    def total_delay(self) -> float:
        return sum(self.delays)


class ExponentialBackoff:
    """Thread-safe exponential backoff with jitter.

    Delay sequence: initial, initial*factor, initial*factor^2, ...
    Each delay is additionally jittered in [delay*0.5 .. delay*1.5].
    Delays are clamped to max_delay.

    Args:
        initial:    First retry delay in seconds (default 1.0).
        max_delay:  Ceiling for any single delay (default 30.0).
        factor:     Multiplier applied after each attempt (default 2.0).
    """

    def __init__(
        self,
        initial: float = 1.0,
        max_delay: float = 30.0,
        factor: float = 2.0,
    ) -> None:
        self.initial = float(initial)
        self.max_delay = float(max_delay)
        self.factor = float(factor)
        self._lock = threading.Lock()
        self._attempt: int = 0

    def next_delay(self) -> float:
        """Return the delay for the upcoming retry, advancing the counter."""
        with self._lock:
            delay = self.initial * (self.factor ** self._attempt)
            delay = min(delay, self.max_delay)
            jittered = delay * (0.5 + random.random())
            self._attempt += 1
            return round(jittered, 3)

    def reset(self) -> None:
        """Reset counter back to zero."""
        with self._lock:
            self._attempt = 0

    def __repr__(self) -> str:
        return (
            f"ExponentialBackoff(initial={self.initial},"
            f" max_delay={self.max_delay}, factor={self.factor})"
        )


def call_with_retry(
    func,
    *,
    max_attempts: int = 3,
    backoff: ExponentialBackoff | None = None,
    retryable: tuple[type[Exception], ...] | None = None,
    on_retry: callable | None = None,
) -> tuple[bool, object, RetryStats]:
    """Call *func* up to *max_attempts* times with exponential backoff.

    Args:
        func:        Zero-argument callable.
        max_attempts: Total attempts (first call + retries), minimum 1.
        backoff:     ExponentialBackoff instance; created with defaults if omitted.
        retryable:   Exception types that trigger a retry. Default: Exception (retry any).
        on_retry:    Optional callback ``(attempt_number: int, delay: float) -> None``
                     invoked after the sleep, before the next call.

    Returns:
        (success, result_or_error, stats)
    """
    if backoff is None:
        backoff = ExponentialBackoff()
    if retryable is None:
        retryable = (Exception,)

    attempts = 0
    delays: list[float] = []
    last_exc: Exception | None = None

    while attempts < max_attempts:
        attempts += 1
        try:
            result = func()
            stats = RetryStats(
                attempts=attempts, succeeded=True, delays=list(delays),
            )
            return True, result, stats
        except retryable as exc:
            last_exc = exc
            if attempts >= max_attempts:
                break
            delay = backoff.next_delay()
            delays.append(delay)
            if on_retry:
                on_retry(attempts, delay)
            time.sleep(delay)

    stats = RetryStats(
        attempts=attempts,
        succeeded=False,
        final_error=str(last_exc) if last_exc else "unknown",
        delays=list(delays),
    )
    return False, last_exc, stats


__all__ = [
    "ExponentialBackoff",
    "RetryStats",
    "call_with_retry",
]

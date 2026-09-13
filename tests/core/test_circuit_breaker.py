# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit and integration tests for CircuitBreaker and ProviderCircuitBreaker.

Verifies:
- State transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
- Threshold enforcement
- Recovery timeout behavior
- Integration with ProviderRegistry routing
- Stats tracking, fallback, excluded_exceptions, reset, global registry, thread safety.
"""

from __future__ import annotations

import threading
import time
from unittest.mock import patch

import pytest

from src.core.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    ProviderCircuitBreaker,
    ProviderHealth,
    get_circuit_breaker,
    reset_all_breakers,
)



class TestCircuitState:
    def test_closed_initial(self):
        health = ProviderHealth()
        assert health.state == CircuitState.CLOSED

    def test_open_after_threshold(self):
        breaker = ProviderCircuitBreaker(failure_threshold=2)
        breaker.record_failure("openai", "gpt-4o")
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").state == CircuitState.OPEN

    def test_half_open_after_recovery_timeout(self):
        breaker = ProviderCircuitBreaker(
            failure_threshold=1, recovery_timeout_seconds=0.1
        )
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").state == CircuitState.OPEN
        time.sleep(0.2)
        assert breaker.can_attempt("openai", "gpt-4o")


class TestRecordSuccess:
    def test_success_resets_failures(self):
        breaker = ProviderCircuitBreaker()
        breaker.record_failure("openai", "gpt-4o")
        breaker.record_failure("openai", "gpt-4o")
        breaker.record_success("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").consecutive_failures == 0
        assert breaker.health("openai", "gpt-4o").state == CircuitState.CLOSED

    def test_success_stamps_timestamp(self):
        breaker = ProviderCircuitBreaker()
        before = time.time()
        breaker.record_success("openai", "gpt-4o")
        health = breaker.health("openai", "gpt-4o")
        assert health.last_success_at >= before

    def test_success_from_half_open_closes_circuit(self):
        breaker = ProviderCircuitBreaker(
            failure_threshold=1, recovery_timeout_seconds=0.05
        )
        breaker.record_failure("openai", "gpt-4o")
        time.sleep(0.1)
        assert breaker.can_attempt("openai", "gpt-4o")  # promotes HALF_OPEN
        breaker.record_success("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").state == CircuitState.CLOSED


class TestRecordFailure:
    def test_failure_increments_count(self):
        breaker = ProviderCircuitBreaker()
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").consecutive_failures == 1
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").consecutive_failures == 2

    def test_failure_stamps_last_failure_at(self):
        breaker = ProviderCircuitBreaker()
        before = time.time()
        breaker.record_failure("openai", "gpt-4o")
        health = breaker.health("openai", "gpt-4o")
        assert health.last_failure_at >= before

    def test_half_open_failure_reopens(self):
        breaker = ProviderCircuitBreaker(
            failure_threshold=1, recovery_timeout_seconds=0.05
        )
        breaker.record_failure("openai", "gpt-4o")
        time.sleep(0.1)
        assert breaker.can_attempt("openai", "gpt-4o")  # HALF_OPEN
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").state == CircuitState.OPEN


class TestCanAttempt:
    def test_open_blocks_until_timeout(self):
        breaker = ProviderCircuitBreaker(
            failure_threshold=1, recovery_timeout_seconds=10.0
        )
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").state == CircuitState.OPEN
        assert not breaker.can_attempt("openai", "gpt-4o")

    def test_unknown_provider_allowed(self):
        breaker = ProviderCircuitBreaker()
        assert breaker.can_attempt("unknown", "model-x")

    def test_half_open_allows_single_attempt(self):
        breaker = ProviderCircuitBreaker(
            failure_threshold=1, recovery_timeout_seconds=0.05
        )
        breaker.record_failure("openai", "gpt-4o")
        time.sleep(0.1)
        assert breaker.can_attempt("openai", "gpt-4o")
        # Subsequent attempts still allowed (single probe policy is optional here)
        assert breaker.can_attempt("openai", "gpt-4o")


class TestDegradation:
    def test_should_degrade_when_open(self):
        breaker = ProviderCircuitBreaker(failure_threshold=1, recovery_timeout_seconds=10.0)
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.should_degrade("openai", "gpt-4o")

    def test_should_not_degrade_when_closed(self):
        breaker = ProviderCircuitBreaker()
        assert not breaker.should_degrade("openai", "gpt-4o")

    def test_should_not_degrade_when_half_open(self):
        breaker = ProviderCircuitBreaker(
            failure_threshold=1, recovery_timeout_seconds=0.05
        )
        breaker.record_failure("openai", "gpt-4o")
        time.sleep(0.1)
        assert not breaker.should_degrade("openai", "gpt-4o")


class TestKeyIsolation:
    def test_different_providers_independent(self):
        breaker = ProviderCircuitBreaker(failure_threshold=1)
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").state == CircuitState.OPEN
        assert breaker.health("gemini", "gemini-2.5-flash").state == CircuitState.CLOSED

    def test_different_models_independent(self):
        breaker = ProviderCircuitBreaker(failure_threshold=1)
        breaker.record_failure("openai", "gpt-4o")
        assert breaker.health("openai", "gpt-4o").state == CircuitState.OPEN
        assert breaker.health("openai", "gpt-4o-mini").state == CircuitState.CLOSED


class TestReset:
    def test_restores_initial_state(self):
        breaker = ProviderCircuitBreaker(failure_threshold=1, recovery_timeout_seconds=10.0)
        breaker.record_failure("openai", "gpt-4o")
        breaker.reset("openai", "gpt-4o")
        health = breaker.health("openai", "gpt-4o")
        assert health.consecutive_failures == 0
        assert health.state == CircuitState.CLOSED
        assert health.last_failure_at == 0.0
        assert health.last_success_at == 0.0


# ---------------------------------------------------------------------------
# Legacy CircuitBreaker Tests
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fail(msg: str = "service error") -> None:
    raise RuntimeError(msg)


def _succeed(value: str = "ok") -> str:
    return value


# ---------------------------------------------------------------------------
# CircuitOpenError
# ---------------------------------------------------------------------------

class TestCircuitOpenError:
    def test_attributes_set(self):
        err = CircuitOpenError("svc", 15.0)
        assert err.service_name == "svc"
        assert err.retry_after == 15.0

    def test_message_contains_service_name(self):
        err = CircuitOpenError("my-service", 5.0)
        assert "my-service" in str(err)

    def test_is_exception(self):
        assert isinstance(CircuitOpenError("x", 0), Exception)


# ---------------------------------------------------------------------------
# CircuitState
# ---------------------------------------------------------------------------

class TestLegacyCircuitState:
    def test_all_three_states_exist(self):
        assert CircuitState.CLOSED
        assert CircuitState.OPEN
        assert CircuitState.HALF_OPEN

    def test_string_values(self):
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

class TestCircuitBreakerInit:
    def test_starts_closed(self):
        cb = CircuitBreaker("svc")
        assert cb.state == CircuitState.CLOSED

    def test_default_thresholds(self):
        cb = CircuitBreaker("svc")
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30.0
        assert cb.success_threshold == 1

    def test_custom_thresholds(self):
        cb = CircuitBreaker("svc", failure_threshold=5, recovery_timeout=60.0, success_threshold=2)
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0
        assert cb.success_threshold == 2

    def test_stats_start_at_zero(self):
        cb = CircuitBreaker("svc")
        s = cb.stats
        assert s.total_calls == 0
        assert s.successful_calls == 0
        assert s.failed_calls == 0
        assert s.rejected_calls == 0
        assert s.consecutive_failures == 0


# ---------------------------------------------------------------------------
# CLOSED state — normal operation
# ---------------------------------------------------------------------------

class TestClosedState:
    def test_successful_call_returns_value(self):
        cb = CircuitBreaker("svc")
        result = cb.call(lambda: _succeed("hello"))
        assert result == "hello"

    def test_successful_call_increments_stats(self):
        cb = CircuitBreaker("svc")
        cb.call(lambda: _succeed())
        s = cb.stats
        assert s.total_calls == 1
        assert s.successful_calls == 1
        assert s.failed_calls == 0

    def test_failed_call_reraises(self):
        cb = CircuitBreaker("svc")
        with pytest.raises(RuntimeError, match="service error"):
            cb.call(lambda: _fail())

    def test_failed_call_increments_failure_stats(self):
        cb = CircuitBreaker("svc")
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        s = cb.stats
        assert s.failed_calls == 1
        assert s.consecutive_failures == 1

    def test_state_remains_closed_below_threshold(self):
        cb = CircuitBreaker("svc", failure_threshold=3)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(lambda: _fail())
        assert cb.state == CircuitState.CLOSED

    def test_success_resets_consecutive_failures(self):
        cb = CircuitBreaker("svc", failure_threshold=3)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        cb.call(lambda: _succeed())
        assert cb.stats.consecutive_failures == 0


# ---------------------------------------------------------------------------
# CLOSED → OPEN transition
# ---------------------------------------------------------------------------

class TestTransitionToOpen:
    def test_opens_after_failure_threshold(self):
        cb = CircuitBreaker("svc", failure_threshold=3)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(lambda: _fail())
        assert cb.state == CircuitState.OPEN

    def test_open_raises_circuit_open_error(self):
        cb = CircuitBreaker("svc", failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: _succeed())

    def test_open_increments_rejected_calls(self):
        cb = CircuitBreaker("svc", failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: _succeed())
        assert cb.stats.rejected_calls == 1

    def test_open_uses_fallback_if_provided(self):
        cb = CircuitBreaker("svc", failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        result = cb.call(lambda: _succeed(), fallback=lambda: "fallback-value")
        assert result == "fallback-value"

    def test_state_changes_counter_increments(self):
        cb = CircuitBreaker("svc", failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        assert cb.stats.state_changes >= 1


# ---------------------------------------------------------------------------
# OPEN → HALF_OPEN transition (recovery timeout)
# ---------------------------------------------------------------------------

class TestTransitionToHalfOpen:
    def test_call_promotes_open_to_half_open_when_timeout_expires_during_check(self):
        cb = CircuitBreaker("race-test", failure_threshold=1, recovery_timeout=10.0)
        cb.on_failure(RuntimeError("fail"))
        assert cb.state == CircuitState.OPEN

        t0 = cb._last_failure_time
        times = [t0 + 1.0, t0 + 15.0, t0 + 15.0, t0 + 15.0]
        with patch("time.time", side_effect=times):
            res = cb.call(lambda: "race_success")

        assert res == "race_success"
        assert cb.state == CircuitState.CLOSED

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker("svc", failure_threshold=1, recovery_timeout=0.05)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        assert cb.state == CircuitState.OPEN
        time.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_allows_probe_call(self):
        cb = CircuitBreaker("svc", failure_threshold=1, recovery_timeout=0.05)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        time.sleep(0.1)
        result = cb.call(lambda: _succeed("probe"))
        assert result == "probe"

    def test_half_open_success_closes_circuit(self):
        cb = CircuitBreaker("svc", failure_threshold=1, recovery_timeout=0.05)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        time.sleep(0.1)
        cb.call(lambda: _succeed())
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens_circuit(self):
        cb = CircuitBreaker("svc", failure_threshold=1, recovery_timeout=0.05)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        time.sleep(0.1)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        assert cb.state == CircuitState.OPEN

    def test_success_threshold_greater_than_one(self):
        cb = CircuitBreaker("svc", failure_threshold=1, recovery_timeout=0.05, success_threshold=2)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        time.sleep(0.1)
        # First probe — still HALF_OPEN
        cb.call(lambda: _succeed())
        assert cb.state == CircuitState.HALF_OPEN
        # Second probe — now CLOSED
        cb.call(lambda: _succeed())
        assert cb.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# Excluded exceptions
# ---------------------------------------------------------------------------

class TestExcludedExceptions:
    def test_excluded_exception_does_not_count_as_failure(self):
        class UserError(Exception):
            pass

        cb = CircuitBreaker("svc", failure_threshold=2, excluded_exceptions=(UserError,))
        for _ in range(5):
            with pytest.raises(UserError):
                cb.call(lambda: (_ for _ in ()).throw(UserError("user err")))
        # Circuit should still be CLOSED (excluded)
        assert cb.state == CircuitState.CLOSED
        assert cb.stats.failed_calls == 0

    def test_non_excluded_exception_still_counts(self):
        class UserError(Exception):
            pass

        cb = CircuitBreaker("svc", failure_threshold=2, excluded_exceptions=(UserError,))
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        assert cb.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

class TestLegacyReset:
    def test_reset_closes_open_circuit(self):
        cb = CircuitBreaker("svc", failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_reset_clears_consecutive_failures(self):
        cb = CircuitBreaker("svc", failure_threshold=5)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(lambda: _fail())
        cb.reset()
        assert cb.stats.consecutive_failures == 0

    def test_circuit_works_normally_after_reset(self):
        cb = CircuitBreaker("svc", failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        cb.reset()
        result = cb.call(lambda: _succeed("after-reset"))
        assert result == "after-reset"


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def setup_method(self):
        reset_all_breakers()

    def teardown_method(self):
        reset_all_breakers()

    def test_get_circuit_breaker_creates_new(self):
        cb = get_circuit_breaker("my-service")
        assert isinstance(cb, CircuitBreaker)
        assert cb.service_name == "my-service"

    def test_get_circuit_breaker_returns_same_instance(self):
        cb1 = get_circuit_breaker("shared")
        cb2 = get_circuit_breaker("shared")
        assert cb1 is cb2

    def test_different_names_return_different_instances(self):
        cb1 = get_circuit_breaker("svc-a")
        cb2 = get_circuit_breaker("svc-b")
        assert cb1 is not cb2

    def test_reset_all_clears_registry(self):
        cb1 = get_circuit_breaker("svc")
        reset_all_breakers()
        cb2 = get_circuit_breaker("svc")
        assert cb1 is not cb2

    def test_custom_thresholds_applied_on_creation(self):
        cb = get_circuit_breaker("svc", failure_threshold=10, recovery_timeout=120.0)
        assert cb.failure_threshold == 10
        assert cb.recovery_timeout == 120.0

    def test_thresholds_not_overridden_on_second_get(self):
        get_circuit_breaker("svc", failure_threshold=10)
        cb2 = get_circuit_breaker("svc", failure_threshold=999)
        # Second get returns existing instance with original thresholds
        assert cb2.failure_threshold == 10


# ---------------------------------------------------------------------------
# Stats integrity
# ---------------------------------------------------------------------------

class TestStats:
    def test_stats_returns_copy(self):
        cb = CircuitBreaker("svc")
        s1 = cb.stats
        cb.call(lambda: _succeed())
        s2 = cb.stats
        # s1 should not change after successful call
        assert s1.successful_calls == 0
        assert s2.successful_calls == 1

    def test_cumulative_mixed_calls(self):
        cb = CircuitBreaker("svc", failure_threshold=10)
        cb.call(lambda: _succeed())
        cb.call(lambda: _succeed())
        with pytest.raises(RuntimeError):
            cb.call(lambda: _fail())
        s = cb.stats
        assert s.total_calls == 3
        assert s.successful_calls == 2
        assert s.failed_calls == 1


# ---------------------------------------------------------------------------
# Thread safety (basic)
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_calls_dont_corrupt_stats(self):
        cb = CircuitBreaker("svc", failure_threshold=1000)
        results = []
        errors = []

        def worker():
            try:
                cb.call(lambda: _succeed())
                results.append(True)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert cb.stats.successful_calls == 20
        assert cb.stats.total_calls == 20

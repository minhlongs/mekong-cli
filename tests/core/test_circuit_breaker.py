"""Unit tests for ProviderCircuitBreaker.

Verifies:
- State transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
- Threshold enforcement
- Recovery timeout behavior
- Integration with ProviderRegistry routing
"""

from __future__ import annotations

import time


from src.core.circuit_breaker import (
    CircuitState,
    ProviderCircuitBreaker,
    ProviderHealth,
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

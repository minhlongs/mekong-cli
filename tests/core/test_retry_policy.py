"""Tests for RetryPolicy, BackoffStrategy, and execute_with_retry in src.core.retry_policy."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from src.core.retry_policy import (
    AGGRESSIVE_RETRY,
    CONSERVATIVE_RETRY,
    LLM_RETRY,
    NO_RETRY,
    BackoffStrategy,
    RetryPolicy,
    execute_with_retry,
)


class TestBackoffStrategy:
    """Test BackoffStrategy enum values."""

    def test_enum_values(self) -> None:
        assert BackoffStrategy.FIXED == "fixed"
        assert BackoffStrategy.EXPONENTIAL == "exponential"
        assert BackoffStrategy.FULL_JITTER == "full_jitter"
        assert BackoffStrategy.EQUAL_JITTER == "equal_jitter"


class TestRetryPolicyDefaults:
    """Test RetryPolicy default attributes and configuration."""

    def test_default_values(self) -> None:
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.initial_interval_seconds == 1.0
        assert policy.backoff_coefficient == 2.0
        assert policy.max_interval_seconds == 60.0
        assert policy.strategy == BackoffStrategy.FULL_JITTER
        assert policy.non_retryable_errors == []
        assert policy.non_retryable_exit_codes == [2]


class TestComputeDelay:
    """Test compute_delay across all backoff strategies and boundary caps."""

    def test_fixed_strategy(self) -> None:
        policy = RetryPolicy(
            initial_interval_seconds=2.5,
            strategy=BackoffStrategy.FIXED,
        )
        assert policy.compute_delay(0) == 2.5
        assert policy.compute_delay(1) == 2.5
        assert policy.compute_delay(5) == 2.5

    def test_exponential_strategy(self) -> None:
        policy = RetryPolicy(
            initial_interval_seconds=1.0,
            backoff_coefficient=2.0,
            max_interval_seconds=10.0,
            strategy=BackoffStrategy.EXPONENTIAL,
        )
        assert policy.compute_delay(0) == 1.0
        assert policy.compute_delay(1) == 2.0
        assert policy.compute_delay(2) == 4.0
        assert policy.compute_delay(3) == 8.0
        # Capped by max_interval_seconds
        assert policy.compute_delay(4) == 10.0
        assert policy.compute_delay(10) == 10.0

    def test_full_jitter_strategy(self) -> None:
        policy = RetryPolicy(
            initial_interval_seconds=2.0,
            backoff_coefficient=2.0,
            max_interval_seconds=20.0,
            strategy=BackoffStrategy.FULL_JITTER,
        )
        with patch("random.uniform", return_value=1.75) as mock_rand:
            delay = policy.compute_delay(1)
            assert delay == 1.75
            mock_rand.assert_called_once_with(0, 4.0)

    def test_equal_jitter_strategy(self) -> None:
        policy = RetryPolicy(
            initial_interval_seconds=2.0,
            backoff_coefficient=2.0,
            max_interval_seconds=20.0,
            strategy=BackoffStrategy.EQUAL_JITTER,
        )
        # base = 2.0 * (2.0 ** 1) = 4.0; half = 2.0
        with patch("random.uniform", return_value=0.5) as mock_rand:
            delay = policy.compute_delay(1)
            assert delay == 2.5  # half (2.0) + 0.5
            mock_rand.assert_called_once_with(0, 2.0)

    def test_unknown_or_custom_strategy_fallback_returns_base(self) -> None:
        policy = RetryPolicy(
            initial_interval_seconds=3.0,
            backoff_coefficient=2.0,
            max_interval_seconds=30.0,
            strategy="unrecognized_strategy",  # type: ignore[arg-type]
        )
        assert policy.compute_delay(1) == 6.0


class TestIsRetryable:
    """Test error message and exit code filtering."""

    def test_non_retryable_exit_code(self) -> None:
        policy = RetryPolicy(non_retryable_exit_codes=[2, 127])
        assert policy.is_retryable("some error", exit_code=2) is False
        assert policy.is_retryable("some error", exit_code=127) is False
        assert policy.is_retryable("some error", exit_code=1) is True

    def test_non_retryable_errors_case_insensitive(self) -> None:
        policy = RetryPolicy(non_retryable_errors=["AuthError", "RATE_LIMIT_EXCEEDED"])
        assert policy.is_retryable("Fatal: autherror occurred", exit_code=1) is False
        assert policy.is_retryable("System rate_limit_exceeded now", exit_code=1) is False
        assert policy.is_retryable("Normal connection timeout", exit_code=1) is True

    def test_no_non_retryable_rules_permits_all(self) -> None:
        policy = RetryPolicy(non_retryable_errors=[], non_retryable_exit_codes=[])
        assert policy.is_retryable("any catastrophic failure", exit_code=99) is True


class TestShouldRetry:
    """Test should_retry decision logic."""

    def test_attempt_exceeds_or_equals_max_attempts(self) -> None:
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(0, "transient") is True
        assert policy.should_retry(1, "transient") is True
        assert policy.should_retry(2, "transient") is True
        assert policy.should_retry(3, "transient") is False
        assert policy.should_retry(4, "transient") is False

    def test_attempt_within_limit_but_error_non_retryable(self) -> None:
        policy = RetryPolicy(max_attempts=5, non_retryable_errors=["forbidden"])
        assert policy.should_retry(1, "403 Forbidden") is False
        assert policy.should_retry(1, "500 Internal Server Error") is True


class TestExecuteWithRetry:
    """Test execute_with_retry helper function."""

    @patch("time.sleep")
    def test_success_on_first_try(self, mock_sleep: MagicMock) -> None:
        func = MagicMock(return_value="success_val")
        res = execute_with_retry(func)
        assert res == "success_val"
        func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_success_after_transient_failures(self, mock_sleep: MagicMock) -> None:
        attempts = 0

        def flaky() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError(f"failure {attempts}")
            return "recovered"

        policy = RetryPolicy(
            max_attempts=4,
            initial_interval_seconds=0.1,
            strategy=BackoffStrategy.FIXED,
        )
        on_retry = MagicMock()

        res = execute_with_retry(flaky, policy=policy, on_retry=on_retry)
        assert res == "recovered"
        assert attempts == 3
        assert mock_sleep.call_count == 2
        assert on_retry.call_count == 2
        # Verify on_retry callback args: (attempt + 1, delay, error_msg)
        on_retry.assert_any_call(1, 0.1, "failure 1")
        on_retry.assert_any_call(2, 0.1, "failure 2")

    @patch("time.sleep")
    def test_non_retryable_error_raises_immediately(self, mock_sleep: MagicMock) -> None:
        policy = RetryPolicy(
            max_attempts=5,
            non_retryable_errors=["permission_denied"],
        )
        func = MagicMock(side_effect=PermissionError("permission_denied on file"))

        with pytest.raises(PermissionError, match="permission_denied"):
            execute_with_retry(func, policy=policy)

        func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_exhausted_retries_raises_last_error(self, mock_sleep: MagicMock) -> None:
        policy = RetryPolicy(
            max_attempts=3,
            initial_interval_seconds=0.01,
            strategy=BackoffStrategy.FIXED,
        )
        func = MagicMock(side_effect=RuntimeError("persistent failure"))

        with pytest.raises(RuntimeError, match="persistent failure"):
            execute_with_retry(func, policy=policy)

        assert func.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_custom_should_retry_bypasses_loop_exit_forcing_fallback(self, mock_sleep: MagicMock) -> None:
        """Forces the loop to complete fully by mocking should_retry, hitting the defensive raise."""
        policy = RetryPolicy(max_attempts=2)
        func = MagicMock(side_effect=ValueError("bad value"))

        with patch.object(policy, "should_retry", return_value=True):
            with pytest.raises(ValueError, match="bad value"):
                execute_with_retry(func, policy=policy)

        # Loop executed twice, should_retry forced to return True on max attempt,
        # so sleep was called twice before loop exited and hit fallback raise
        assert func.call_count == 2
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_zero_max_attempts_returns_none(self, mock_sleep: MagicMock) -> None:
        policy = RetryPolicy(max_attempts=0)
        func = MagicMock(return_value="never_called")
        res = execute_with_retry(func, policy=policy)
        assert res is None
        func.assert_not_called()
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_default_policy_used_when_none(self, mock_sleep: MagicMock) -> None:
        attempts = 0

        def flaky() -> str:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise ConnectionResetError("reset")
            return "ok"

        res = execute_with_retry(flaky, policy=None)
        assert res == "ok"
        assert attempts == 2
        assert mock_sleep.call_count == 1


class TestPreconfiguredPolicies:
    """Test pre-configured retry policies."""

    def test_aggressive_retry(self) -> None:
        assert AGGRESSIVE_RETRY.max_attempts == 5
        assert AGGRESSIVE_RETRY.initial_interval_seconds == 0.5
        assert AGGRESSIVE_RETRY.backoff_coefficient == 1.5
        assert AGGRESSIVE_RETRY.strategy == BackoffStrategy.FULL_JITTER

    def test_conservative_retry(self) -> None:
        assert CONSERVATIVE_RETRY.max_attempts == 2
        assert CONSERVATIVE_RETRY.initial_interval_seconds == 2.0
        assert CONSERVATIVE_RETRY.backoff_coefficient == 3.0
        assert CONSERVATIVE_RETRY.max_interval_seconds == 30.0
        assert CONSERVATIVE_RETRY.strategy == BackoffStrategy.EQUAL_JITTER

    def test_llm_retry(self) -> None:
        assert LLM_RETRY.max_attempts == 3
        assert LLM_RETRY.initial_interval_seconds == 1.0
        assert LLM_RETRY.backoff_coefficient == 2.0
        assert LLM_RETRY.max_interval_seconds == 30.0
        assert LLM_RETRY.strategy == BackoffStrategy.FULL_JITTER
        assert "invalid_api_key" in LLM_RETRY.non_retryable_errors
        assert "authentication" in LLM_RETRY.non_retryable_errors
        assert "forbidden" in LLM_RETRY.non_retryable_errors

    def test_no_retry(self) -> None:
        assert NO_RETRY.max_attempts == 1


class TestPublicExports:
    """Verify all symbols exported in __all__ are defined."""

    def test_all_symbols_present(self) -> None:
        import src.core.retry_policy as mod

        for symbol in mod.__all__:
            assert hasattr(mod, symbol)
        assert set(mod.__all__) == {
            "AGGRESSIVE_RETRY",
            "CONSERVATIVE_RETRY",
            "LLM_RETRY",
            "NO_RETRY",
            "BackoffStrategy",
            "RetryPolicy",
            "execute_with_retry",
        }

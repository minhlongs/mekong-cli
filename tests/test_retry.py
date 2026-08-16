"""Tests for exponential backoff + call_with_retry (Phase C3 - retry.py)."""

import threading

import pytest

from src.core.retry import ExponentialBackoff, call_with_retry


class TestExponentialBackoffInit:
    def test_default_params(self):
        b = ExponentialBackoff()
        assert b.initial == 1.0
        assert b.max_delay == 30.0
        assert b.factor == 2.0

    def test_custom_params(self):
        b = ExponentialBackoff(initial=0.5, max_delay=10.0, factor=3.0)
        assert b.initial == 0.5
        assert b.max_delay == 10.0
        assert b.factor == 3.0


class TestExponentialBackoffDelays:
    def test_first_delay_equals_initial(self):
        b = ExponentialBackoff(initial=1.0, max_delay=30.0, factor=2.0)
        d = b.next_delay()
        assert 0.5 <= d <= 1.5

    def test_delay_doubles_each_attempt(self):
        b = ExponentialBackoff(initial=1.0, max_delay=30.0, factor=2.0)
        delays = [b.next_delay() for _ in range(6)]
        expected = [1.0, 2.0, 4.0, 8.0, 16.0, 30.0]
        for got, exp in zip(delays, expected):
            assert got == pytest.approx(exp, rel=0.6)

    def test_delay_clamped_to_max(self):
        b = ExponentialBackoff(initial=1.0, max_delay=5.0, factor=2.0)
        b.next_delay()
        b.next_delay()
        b.next_delay()
        d = b.next_delay()
        # After clamp, raw=5.0; jitter [0.5..1.5] => max 7.5
        # Without clamp, raw would be 8.0+ (wider range)
        assert d <= 5.0 * 1.5

    def test_jitter_range(self):
        b = ExponentialBackoff(initial=10.0, max_delay=30.0, factor=2.0)
        raw = 10.0
        for _ in range(20):
            d = b.next_delay()
            assert raw * 0.5 <= d <= raw * 1.5
            raw = min(raw * 2.0, 30.0)


class TestExponentialBackoffReset:
    def test_reset_restarts_sequence(self):
        b = ExponentialBackoff(initial=1.0, max_delay=30.0, factor=2.0)
        b.next_delay()
        b.reset()
        d = b.next_delay()
        assert 0.5 <= d <= 1.5


class TestExponentialBackoffRepr:
    def test_repr(self):
        b = ExponentialBackoff(initial=1.0, max_delay=30.0, factor=2.0)
        r = repr(b)
        assert "ExponentialBackoff" in r
        assert "initial=1.0" in r
        assert "max_delay=30.0" in r


class TestCallWithRetrySuccess:
    def test_succeeds_on_first_try(self):
        calls = 0

        def fn():
            nonlocal calls
            calls += 1
            return "ok"

        success, result, stats = call_with_retry(fn, max_attempts=3)
        assert success is True
        assert result == "ok"
        assert stats.attempts == 1
        assert stats.succeeded is True
        assert stats.delays == []

    def test_retries_then_succeeds(self):
        calls = 0

        def fn():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("transient")
            return "recovered"

        success, result, stats = call_with_retry(
            fn, max_attempts=5,
            backoff=ExponentialBackoff(initial=0.0, max_delay=0.0, factor=1.0),
        )
        assert success is True
        assert result == "recovered"
        assert stats.attempts == 3
        assert len(stats.delays) == 2


class TestCallWithRetryFailure:
    def test_exhausts_retries(self):
        def fn():
            raise RuntimeError("always fails")

        success, result, stats = call_with_retry(
            fn, max_attempts=3,
            backoff=ExponentialBackoff(initial=0.0, max_delay=0.0, factor=1.0),
        )
        assert success is False
        assert isinstance(result, RuntimeError)
        assert stats.attempts == 3
        assert stats.succeeded is False
        assert "always fails" in stats.final_error

    def test_non_retryable_exception_propagates(self):
        def fn():
            raise TypeError("not retryable")

        with pytest.raises(TypeError, match="not retryable"):
            call_with_retry(
                fn, max_attempts=5, retryable=(ValueError,),
                backoff=ExponentialBackoff(initial=0.0, max_delay=0.0, factor=1.0),
            )


class TestCallWithRetryCallback:
    def test_on_retry_callback_called(self):
        retry_log = []

        def on_retry(attempt, delay):
            retry_log.append((attempt, round(delay, 3)))

        def fn():
            raise RuntimeError("fail")

        call_with_retry(
            fn, max_attempts=3,
            backoff=ExponentialBackoff(initial=2.0, max_delay=10.0, factor=2.0),
            on_retry=on_retry,
        )
        assert len(retry_log) == 2
        assert retry_log[0][0] == 1
        assert retry_log[1][0] == 2


class TestCallWithRetryDefaultBackoff:
    def test_works_without_explicit_backoff(self):
        def fn():
            return "ok"

        success, result, _ = call_with_retry(fn, max_attempts=2)
        assert success is True
        assert result == "ok"


class TestBackoffThreadSafety:
    def test_concurrent_next_delay(self):
        b = ExponentialBackoff(initial=1.0, max_delay=30.0, factor=2.0)
        results = []
        errors = []

        def worker():
            try:
                for _ in range(10):
                    results.append(b.next_delay())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert len(results) == 80
        assert all(d >= 0 for d in results)

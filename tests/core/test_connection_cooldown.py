"""Tests for connection cooldown module."""

from __future__ import annotations

import threading
import time

import pytest

from src.core.connection_cooldown import (
    ConnectionCooldown,
    get_connection_cooldown,
    reset_cooldown_singleton,
)


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Ensure a fresh singleton for every test."""
    reset_cooldown_singleton()
    yield
    reset_cooldown_singleton()


# ------------------------------------------------------------------
# is_available
# ------------------------------------------------------------------


class TestIsAvailable:
    def test_new_key_is_available(self) -> None:
        cd = ConnectionCooldown()
        assert cd.is_available("key-1") is True

    def test_key_available_after_backoff_expires(self) -> None:
        cd = ConnectionCooldown(base_cooldown=0.05)
        cd.record_failure("key-1")
        assert cd.is_available("key-1") is False
        time.sleep(0.1)
        assert cd.is_available("key-1") is True

    def test_available_after_success(self) -> None:
        cd = ConnectionCooldown(base_cooldown=60)
        cd.record_failure("key-1")
        assert cd.is_available("key-1") is False
        cd.on_success("key-1")
        assert cd.is_available("key-1") is True


# ------------------------------------------------------------------
# record_failure
# ------------------------------------------------------------------


class TestRecordFailure:
    def test_first_failure_uses_base_cooldown(self) -> None:
        cd = ConnectionCooldown(base_cooldown=10)
        cd.record_failure("k")
        assert cd.get_backoff("k") == 10.0

    def test_exponential_doubling(self) -> None:
        cd = ConnectionCooldown(base_cooldown=5)
        cd.record_failure("k")
        assert cd.get_backoff("k") == 5.0
        cd.record_failure("k")
        assert cd.get_backoff("k") == 10.0
        cd.record_failure("k")
        assert cd.get_backoff("k") == 20.0

    def test_capped_at_max_backoff(self) -> None:
        cd = ConnectionCooldown(base_cooldown=100, max_backoff=300)
        cd.record_failure("k")
        cd.record_failure("k")
        cd.record_failure("k")  # would be 400, capped at 300
        assert cd.get_backoff("k") == 300.0

    def test_retry_after_overrides_computed(self) -> None:
        cd = ConnectionCooldown(base_cooldown=5)
        cd.record_failure("k", retry_after=999.0)
        assert cd.get_backoff("k") == 999.0


# ------------------------------------------------------------------
# on_success
# ------------------------------------------------------------------


class TestOnSuccess:
    def test_resets_backoff(self) -> None:
        cd = ConnectionCooldown(base_cooldown=10)
        cd.record_failure("k")
        cd.record_failure("k")
        assert cd.get_backoff("k") == 20.0
        cd.on_success("k")
        assert cd.get_backoff("k") == 0.0

    def test_success_on_unknown_key_no_error(self) -> None:
        cd = ConnectionCooldown()
        cd.on_success("nonexistent")  # should not raise


# ------------------------------------------------------------------
# reset
# ------------------------------------------------------------------


class TestReset:
    def test_reset_single_key(self) -> None:
        cd = ConnectionCooldown(base_cooldown=10)
        cd.record_failure("a")
        cd.record_failure("b")
        cd.reset("a")
        assert cd.is_available("a") is True
        assert cd.is_available("b") is False

    def test_reset_all(self) -> None:
        cd = ConnectionCooldown(base_cooldown=10)
        cd.record_failure("a")
        cd.record_failure("b")
        cd.reset_all()
        assert cd.is_available("a") is True
        assert cd.is_available("b") is True


# ------------------------------------------------------------------
# Thread safety
# ------------------------------------------------------------------


class TestThreadSafety:
    def test_concurrent_record_failure(self) -> None:
        cd = ConnectionCooldown(base_cooldown=1)
        errors: list[Exception] = []

        def worker(n: int) -> None:
            try:
                for _ in range(100):
                    cd.record_failure("shared-key")
                    cd.is_available("shared-key")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert errors == []
        # Just verify it didn't crash — exact count depends on timing
        assert cd.get_backoff("shared-key") > 0

    def test_concurrent_mixed_operations(self) -> None:
        cd = ConnectionCooldown(base_cooldown=0.01)
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for _ in range(50):
                    cd.record_failure("k")
                    cd.is_available("k")
                    cd.on_success("k")
                    cd.get_backoff("k")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert errors == []


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------


class TestSingleton:
    def test_same_instance(self) -> None:
        a = get_connection_cooldown()
        b = get_connection_cooldown()
        assert a is b

    def test_reset_creates_fresh_instance(self) -> None:
        a = get_connection_cooldown()
        a.record_failure("x")
        reset_cooldown_singleton()
        b = get_connection_cooldown()
        assert a is not b
        assert b.is_available("x") is True

"""
Tests for rate_limiter — targets 36% → 80%+ coverage.

Covers:
- RateLimitConfig.refill_rate
- TokenBucket: _refill, _refill_with_time, consume, wait_time, remaining, reset
- BucketEntry dataclass
- InMemoryRateStorage: get_bucket, cleanup, get_stats, clear
- RateLimiter: check_limit, get_remaining, get_reset_time, cleanup, get_stats, register_preset
- RateLimitExceeded: construction variants
- get_rate_limiter singleton
- init_rate_limiter
"""

import asyncio
import time
import pytest

from src.auth.rate_limiter import (
    RateLimitConfig,
    RateLimitPreset,
    TokenBucket,
    BucketEntry,
    InMemoryRateStorage,
    RateLimiter,
    RateLimitExceeded,
    DEFAULT_RATE_LIMITS,
    get_rate_limiter,
    init_rate_limiter,
)


# ---------------------------------------------------------------------------
# Helper to run coroutines in tests
# ---------------------------------------------------------------------------

def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# RateLimitConfig
# ---------------------------------------------------------------------------

class TestRateLimitConfig:
    def test_refill_rate(self):
        config = RateLimitConfig(limit=100, window=60)
        assert abs(config.refill_rate - 100 / 60) < 1e-9

    def test_default_limits_populated(self):
        assert RateLimitPreset.AUTH_LOGIN in DEFAULT_RATE_LIMITS
        assert DEFAULT_RATE_LIMITS[RateLimitPreset.AUTH_LOGIN].limit == 5


# ---------------------------------------------------------------------------
# TokenBucket
# ---------------------------------------------------------------------------

class TestTokenBucket:
    def test_starts_full(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.tokens == 10

    def test_consume_reduces_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        allowed = run(bucket.consume(3))
        assert allowed is True
        assert bucket.tokens == pytest.approx(7, abs=0.01)

    def test_consume_returns_false_insufficient_tokens(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        allowed = run(bucket.consume(10))
        assert allowed is False

    def test_consume_default_one_token(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        allowed = run(bucket.consume())
        assert allowed is True

    def test_remaining_is_floor(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        run(bucket.consume(2.7))
        assert bucket.remaining == 2  # floor of 2.3

    def test_wait_time_zero_when_enough_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        wait = run(bucket.wait_time(5))
        assert wait == 0.0

    def test_wait_time_positive_when_insufficient(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        run(bucket.consume(5))  # empty
        wait = run(bucket.wait_time(1))
        # Need 1 token at rate 1/s → ~1 second
        assert wait > 0

    def test_reset_refills_bucket(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        run(bucket.consume(8))
        bucket.reset()
        assert bucket.tokens == 10

    def test_refill_with_time(self):
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        run(bucket.consume(10))  # empty
        # Simulate 3 seconds passing
        bucket._refill_with_time(bucket.last_update + 3.0)
        assert bucket.tokens == pytest.approx(6.0, abs=0.01)

    def test_refill_does_not_exceed_capacity(self):
        bucket = TokenBucket(capacity=5, refill_rate=10.0)
        bucket._refill_with_time(bucket.last_update + 100.0)
        assert bucket.tokens == 5.0

    def test_consume_zero_tokens(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        assert run(bucket.consume(0)) is True


# ---------------------------------------------------------------------------
# BucketEntry
# ---------------------------------------------------------------------------

class TestBucketEntry:
    def test_default_last_access_is_recent(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        entry = BucketEntry(bucket=bucket, key="test_key")
        assert entry.last_access <= time.time()
        assert entry.key == "test_key"


# ---------------------------------------------------------------------------
# InMemoryRateStorage
# ---------------------------------------------------------------------------

class TestInMemoryRateStorage:
    def test_get_bucket_creates_new(self):
        storage = InMemoryRateStorage()
        config = RateLimitConfig(limit=10, window=60)
        bucket = run(storage.get_bucket("key1", config))
        assert bucket is not None
        assert bucket.capacity == 10

    def test_get_bucket_returns_existing(self):
        storage = InMemoryRateStorage()
        config = RateLimitConfig(limit=10, window=60)
        b1 = run(storage.get_bucket("key1", config))
        b2 = run(storage.get_bucket("key1", config))
        assert b1 is b2

    def test_get_bucket_updates_last_access(self):
        storage = InMemoryRateStorage()
        config = RateLimitConfig(limit=10, window=60)
        run(storage.get_bucket("key1", config))
        before = time.time()
        run(storage.get_bucket("key1", config))
        entry = storage._buckets["key1"]
        assert entry.last_access >= before

    def test_cleanup_removes_stale_entries(self):
        storage = InMemoryRateStorage(ttl_seconds=3600)
        config = RateLimitConfig(limit=10, window=60)
        run(storage.get_bucket("stale_key", config))
        # Force the entry to be old
        storage._buckets["stale_key"].last_access = time.time() - 7200
        removed = run(storage.cleanup())
        assert removed == 1
        assert "stale_key" not in storage._buckets

    def test_cleanup_with_max_age_override(self):
        storage = InMemoryRateStorage(ttl_seconds=3600)
        config = RateLimitConfig(limit=10, window=60)
        run(storage.get_bucket("old_key", config))
        storage._buckets["old_key"].last_access = time.time() - 100
        # max_age=50 → entry age 100 > 50 → removed
        removed = run(storage.cleanup(max_age=50))
        assert removed == 1

    def test_cleanup_keeps_fresh_entries(self):
        storage = InMemoryRateStorage(ttl_seconds=3600)
        config = RateLimitConfig(limit=10, window=60)
        run(storage.get_bucket("fresh_key", config))
        removed = run(storage.cleanup())
        assert removed == 0

    def test_get_stats_empty(self):
        storage = InMemoryRateStorage()
        stats = run(storage.get_stats())
        assert stats["active_buckets"] == 0
        assert stats["oldest_entry_age"] == 0

    def test_get_stats_with_entries(self):
        storage = InMemoryRateStorage()
        config = RateLimitConfig(limit=10, window=60)
        run(storage.get_bucket("k1", config))
        run(storage.get_bucket("k2", config))
        stats = run(storage.get_stats())
        assert stats["active_buckets"] == 2
        assert stats["total_capacity"] == 20

    def test_clear_removes_all(self):
        storage = InMemoryRateStorage()
        config = RateLimitConfig(limit=10, window=60)
        run(storage.get_bucket("k1", config))
        run(storage.get_bucket("k2", config))
        run(storage.clear())
        stats = run(storage.get_stats())
        assert stats["active_buckets"] == 0


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def test_check_limit_allowed(self):
        limiter = RateLimiter()
        allowed, headers = run(limiter.check_limit("127.0.0.1:/test", RateLimitPreset.API_DEFAULT))
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

    def test_check_limit_denied_adds_retry_after(self):
        # Use a very restrictive preset
        storage = InMemoryRateStorage()
        limiter = RateLimiter(storage=storage)
        config = RateLimitConfig(limit=1, window=60)
        limiter._presets["tiny"] = config
        # First request succeeds
        run(limiter.check_limit("ip:/test", "tiny"))
        # Second request denied
        allowed, headers = run(limiter.check_limit("ip:/test", "tiny"))
        assert allowed is False
        assert "Retry-After" in headers

    def test_check_limit_unknown_preset_uses_default(self):
        limiter = RateLimiter()
        # Passing a string that's not a RateLimitPreset key → falls back to API_DEFAULT
        allowed, headers = run(limiter.check_limit("ip:/test", "nonexistent_preset"))
        assert allowed is True

    def test_get_remaining(self):
        limiter = RateLimiter()
        remaining = run(limiter.get_remaining("ip:/test", RateLimitPreset.API_DEFAULT))
        assert remaining == DEFAULT_RATE_LIMITS[RateLimitPreset.API_DEFAULT].limit

    def test_get_remaining_decreases_after_consume(self):
        limiter = RateLimiter()
        preset = RateLimitPreset.AUTH_LOGIN
        run(limiter.check_limit("ip:/login", preset))  # consume 1
        remaining = run(limiter.get_remaining("ip:/login", preset))
        expected = DEFAULT_RATE_LIMITS[preset].limit - 1
        assert remaining == expected

    def test_get_reset_time_full_bucket(self):
        limiter = RateLimiter()
        reset = run(limiter.get_reset_time("ip:/new", RateLimitPreset.API_DEFAULT))
        # Full bucket → reset time ≈ now
        assert abs(reset - time.time()) < 2

    def test_get_reset_time_after_consumption(self):
        limiter = RateLimiter()
        preset = RateLimitPreset.AUTH_LOGIN  # limit=5, window=60
        # Consume all tokens
        for _ in range(5):
            run(limiter.check_limit("ip:/login2", preset))
        reset = run(limiter.get_reset_time("ip:/login2", preset))
        # Should be in the future
        assert reset > time.time()

    def test_cleanup_delegates_to_storage(self):
        storage = InMemoryRateStorage()
        limiter = RateLimiter(storage=storage)
        config = RateLimitConfig(limit=10, window=60)
        run(storage.get_bucket("old", config))
        storage._buckets["old"].last_access = time.time() - 7200
        removed = run(limiter.cleanup())
        assert removed == 1

    def test_get_stats_includes_presets(self):
        limiter = RateLimiter()
        stats = run(limiter.get_stats())
        assert "presets" in stats
        assert RateLimitPreset.AUTH_LOGIN.value in stats["presets"]

    def test_register_custom_preset(self):
        limiter = RateLimiter()
        limiter.register_preset("custom", limit=50, window=120)
        assert "custom" in limiter._presets
        assert limiter._presets["custom"].limit == 50
        assert limiter._presets["custom"].window == 120


# ---------------------------------------------------------------------------
# RateLimitExceeded
# ---------------------------------------------------------------------------

class TestRateLimitExceeded:
    def test_default_message(self):
        exc = RateLimitExceeded()
        assert "Rate limit exceeded" in exc.message
        assert exc.retry_after == 60  # default

    def test_custom_message_and_headers(self):
        headers = {"Retry-After": "30"}
        exc = RateLimitExceeded(message="Too many requests", headers=headers)
        assert exc.message == "Too many requests"
        assert exc.retry_after == 30
        assert exc.headers == headers

    def test_is_exception(self):
        exc = RateLimitExceeded()
        assert isinstance(exc, Exception)

    def test_str_representation(self):
        exc = RateLimitExceeded(message="Limited")
        assert str(exc) == "Limited"

    def test_empty_headers(self):
        exc = RateLimitExceeded(headers={})
        assert exc.retry_after == 60  # default fallback

    def test_retry_after_from_headers(self):
        exc = RateLimitExceeded(headers={"Retry-After": "120"})
        assert exc.retry_after == 120


# ---------------------------------------------------------------------------
# get_rate_limiter singleton & init_rate_limiter
# ---------------------------------------------------------------------------

class TestRateLimiterSingleton:
    def test_get_rate_limiter_singleton(self):
        import src.auth.rate_limiter as mod
        mod._rate_limiter = None
        l1 = get_rate_limiter()
        l2 = get_rate_limiter()
        assert l1 is l2
        mod._rate_limiter = None

    def test_init_rate_limiter_custom_storage(self):
        import src.auth.rate_limiter as mod
        storage = InMemoryRateStorage(ttl_seconds=100)
        limiter = run(init_rate_limiter(storage=storage))
        assert limiter is not None
        assert mod._rate_limiter is limiter
        mod._rate_limiter = None

    def test_init_rate_limiter_default_storage(self):
        import src.auth.rate_limiter as mod
        limiter = run(init_rate_limiter())
        assert limiter is not None
        mod._rate_limiter = None


# ---------------------------------------------------------------------------
# Concurrency — multiple consume calls
# ---------------------------------------------------------------------------

class TestRateLimiterConcurrency:
    def test_concurrent_consumes(self):
        """Multiple concurrent consume calls should not exceed capacity."""
        bucket = TokenBucket(capacity=5, refill_rate=0)  # no refill
        async def consume_all():
            tasks = [bucket.consume() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            return results
        results = asyncio.run(consume_all())
        allowed = sum(1 for r in results if r)
        denied = sum(1 for r in results if not r)
        assert allowed == 5
        assert denied == 5

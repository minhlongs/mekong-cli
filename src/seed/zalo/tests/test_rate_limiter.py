"""Unit tests for Zalo OA Rate Limiter."""

# Test helpers conventionally skip full type annotations.
# mypy: disable-error-code="no-untyped-def,call-arg,union-attr,misc"

from __future__ import annotations

import time

import pytest

from src.seed.zalo.rate_limiter import (
    InMemoryKV,
    ZaloRateLimiter,
    SlidingWindowRateLimiter,
    create_rate_limiter,
)


@pytest.fixture
def in_memory_kv() -> InMemoryKV:
    """Create in-memory KV store."""
    return InMemoryKV()


@pytest.fixture
def rate_limiter(in_memory_kv: InMemoryKV) -> ZaloRateLimiter:
    """Create rate limiter with in-memory KV."""
    return ZaloRateLimiter(in_memory_kv, default_limit=10, default_window_seconds=60)


@pytest.fixture
def sliding_limiter(in_memory_kv: InMemoryKV) -> SlidingWindowRateLimiter:
    """Create sliding window rate limiter."""
    return SlidingWindowRateLimiter(in_memory_kv, default_limit=10, default_window_seconds=60)


class TestInMemoryKV:
    """Tests for InMemoryKV."""

    @pytest.mark.asyncio
    async def test_put_and_get(self, in_memory_kv: InMemoryKV):
        """Test basic put and get."""
        await in_memory_kv.put("key1", "value1")
        value = await in_memory_kv.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, in_memory_kv: InMemoryKV):
        """Test getting non-existent key returns None."""
        value = await in_memory_kv.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, in_memory_kv: InMemoryKV):
        """Test deleting key."""
        await in_memory_kv.put("key1", "value1")
        await in_memory_kv.delete("key1")
        value = await in_memory_kv.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_expiration(self, in_memory_kv: InMemoryKV):
        """Test key expiration."""
        await in_memory_kv.put("key1", "value1", expiration_ttl=1)  # 1 second TTL
        value = await in_memory_kv.get("key1")
        assert value == "value1"

        time.sleep(1.1)
        value = await in_memory_kv.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_no_expiration(self, in_memory_kv: InMemoryKV):
        """Test key without expiration persists."""
        await in_memory_kv.put("key1", "value1", expiration_ttl=None)
        time.sleep(0.1)
        value = await in_memory_kv.get("key1")
        assert value == "value1"


class TestZaloRateLimiter:
    """Tests for ZaloRateLimiter (fixed window)."""

    @pytest.mark.asyncio
    async def test_check_limit_allows_within_limit(self, rate_limiter: ZaloRateLimiter):
        """Test requests within limit are allowed."""
        allowed, info = await rate_limiter.check_limit("oa_123")

        assert allowed is True
        assert info.limit == 10
        assert info.remaining == 9
        assert info.exceeded is False

    @pytest.mark.asyncio
    async def test_check_limit_blocks_over_limit(self, rate_limiter: ZaloRateLimiter):
        """Test requests over limit are blocked."""
        # Use up all 10 requests
        for i in range(10):
            allowed, _ = await rate_limiter.check_limit("oa_123")
            assert allowed is True

        # 11th request should be blocked
        allowed, info = await rate_limiter.check_limit("oa_123")

        assert allowed is False
        assert info.remaining == 0
        assert info.exceeded is True

    @pytest.mark.asyncio
    async def test_separate_oa_ids(self, rate_limiter: ZaloRateLimiter):
        """Test rate limits are separate per OA ID."""
        for i in range(10):
            await rate_limiter.check_limit("oa_1")

        # oa_2 should still have full limit
        allowed, info = await rate_limiter.check_limit("oa_2")
        assert allowed is True
        assert info.remaining == 9

    @pytest.mark.asyncio
    async def test_custom_limit(self, in_memory_kv: InMemoryKV):
        """Test custom limit per check."""
        limiter = ZaloRateLimiter(in_memory_kv, default_limit=100)
        allowed, info = await limiter.check_limit("oa_123", limit=5)

        assert allowed is True
        assert info.limit == 5

    @pytest.mark.asyncio
    async def test_custom_window(self, in_memory_kv: InMemoryKV):
        """Test custom window per check."""
        limiter = ZaloRateLimiter(in_memory_kv, default_limit=100, default_window_seconds=60)
        allowed, info = await limiter.check_limit("oa_123", window_seconds=30)

        assert allowed is True
        # Reset time should be within 30 seconds
        assert info.reset_at - int(time.time()) <= 30

    @pytest.mark.asyncio
    async def test_get_status(self, rate_limiter: ZaloRateLimiter):
        """Test getting current status without incrementing."""
        # Make some requests
        for i in range(3):
            await rate_limiter.check_limit("oa_123")

        status = await rate_limiter.get_status("oa_123")

        assert status.limit == 10
        assert status.remaining == 7
        assert status.exceeded is False

    @pytest.mark.asyncio
    async def test_reset_limit(self, rate_limiter: ZaloRateLimiter):
        """Test resetting rate limit."""
        # Use some requests
        for i in range(5):
            await rate_limiter.check_limit("oa_123")

        # Reset
        await rate_limiter.reset_limit("oa_123")

        # Should have full limit again
        status = await rate_limiter.get_status("oa_123")
        assert status.remaining == 10

    @pytest.mark.asyncio
    async def test_set_and_get_custom_limit(self, rate_limiter: ZaloRateLimiter):
        """Test setting and getting custom limit config."""
        await rate_limiter.set_custom_limit("oa_123", 50, 120)
        config = await rate_limiter.get_custom_limit("oa_123")

        assert config == (50, 120)

    @pytest.mark.asyncio
    async def test_get_custom_limit_not_set(self, rate_limiter: ZaloRateLimiter):
        """Test getting custom limit when not set."""
        config = await rate_limiter.get_custom_limit("oa_999")
        assert config is None


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""

    @pytest.mark.asyncio
    async def test_check_limit_allows_within_limit(self, sliding_limiter: SlidingWindowRateLimiter):
        """Test sliding window allows requests within limit."""
        for i in range(10):
            allowed, info = await sliding_limiter.check_limit("oa_123")
            assert allowed is True
            assert info.remaining == 9 - i

    @pytest.mark.asyncio
    async def test_check_limit_blocks_over_limit(self, sliding_limiter: SlidingWindowRateLimiter):
        """Test sliding window blocks over limit."""
        for i in range(10):
            await sliding_limiter.check_limit("oa_123")

        allowed, info = await sliding_limiter.check_limit("oa_123")

        assert allowed is False
        assert info.exceeded is True

    @pytest.mark.asyncio
    async def test_sliding_window_accuracy(self, in_memory_kv: InMemoryKV):
        """Test sliding window is more accurate than fixed window."""
        limiter = SlidingWindowRateLimiter(in_memory_kv, default_limit=5, default_window_seconds=10, sub_windows=5)

        # Make 5 requests quickly
        for i in range(5):
            allowed, _ = await limiter.check_limit("oa_123")
            assert allowed is True

        # Next request blocked
        allowed, _ = await limiter.check_limit("oa_123")
        assert allowed is False

    @pytest.mark.asyncio
    async def test_sub_window_expiration(self, in_memory_kv: InMemoryKV):
        """Test old sub-windows expire."""
        limiter = SlidingWindowRateLimiter(
            in_memory_kv,
            default_limit=5,
            default_window_seconds=2,  # Short window
            sub_windows=2,
        )

        # Make 5 requests
        for i in range(5):
            await limiter.check_limit("oa_123")

        # Wait for window to pass
        time.sleep(2.5)

        # Should be allowed again
        allowed, _ = await limiter.check_limit("oa_123")
        assert allowed is True


class TestCreateRateLimiter:
    """Tests for create_rate_limiter factory."""

    @pytest.mark.asyncio
    async def test_create_fixed_window(self):
        """Test creating fixed window limiter."""
        limiter = create_rate_limiter(default_limit=50, sliding=False)

        assert isinstance(limiter, ZaloRateLimiter)
        assert not isinstance(limiter, SlidingWindowRateLimiter)
        assert limiter.default_limit == 50

    @pytest.mark.asyncio
    async def test_create_sliding_window(self):
        """Test creating sliding window limiter."""
        limiter = create_rate_limiter(default_limit=50, sliding=True)

        assert isinstance(limiter, SlidingWindowRateLimiter)
        assert limiter.default_limit == 50

    @pytest.mark.asyncio
    async def test_create_with_custom_kv(self, in_memory_kv: InMemoryKV):
        """Test creating limiter with custom KV."""
        limiter = create_rate_limiter(kv=in_memory_kv)

        assert limiter.kv is in_memory_kv
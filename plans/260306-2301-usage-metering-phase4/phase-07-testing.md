---
title: "Phase 7 — Test Suite"
description: "Comprehensive tests for usage metering components"
status: pending
priority: P2
effort: 2h
parent_plan: 260306-2301-usage-metering-phase4
---

# Phase 7 — Test Suite

## Context Links

- Parent Plan: `plans/260306-2301-usage-metering-phase4/plan.md`
- Test Pattern: `tests/test_license_validation.py`

## Test Files to Create

| File | Coverage |
|------|----------|
| `test_usage_queue.py` | UsageQueue enqueue/dequeue/flush |
| `test_usage_meter.py` | UsageMeter record_usage/get_summary |
| `test_timestamp_validation.py` | Reject events > 300s |
| `test_idempotency.py` | Prevent double-counting |
| `test_tier_limits.py` | Enforce daily limits |
| `test_executor_integration.py` | End-to-end |

## Implementation

### Test 1: test_usage_queue.py

```python
"""Tests for UsageQueue async buffer."""

import asyncio
import pytest
from src.lib.usage_queue import UsageQueue


class TestUsageQueue:
    """Test UsageQueue operations."""

    @pytest.mark.asyncio
    async def test_enqueue(self):
        """Test enqueue adds event to queue."""
        queue = UsageQueue(max_size=10)
        await queue.start()

        await queue.enqueue(
            key_id="test123",
            tier="pro",
            command="mekong cook test",
        )

        assert queue._queue.qsize() == 1
        await queue.stop()

    @pytest.mark.asyncio
    async def test_flush_batch(self):
        """Test flush_batch records events."""
        queue = UsageQueue(max_size=10, flush_interval=0.1)
        await queue.start()

        await queue.enqueue(
            key_id="test123",
            tier="pro",
            command="test command",
        )

        # Wait for flush
        await asyncio.sleep(0.2)
        await queue.stop()

        # Verify logged (mock logger to assert)

    @pytest.mark.asyncio
    async def test_sqlite_fallback(self):
        """Test SQLite fallback when PostgreSQL unavailable."""
        # TODO: Mock PostgreSQL to fail
        pass
```

### Test 2: test_timestamp_validation.py

```python
"""Tests for timestamp validation."""

import pytest
from datetime import datetime, timezone, timedelta
from src.lib.usage_meter import UsageMeter


class TestTimestampValidation:
    """Test timestamp validation logic."""

    @pytest.mark.asyncio
    async def test_valid_timestamp(self):
        """Test recent timestamp accepted."""
        meter = UsageMeter()
        now = datetime.now(timezone.utc)

        allowed, error = await meter.record_usage(
            key_id="test123",
            tier="pro",
            event_timestamp=now,
        )

        assert allowed is True

    @pytest.mark.asyncio
    async def test_old_timestamp_rejected(self):
        """Test timestamp > 300s rejected."""
        meter = UsageMeter()
        old = datetime.now(timezone.utc) - timedelta(seconds=400)

        allowed, error = await meter.record_usage(
            key_id="test123",
            tier="pro",
            event_timestamp=old,
        )

        assert allowed is False
        assert "timestamp too old" in error.lower()

    @pytest.mark.asyncio
    async def test_future_timestamp_rejected(self):
        """Test future timestamp rejected."""
        meter = UsageMeter()
        future = datetime.now(timezone.utc) + timedelta(seconds=400)

        allowed, error = await meter.record_usage(
            key_id="test123",
            tier="pro",
            event_timestamp=future,
        )

        assert allowed is False
```

### Test 3: test_idempotency.py

```python
"""Tests for idempotency key system."""

import pytest
from src.lib.usage_meter import UsageMeter


class TestIdempotency:
    """Test idempotency prevents double-counting."""

    @pytest.mark.asyncio
    async def test_duplicate_prevented(self):
        """Test same idempotency key not counted twice."""
        meter = UsageMeter()
        idempotency_key = "test123:abc123:2026-03-06"

        # First record
        allowed1, _ = await meter.record_usage(
            key_id="test123",
            tier="pro",
            commands_count=1,
            idempotency_key=idempotency_key,
        )

        # Second record with same key
        allowed2, error = await meter.record_usage(
            key_id="test123",
            tier="pro",
            commands_count=1,
            idempotency_key=idempotency_key,
        )

        assert allowed1 is True
        assert allowed2 is True  # Idempotent, not error
        assert "already recorded" in error.lower()

    @pytest.mark.asyncio
    async def test_different_keys_counted(self):
        """Test different idempotency keys both counted."""
        # TODO: Verify usage count increments
        pass
```

### Test 4: test_tier_limits.py

```python
"""Tests for tier limit enforcement."""

import pytest
from src.lib.usage_meter import UsageMeter
from src.db.repository import LicenseRepository


class TestTierLimits:
    """Test tier limits enforcement."""

    @pytest.mark.asyncio
    async def test_free_limit_enforced(self):
        """Test free tier (10/day) enforced."""
        # TODO: Mock repository to return 10 commands already
        pass

    @pytest.mark.asyncio
    async def test_pro_limit_higher(self):
        """Test pro tier (1000/day) allows more."""
        pass

    @pytest.mark.asyncio
    async def test_enterprise_unlimited(self):
        """Test enterprise tier unlimited."""
        pass
```

### Test 5: test_executor_integration.py

```python
"""Integration tests for executor usage recording."""

import pytest
from src.core.executor import RecipeExecutor
from src.core.parser import Recipe, RecipeStep


class TestExecutorIntegration:
    """Test executor records usage on success."""

    @pytest.mark.asyncio
    async def test_usage_recorded_on_success(self):
        """Test successful command triggers usage recording."""
        # TODO: Mock UsageQueue to verify enqueue called
        pass

    @pytest.mark.asyncio
    async def test_usage_not_recorded_on_failure(self):
        """Test failed command doesn't record usage."""
        pass

    @pytest.mark.asyncio
    async def test_no_license_key_graceful(self):
        """Test missing RAAS_LICENSE_KEY doesn't fail command."""
        pass
```

## Success Criteria

- [ ] All 6 test files created
- [ ] Tests cover timestamp validation
- [ ] Tests cover idempotency
- [ ] Tests cover tier limits
- [ ] Integration tests pass
- [ ] `python3 -m pytest tests/test_usage_*.py` passes 100%

## Todo List

- [ ] Create `tests/test_usage_queue.py`
- [ ] Create `tests/test_usage_meter.py`
- [ ] Create `tests/test_timestamp_validation.py`
- [ ] Create `tests/test_idempotency.py`
- [ ] Create `tests/test_tier_limits.py`
- [ ] Create `tests/test_executor_integration.py`
- [ ] Run tests, fix failures

## Mocking Strategy

- Mock `LicenseRepository` for unit tests
- Mock `UsageQueue` for executor tests
- Use real PostgreSQL for integration tests (or mock to avoid dependency)

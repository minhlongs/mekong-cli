---
title: "Phase 4 — Structured Logging"
description: "Add structlog to all usage metering events"
status: completed
priority: P2
effort: 0.5h
parent_plan: 260306-2301-usage-metering-phase4
---

# Phase 4 — Structured Logging

## Context Links

- Parent Plan: `plans/260306-2301-usage-metering-phase4/plan.md`
- Logging Config: `src/config/logging_config.py`

## Overview

Add structlog to `usage_meter.py` and `usage_queue.py` for full event traceability.

## Log Events

| Event | Level | Context |
|-------|-------|---------|
| `usage.captured` | INFO | key_id, tier, command |
| `usage.recorded` | INFO | key_id, tier, daily_total |
| `usage.rejected` | WARNING | key_id, reason, details |
| `usage.limit_reached` | WARNING | key_id, limit, current |
| `usage.queue.enqueued` | DEBUG | key_id, queue_size |
| `usage.queue.flushed` | INFO | batch_size |
| `usage.queue.started` | INFO | worker_id |
| `usage.queue.stopped` | INFO | final_flush_size |

## Implementation

### Step 1: Add Logger to usage_meter.py

```python
# src/lib/usage_meter.py
from src.config.logging_config import get_logger

class UsageMeter:
    """Track and enforce usage limits with PostgreSQL backend."""

    def __init__(self, repository: Optional[LicenseRepository] = None) -> None:
        self._repo = repository or get_repository()
        self._logger = get_logger(__name__)
```

### Step 2: Add Logging to record_usage

```python
async def record_usage(
    self,
    key_id: str,
    tier: str,
    commands_count: int = 1,
    event_timestamp: Optional[datetime] = None,
) -> tuple[bool, str]:
    """Record command usage with structured logging."""
    # Check limits
    limits = get_tier_limits(tier)
    max_commands = limits["commands_per_day"]

    usage = await self._repo.get_usage(key_id)
    current_count = usage["commands_count"] if usage else 0

    if max_commands >= 0 and current_count >= max_commands:
        self._logger.warning(
            "usage.limit_reached",
            key_id=key_id,
            tier=tier,
            current=current_count,
            limit=max_commands,
        )
        return False, f"Daily limit reached: {current_count}/{max_commands}"

    # Record
    result = await self._repo.record_usage(key_id, commands_count=commands_count)

    new_total = current_count + commands_count
    self._logger.info(
        "usage.recorded",
        key_id=key_id,
        tier=tier,
        commands_count=commands_count,
        daily_total=new_total,
        limit=max_commands if max_commands >= 0 else "unlimited",
    )

    return True, ""
```

### Step 3: Add Logger to usage_queue.py

```python
# src/lib/usage_queue.py
from src.config.logging_config import get_logger

class UsageQueue:
    def __init__(self, ...) -> None:
        self._queue = asyncio.Queue(maxsize=max_size)
        self._logger = get_logger(__name__)
        # ... rest
```

## Success Criteria

- [ ] All 8 log events implemented
- [ ] No `print()` statements remain
- [ ] Log context includes key_id, tier, timestamps
- [ ] JSON output in production, console in dev

## Todo List

- [ ] Add logger to UsageMeter
- [ ] Add logging to record_usage()
- [ ] Add logger to UsageQueue
- [ ] Add logging to all queue operations
- [ ] Remove print() statements

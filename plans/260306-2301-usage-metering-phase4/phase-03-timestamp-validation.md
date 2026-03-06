---
title: "Phase 3 — Timestamp Validation"
description: "Validate event timestamps, reject events > 300s old"
status: completed
priority: P2
effort: 0.5h
parent_plan: 260306-2301-usage-metering-phase4
---

# Phase 3 — Timestamp Validation

## Context Links

- Parent Plan: `plans/260306-2301-usage-metering-phase4/plan.md`
- Target: `src/lib/usage_meter.py`

## Overview

Add timestamp validation to `UsageMeter.record_usage()` to reject stale events (> 5 min old).

## Implementation

### Step 1: Update record_usage Signature

```python
# src/lib/usage_meter.py
from datetime import datetime, timezone

async def record_usage(
    self,
    key_id: str,
    tier: str,
    commands_count: int = 1,
    event_timestamp: Optional[datetime] = None,
) -> tuple[bool, str]:
    """
    Record a command usage.

    Args:
        key_id: License key ID
        tier: License tier
        commands_count: Number of commands to record
        event_timestamp: When the event occurred (defaults to now)

    Returns:
        Tuple of (allowed, error_message)
    """
    # Validate timestamp if provided
    if event_timestamp is not None:
        now = datetime.now(timezone.utc)
        # Ensure event_timestamp is timezone-aware
        if event_timestamp.tzinfo is None:
            event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)

        age = (now - event_timestamp).total_seconds()
        max_age = 300  # 5 minutes

        if abs(age) > max_age:
            self._logger.warning(
                "usage.rejected",
                key_id=key_id,
                reason="timestamp_too_old",
                age_seconds=age,
                max_age=max_age,
            )
            return False, f"Event timestamp too old: {age:.0f}s (max: {max_age}s)"
```

### Step 2: Update Caller

In `usage_queue.py`, pass timestamp from event:

```python
# In _flush_batch():
timestamp = datetime.fromisoformat(event["timestamp"])
allowed, error = await self._meter.record_usage(
    key_id=event["key_id"],
    tier=event["tier"],
    commands_count=1,
    event_timestamp=timestamp,
)
```

## Success Criteria

- [ ] Events > 300s old rejected with clear error
- [ ] Events < 300s accepted
- [ ] Timestamps handled timezone-aware (UTC)
- [ ] Rejections logged with structlog

## Todo List

- [ ] Add `event_timestamp` param to `record_usage()`
- [ ] Implement validation logic
- [ ] Update caller in `usage_queue.py`
- [ ] Add test case for old timestamps

## Edge Cases

- **No timestamp provided**: Use current time (backward compatible)
- **Timezone-naive timestamp**: Assume UTC
- **Future timestamp**: Also rejected (abs(age))

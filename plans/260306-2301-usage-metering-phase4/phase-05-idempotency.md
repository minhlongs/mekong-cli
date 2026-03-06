---
title: "Phase 5 — Idempotency Key System"
description: "Prevent double-counting with idempotency keys (24h TTL)"
status: pending
priority: P2
effort: 1.5h
parent_plan: 260306-2301-usage-metering-phase4
---

# Phase 5 — Idempotency Key System

## Context Links

- Parent Plan: `plans/260306-2301-usage-metering-phase4/plan.md`
- Repository: `src/db/repository.py`
- Migration: `docs/migrations/add_idempotency_keys_table.sql`

## Overview

Add idempotency key generation and validation to prevent double-counting the same command.

## Idempotency Key Format

```
{key_id}:{command_hash}:{date}
# Example: abc1234:sha256("mekong cook"):2026-03-06
```

**TTL**: 24 hours (auto-cleanup via daily cron or lazy deletion)

## Database Schema

```sql
-- docs/migrations/add_idempotency_keys_table.sql
CREATE TABLE IF NOT EXISTS usage_idempotency_keys (
    id SERIAL PRIMARY KEY,
    key_id TEXT NOT NULL,
    command_hash TEXT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(key_id, command_hash, date)
);

-- Index for cleanup
CREATE INDEX idx_idempotency_keys_date
ON usage_idempotency_keys(date);

-- Comment
COMMENT ON TABLE usage_idempotency_keys IS
'Prevents double-counting of CLI commands; TTL 24h';
```

## Implementation

### Step 1: Add Repository Methods

```python
# src/db/repository.py
async def check_idempotency_key(
    self,
    key_id: str,
    command_hash: str,
    date: date,
) -> bool:
    """Check if idempotency key exists."""
    query = """
        SELECT 1 FROM usage_idempotency_keys
        WHERE key_id = $1 AND command_hash = $2 AND date = $3
    """
    result = await self._db.fetch_one(query, (key_id, command_hash, date))
    return result is not None

async def store_idempotency_key(
    self,
    key_id: str,
    command_hash: str,
    date: date,
) -> bool:
    """Store idempotency key."""
    query = """
        INSERT INTO usage_idempotency_keys (key_id, command_hash, date)
        VALUES ($1, $2, $3)
        ON CONFLICT (key_id, command_hash, date) DO NOTHING
    """
    await self._db.execute(query, (key_id, command_hash, date))
    return True

async def cleanup_old_idempotency_keys(self, days_old: int = 1) -> int:
    """Delete idempotency keys older than N days."""
    query = f"""
        DELETE FROM usage_idempotency_keys
        WHERE date < CURRENT_DATE - INTERVAL '{days_old} days'
    """
    # Returns number of rows affected
    result = await self._db.execute(query)
    # Parse "DELETE N" to get count
    return int(result.split()[-1]) if result else 0
```

### Step 2: Update UsageMeter.record_usage

```python
# src/lib/usage_meter.py
import hashlib

async def record_usage(
    self,
    key_id: str,
    tier: str,
    commands_count: int = 1,
    event_timestamp: Optional[datetime] = None,
    idempotency_key: Optional[str] = None,
) -> tuple[bool, str]:
    """Record usage with idempotency check."""

    # Check idempotency if key provided
    if idempotency_key:
        parts = idempotency_key.split(":")
        if len(parts) == 3:
            stored_key_id, command_hash, date_str = parts
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            is_duplicate = await self._repo.check_idempotency_key(
                key_id=stored_key_id,
                command_hash=command_hash,
                date=date,
            )

            if is_duplicate:
                self._logger.debug(
                    "usage.duplicate",
                    key_id=key_id,
                    idempotency_key=idempotency_key,
                )
                return True, "Already recorded (idempotent)"

    # ... existing timestamp validation ...
    # ... existing limit check ...

    # Record usage
    await self._repo.record_usage(key_id, commands_count=commands_count)

    # Store idempotency key after successful record
    if idempotency_key:
        await self._repo.store_idempotency_key(
            key_id=key_id,
            command_hash=parts[1] if idempotency_key else "",
            date=date,
        )

    return True, ""
```

### Step 3: Update Executor Hook

In `executor.py`, generate idempotency key:

```python
# In _record_usage():
timestamp = datetime.utcnow()
date_str = timestamp.strftime("%Y-%m-%d")
command_hash = hashlib.sha256(command.encode()).hexdigest()[:16]
idempotency_key = f"{key_id}:{command_hash}:{date_str}"

# Pass to queue
await self._usage_queue.enqueue(
    key_id=key_id,
    tier=tier,
    command=command,
    metadata={"idempotency_key": idempotency_key},
)
```

## Success Criteria

- [ ] Idempotency key table created
- [ ] `check_idempotency_key()` method works
- [ ] `store_idempotency_key()` method works
- [ ] Duplicate commands not counted twice
- [ ] Old keys cleaned up (24h TTL)

## Todo List

- [ ] Create SQL migration file
- [ ] Run migration on database
- [ ] Add repository methods
- [ ] Update UsageMeter.record_usage()
- [ ] Update executor to generate keys
- [ ] Test duplicate prevention

## Unresolved Questions

1. **Cleanup strategy**: Lazy (on access) or scheduled (cron job)?
   - Proposed: Lazy cleanup on first access per day

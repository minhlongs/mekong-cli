---
title: "Usage Metering Phase 4 — Implementation Plan"
description: "Integrate usage metering into RecipeExecutor with timestamp validation, structlog logging, idempotency, and async queue"
status: pending
priority: P2
effort: 8h
branch: master
tags: [roiaas, phase4, usage-metering, telemetry]
created: 2026-03-06
---

# Usage Metering Phase 4 — Implementation Plan

> **ROIaaS Phase 4** — Track and enforce usage limits per license key with PostgreSQL backend.

## Context

- **Existing**: `src/lib/usage_meter.py` (UsageMeter class với PostgreSQL)
- **Need**: Hook into `RecipeExecutor` to record usage after each successful command
- **Requirements**:
  1. Capture CLI command invocations with timestamps
  2. Validate timestamps (reject > 5 min old)
  3. Log with structlog
  4. Authenticated API calls (via RAAS_LICENSE_KEY)
  5. Idempotency (prevent double-counting)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  RecipeExecutor.execute_step()                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ _execute_shell_step()                                │  │
│  │   → subprocess.run()                                 │  │
│  │   → if exit_code == 0: _record_usage() ◄──── HOOK    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  UsageQueue (new) — Async buffer with SQLite fallback       │
│   - Queue events in memory                                  │
│   - Flush to PostgreSQL in background                       │
│   - SQLite buffer if DB unavailable                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  UsageMeter.record_usage()                                  │
│   - Validate timestamp (< 300s old)                         │
│   - Check idempotency key                                   │
│   - Verify tier limits                                      │
│   - Record to PostgreSQL                                    │
│   - Log with structlog                                      │
└─────────────────────────────────────────────────────────────┘
```

## Success Criteria

- [ ] Every successful shell command recorded in usage_records
- [ ] Timestamp validation rejects events > 5 min old
- [ ] Idempotency prevents double-counting (same command × 24h)
- [ ] Structured logs: `usage.captured`, `usage.recorded`, `usage.rejected`
- [ ] License key extracted from `RAAS_LICENSE_KEY` env var
- [ ] Tests pass: timestamp validation, idempotency, tier limits
- [ ] Zero console.log — all structlog

---

## Phase 1: Usage Queue — Async Buffer Layer

**Goal**: Create `src/lib/usage_queue.py` for reliable async usage recording.

### Why Queue?

- Shell execution is sync; usage recording is async (PostgreSQL)
- Prevent blocking command execution on DB latency
- SQLite buffer as fallback if DB unavailable

### Tasks

- [ ] Task 1.1: Create `UsageQueue` class with asyncio.Queue
- [ ] Task 1.2: Implement `enqueue()` method for adding events
- [ ] Task 1.3: Implement background worker `_process_queue()`
- [ ] Task 1.4: Add SQLite buffer fallback (file: `.mekong/usage_buffer.db`)
- [ ] Task 1.5: Add `start()` and `stop()` lifecycle methods
- [ ] Task 1.6: Log queue events with structlog

### Files

- **Create**: `src/lib/usage_queue.py`
- **Modify**: None

### Context Links

- `src/lib/usage_meter.py` — UsageMeter class
- `src/db/repository.py` — LicenseRepository for DB operations
- `src/config/logging_config.py` — structlog setup

---

## Phase 2: Executor Integration — Hook into RecipeExecutor

**Goal**: Add `_record_usage()` method to `RecipeExecutor._execute_shell_step()`.

### Implementation

```python
# In _execute_shell_step(), after successful execution:
if process.returncode == 0:
    await self._record_usage(command, metadata)
```

### Tasks

- [ ] Task 2.1: Add `from src.lib.usage_queue import UsageQueue` import
- [ ] Task 2.2: Initialize UsageQueue in `__init__()`
- [ ] Task 2.3: Create `_record_usage()` method in RecipeExecutor
- [ ] Task 2.4: Extract `key_id` from `RAAS_LICENSE_KEY` env var
- [ ] Task 2.5: Generate idempotency key (hash of command + timestamp)
- [ ] Task 2.6: Call `UsageQueue.enqueue()` after successful execution
- [ ] Task 2.7: Handle errors gracefully (log but don't fail command)

### Files

- **Modify**: `src/core/executor.py`
- **Create**: None

### Context Links

- `src/lib/license_generator.py` — parse license key format
- `.env.example` — document RAAS_LICENSE_KEY

---

## Phase 3: Timestamp Validation — Reject Stale Events

**Goal**: Add timestamp validation to `UsageMeter.record_usage()`.

### Validation Rules

- Event timestamp must be within 300s (5 min) of current time
- Reject events with timestamp > 300s old
- Log rejections with reason

### Tasks

- [ ] Task 3.1: Add `event_timestamp` param to `record_usage()`
- [ ] Task 3.2: Validate: `abs(now - event_timestamp) < 300`
- [ ] Task 3.3: Return `(False, "Event timestamp too old")` if invalid
- [ ] Task 3.4: Log rejection with structlog: `usage.rejected`
- [ ] Task 3.5: Update caller to pass current timestamp

### Files

- **Modify**: `src/lib/usage_meter.py`
- **Modify**: `src/lib/usage_queue.py` (pass timestamp)

### Context Links

- `src/config/logging_config.py` — structlog logger

---

## Phase 4: Structured Logging — Full Event Traceability

**Goal**: Add structlog to all usage metering events.

### Log Events

| Event | Level | Context |
|-------|-------|---------|
| `usage.captured` | INFO | key_id, tier, command, timestamp |
| `usage.recorded` | INFO | key_id, commands_count, daily_total |
| `usage.rejected` | WARNING | key_id, reason, timestamp |
| `usage.limit_reached` | WARNING | key_id, limit, current |
| `usage.queue.enqueued` | DEBUG | queue_size |
| `usage.queue.flushed` | INFO | batch_size |

### Tasks

- [ ] Task 4.1: Import `get_logger` in `usage_meter.py`
- [ ] Task 4.2: Import `get_logger` in `usage_queue.py`
- [ ] Task 4.3: Add logger instances
- [ ] Task 4.4: Log all events with structured context
- [ ] Task 4.5: Remove all `print()` statements

### Files

- **Modify**: `src/lib/usage_meter.py`
- **Modify**: `src/lib/usage_queue.py`

### Context Links

- `src/config/logging_config.py` — logger factory

---

## Phase 5: Idempotency — Prevent Double-Counting

**Goal**: Add idempotency key generation and validation.

### Idempotency Key Format

```
{key_id}:{command_hash}:{timestamp_date}
# Example: abc123:sha256("mekong cook"):2026-03-06
```

### Storage

- Table: `usage_idempotency_keys` (key_id, command_hash, date, created_at)
- TTL: 24 hours (auto-cleanup via daily job)

### Tasks

- [ ] Task 5.1: Create DB table `usage_idempotency_keys` (migration SQL)
- [ ] Task 5.2: Add `check_idempotency_key()` to LicenseRepository
- [ ] Task 5.3: Add `store_idempotency_key()` to LicenseRepository
- [ ] Task 5.4: Generate idempotency key in `_record_usage()`
- [ ] Task 5.5: Check before recording usage
- [ ] Task 5.6: Store after successful record

### Files

- **Modify**: `src/db/repository.py` (add methods)
- **Modify**: `src/lib/usage_meter.py` (check idempotency)
- **Create**: `docs/migrations/add_idempotency_keys_table.sql`

### Context Links

- `src/db/database.py` — DB connection

---

## Phase 6: License Key Parsing — Extract key_id

**Goal**: Parse `RAAS_LICENSE_KEY` to extract `key_id` and `tier`.

### Key Format

```
raas-{tier}-{key_id}-{signature}
# Example: raas-pro-abc1234-signature
```

### Tasks

- [ ] Task 6.1: Create `parse_license_key()` helper in `license_generator.py`
- [ ] Task 6.2: Extract tier and key_id from full license key
- [ ] Task 6.3: Validate signature (optional for perf)
- [ ] Task 6.4: Use in executor to extract key_id from env var

### Files

- **Modify**: `src/lib/license_generator.py`
- **Modify**: `src/core/executor.py` (use parser)

### Context Links

- `src/lib/usage_meter.py` — needs key_id and tier

---

## Phase 7: Testing — Comprehensive Test Suite

**Goal**: Write tests for all usage metering components.

### Test Coverage

| Test File | Coverage |
|-----------|----------|
| `test_usage_queue.py` | UsageQueue enqueue/dequeue/flush |
| `test_usage_meter.py` | UsageMeter record_usage/get_summary |
| `test_timestamp_validation.py` | Reject events > 300s old |
| `test_idempotency.py` | Prevent double-counting |
| `test_tier_limits.py` | Enforce daily limits |
| `test_executor_integration.py` | End-to-end usage recording |

### Tasks

- [ ] Task 7.1: Create `tests/test_usage_queue.py`
- [ ] Task 7.2: Create `tests/test_usage_meter.py`
- [ ] Task 7.3: Create `tests/test_timestamp_validation.py`
- [ ] Task 7.4: Create `tests/test_idempotency.py`
- [ ] Task 7.5: Create `tests/test_tier_limits.py`
- [ ] Task 7.6: Create `tests/test_executor_integration.py`
- [ ] Task 7.7: Run full test suite, fix failures

### Files

- **Create**: `tests/test_usage_*.py` (6 files)

### Context Links

- `tests/test_license_validation.py` — test pattern reference

---

## Phase 8: Database Migration — Schema Updates

**Goal**: Create SQL migrations for new tables.

### Tables

1. `usage_idempotency_keys` — Track processed events
2. (Optional) `usage_queue_buffer` — SQLite fallback table

### Tasks

- [ ] Task 8.1: Create `docs/migrations/add_idempotency_keys_table.sql`
- [ ] Task 8.2: Document migration in `docs/usage-metering.md`
- [ ] Task 8.3: Add migration runner script (optional)

### Files

- **Create**: `docs/migrations/add_idempotency_keys_table.sql`
- **Create**: `docs/usage-metering.md` (documentation)

---

## Implementation Order

```
Phase 1 → Phase 6 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 8 → Phase 7
   │          │         │         │         │         │         │        │
   │          │         │         │         │         │         │        └─ Test
   │          │         │         │         │         │         └─ Migrate
   │          │         │         │         │         └─ Idempotency
   │          │         │         │         └─ Logging
   │          │         │         └─ Timestamp
   │          │         └─ Hook
   │          └─ Parse Key
   └─ Queue
```

**Rationale**:
1. Queue first (infrastructure)
2. Key parsing (needed for executor hook)
3. Executor hook (core integration)
4. Timestamp validation (business logic)
5. Logging (observability)
6. Idempotency (data integrity)
7. Migration (schema)
8. Tests (verification)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| DB connection fails | Usage lost | SQLite buffer fallback in UsageQueue |
| Timestamp sync issues | False rejections | Use UTC, allow 30s clock skew |
| Idempotency key collision | Under-counting | Use SHA256 hash + date |
| Performance overhead | Slow CLI | Async queue, non-blocking |
| License key parsing fails | No usage tracked | Graceful fallback, log error |

---

## Dependencies

- `asyncpg` — PostgreSQL async driver (already in `pyproject.toml`)
- `structlog` — Structured logging (already in `pyproject.toml`)
- PostgreSQL database — `DATABASE_URL` env var

---

## Unresolved Questions

1. **Idempotency TTL**: 24h or 7d? (Proposed: 24h for CLI commands)
2. **SQLite buffer location**: `.mekong/usage_buffer.db` or `/tmp/`?
3. **Queue flush interval**: Every command or batch (N commands)?
4. **Signature validation**: Validate on every command or cache?

---

## Related Files

- `src/core/executor.py` — Hook target
- `src/lib/usage_meter.py` — Usage tracking
- `src/lib/usage_queue.py` — **NEW** Async queue
- `src/lib/license_generator.py` — Key parsing
- `src/db/repository.py` — DB operations
- `src/config/logging_config.py` — structlog
- `tests/test_usage_*.py` — **NEW** Test suite

---

## Next Steps

1. **Claim Phase 1** — Create `UsageQueue` class
2. **Review plan** — Confirm architecture
3. **Execute** — Follow implementation order

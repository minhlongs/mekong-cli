---
title: "Phase 4 — Usage Metering Implementation"
description: "Track command invocations per license key with async queue, tier limits enforcement, and admin API"
status: pending
priority: P1
effort: 8h
branch: master
tags: [roiass, phase4, metering, usage-tracking]
created: 2026-03-06
---

# Phase 4 — Usage Metering Implementation Plan

## Overview

Implement usage tracking system for ROIaaS license metering with:
- Command invocation tracking per license key
- Tier-based daily limits (free: 10/day, trial: 50/day, pro: 1000/day, enterprise: unlimited)
- Async queue for usage events (SQLite staging → PostgreSQL batch flush)
- Background worker for batch processing
- Admin API for usage queries
- CLI warnings at 80%/95%/100% limits

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLI Command Execution                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  src/core/executor.py                                           │
│  RecipeExecutor.execute_step()                                  │
│  → After successful execution (exit_code=0)                     │
│  → Call UsageTracker.record()                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  src/core/usage_tracker.py (NEW)                                │
│  UsageTracker class - Sync wrapper                               │
│  → Enqueue to SQLite queue table                                │
│  → Return immediately (non-blocking)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  SQLite Queue   │
                    │  .mekong/       │
                    │  usage_queue.db │
                    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  src/core/usage_flush_worker.py (NEW)                           │
│  Background daemon process                                       │
│  → Poll SQLite queue every 5s                                   │
│  → Batch flush (100 records) to PostgreSQL                      │
│  → Handle connection pool efficiently                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  PostgreSQL     │
                    │  usage_records  │
                    │  table          │
                    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  src/api/usage_service.py (NEW)                                 │
│  FastAPI endpoints for admin queries                            │
│  → GET /usage/{key_id} - Summary                                │
│  → GET /usage/tier/{tier} - Usage by tier                       │
│  → POST /usage/reset - Manual reset                             │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure

### New Files (Create)

| File | Purpose | Lines (est) |
|------|---------|-------------|
| `src/core/usage_tracker.py` | Sync wrapper with SQLite queue | ~150 |
| `src/core/usage_flush_worker.py` | Background batch processor | ~200 |
| `src/api/usage_service.py` | Usage query API | ~180 |
| `src/api/usage_router.py` | FastAPI router endpoints | ~120 |
| `tests/test_usage_tracker.py` | Unit tests | ~150 |
| `tests/test_usage_worker.py` | Worker tests | ~100 |

### Modified Files

| File | Changes | Purpose |
|------|---------|---------|
| `src/core/executor.py` | Add usage tracking hook | Record usage after successful execution |
| `src/core/orchestrator.py` | Optional: batch tracking | Track at recipe level vs step level |
| `.mekong/usage_queue.db` | Create SQLite schema | Staging queue for async flush |

## Component Breakdown

### 1. UsageTracker (src/core/usage_tracker.py)

**Responsibilities:**
- Sync wrapper for async usage recording
- SQLite queue for staging events
- Check limits and return warnings
- Thread-safe enqueue operations

**API:**
```python
class UsageTracker:
    def __init__(self, queue_path: Optional[str] = None)

    def record(self, key_id: str, tier: str, count: int = 1) -> tuple[bool, str, dict]
        """
        Record usage and check limits.
        Returns: (allowed, warning_message, usage_summary)
        """

    def _enqueue(self, key_id: str, tier: str, count: int) -> None
        """Add to SQLite queue"""

    def _check_limit(self, key_id: str, tier: str) -> tuple[bool, str, dict]
        """Check if limit exceeded, return warning info"""

    def get_today_usage(self, key_id: str) -> int
        """Get cached today's usage count"""
```

**SQLite Queue Schema:**
```sql
CREATE TABLE IF NOT EXISTS usage_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id VARCHAR(50) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    commands_count INTEGER DEFAULT 1,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    flushed BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_usage_queue_flushed ON usage_queue (flushed);
```

### 2. UsageFlushWorker (src/core/usage_flush_worker.py)

**Responsibilities:**
- Run as background daemon
- Poll SQLite queue every 5 seconds
- Batch flush (100 records) to PostgreSQL
- Handle connection pool management
- Error handling with retry

**API:**
```python
class UsageFlushWorker:
    def __init__(self, batch_size: int = 100, poll_interval: float = 5.0)

    async def start(self) -> None
        """Start the background worker"""

    async def stop(self) -> None
        """Gracefully stop worker"""

    async def flush_batch(self) -> int
        """Flush one batch to PostgreSQL, return count flushed"""

    def _get_pending_records(self, limit: int) -> list[dict]
        """Get pending records from SQLite"""

    async def _mark_flushed(self, record_ids: list[int]) -> None
        """Mark records as flushed in SQLite"""
```

**Process Management:**
- Spawn via `subprocess.Popen` from CLI startup
- PID file: `.mekong/usage_worker.pid`
- Log file: `.mekong/logs/usage_worker.log`
- Graceful shutdown on SIGTERM/SIGINT

### 3. UsageService API (src/api/usage_service.py)

**Responsibilities:**
- Business logic for usage queries
- Aggregate usage statistics
- Tier-based filtering
- Date range queries

**API:**
```python
class UsageService:
    def __init__(self, repository: Optional[LicenseRepository] = None)

    async def get_usage_summary(self, key_id: str, days: int = 30) -> dict
        """Get usage summary for a key"""

    async def get_tier_usage(self, tier: str, days: int = 7) -> dict
        """Get aggregated usage for a tier"""

    async def get_all_usage_summary(self, days: int = 7) -> dict
        """Get summary across all keys"""

    async def reset_daily_usage(self, key_id: str) -> bool
        """Soft reset daily counter"""
```

### 4. UsageRouter (src/api/usage_router.py)

**FastAPI Endpoints:**
```python
router = APIRouter(prefix="/api/usage", tags=["usage"])

@router.get("/{key_id}")
async def get_usage(key_id: str, days: int = 30) -> dict

@router.get("/tier/{tier}")
async def get_tier_usage(tier: str, days: int = 7) -> dict

@router.get("/summary")
async def get_all_usage(days: int = 7) -> dict

@router.post("/reset/{key_id}")
async def reset_usage(key_id: str, actor_email: str) -> dict

@router.get("/limits")
async def get_tier_limits() -> dict
```

### 5. Executor Hook (src/core/executor.py)

**Integration Point:**
```python
# In _execute_shell_step(), after successful execution:
if process.returncode == 0:
    # Record usage
    from src.core.usage_tracker import get_tracker
    tracker = get_tracker()
    key_id = os.getenv("RAAS_LICENSE_KEY_ID")
    tier = os.getenv("RAAS_LICENSE_TIER", "free")

    if key_id:
        allowed, warning, summary = tracker.record(key_id, tier)
        if warning:
            self.console.print(f"[yellow]{warning}[/yellow]")
```

## Implementation Steps (Sequential)

### Phase 4.1: Database Schema & UsageTracker (2h)

1. Create SQLite queue schema migration
2. Implement `UsageTracker` class with:
   - SQLite enqueue operations
   - Limit checking logic
   - Warning generation (80%/95%/100%)
3. Add helper functions and global instance
4. Write unit tests for tracker

**Todo:**
- [ ] Create `.mekong/usage_queue.db` with schema
- [ ] Implement `src/core/usage_tracker.py`
- [ ] Add `get_tracker()` factory function
- [ ] Write `tests/test_usage_tracker.py`

### Phase 4.2: Background Flush Worker (2h)

1. Implement `UsageFlushWorker` class
2. Add batch flush logic with PostgreSQL integration
3. Add signal handlers for graceful shutdown
4. Create startup script for worker process
5. Write worker tests

**Todo:**
- [ ] Implement `src/core/usage_flush_worker.py`
- [ ] Add PID file management
- [ ] Add logging configuration
- [ ] Write `tests/test_usage_worker.py`
- [ ] Create startup script `scripts/start-usage-worker.sh`

### Phase 4.3: Executor Integration (1.5h)

1. Modify `RecipeExecutor._execute_shell_step()`
2. Add usage tracking hook after successful execution
3. Display warnings for 80%/95%/100% limits
4. Handle edge cases (no license, offline mode)

**Todo:**
- [ ] Add import for `get_tracker()` in executor.py
- [ ] Hook usage tracking in `_execute_shell_step()`
- [ ] Add warning display logic
- [ ] Test with different tier limits

### Phase 4.4: Usage Service & API (2h)

1. Implement `UsageService` class
2. Create `UsageRouter` with FastAPI endpoints
3. Register router in main API app
4. Add authentication middleware for admin endpoints

**Todo:**
- [ ] Implement `src/api/usage_service.py`
- [ ] Implement `src/api/usage_router.py`
- [ ] Register router in `src/api/__init__.py`
- [ ] Add auth check for admin endpoints

### Phase 4.5: Daily Reset Cron Job (0.5h)

1. Create reset script `scripts/reset-daily-usage.py`
2. Add cron job documentation
3. Optional: Implement in-worker auto-reset

**Todo:**
- [ ] Create reset script
- [ ] Add cron example to docs
- [ ] Document manual reset API endpoint

### Phase 4.6: Testing & Integration (1.5h)

1. Integration tests for full flow
2. Test with actual CLI commands
3. Verify PostgreSQL flush works
4. Test API endpoints with curl

**Todo:**
- [ ] Write integration tests
- [ ] Test end-to-end flow
- [ ] Verify API with curl
- [ ] Document manual testing steps

## Success Criteria

### Functional Requirements

- [ ] Command invocations tracked per license key
- [ ] Tier limits enforced (free: 10/day, trial: 50/day, pro: 1000/day)
- [ ] SQLite queue stores events reliably
- [ ] Background worker flushes to PostgreSQL every 5s
- [ ] Admin API returns usage summaries
- [ ] CLI warnings at 80%/95%/100% thresholds

### Non-Functional Requirements

- [ ] Usage tracking adds <50ms to command execution
- [ ] Worker handles 1000+ events/minute
- [ ] No data loss on worker crash (queue persists)
- [ ] Thread-safe SQLite operations

### Testing Requirements

- [ ] Unit tests for UsageTracker (90% coverage)
- [ ] Unit tests for UsageFlushWorker
- [ ] Integration tests for full flow
- [ ] Manual test: verify PostgreSQL records after CLI commands

### Documentation Requirements

- [ ] API endpoints documented in `docs/`
- [ ] Worker deployment documented
- [ ] Usage limits documented for users

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQLite lock contention | Medium | Use WAL mode, short transactions |
| Worker process dies | Medium | Auto-restart via parent process |
| PostgreSQL connection pool exhaustion | High | Batch flush, connection reuse |
| Usage tracking slows CLI | Medium | Keep sync path minimal, async flush |
| Data loss on crash | High | WAL mode, flush on shutdown |

## Dependencies

- PostgreSQL with `usage_records` table (Phase 3 completed ✅)
- `UsageMeter` class in `src/lib/usage_meter.py` (Phase 3 completed ✅)
- Tier limits configuration in `src/lib/license_generator.py` (Phase 3 completed ✅)

## Next Steps

After Phase 4 completion:
1. Phase 5 — Analytics Dashboard
2. Add usage metrics to telemetry dashboard
3. Create revenue reports from usage data

---

## Appendix: Warning Messages

```python
WARNING_MESSAGES = {
    "80": "⚠️  You've used 80% of your daily {tier} limit ({used}/{limit} commands)",
    "95": "⚠️  WARNING: You've used 95% of your daily {tier} limit ({used}/{limit} commands)",
    "100": "❌ LIMIT REACHED: You've reached your daily {tier} limit ({limit} commands). Upgrade to continue.",
}
```

## Appendix: Tier Limits Config

```python
TIER_LIMITS = {
    "free": {"commands_per_day": 10, "max_days": None},
    "trial": {"commands_per_day": 50, "max_days": 7},
    "pro": {"commands_per_day": 1000, "max_days": None},
    "enterprise": {"commands_per_day": -1, "max_days": None},
}
```

## Unresolved Questions

1. **Q:** Should we track failed commands (exit_code != 0)?
   **A:** No — only track successful executions (exit_code == 0)

2. **Q:** Should --help calls count toward limits?
   **A:** No — exclude help/docs commands

3. **Q:** How to handle multi-command recipes?
   **A:** Each step = 1 count (current design)

4. **Q:** Should enterprise unlimited still track?
   **A:** Yes — track for analytics, don't block

---

_Report generated: 2026-03-06 21:24 UTC_

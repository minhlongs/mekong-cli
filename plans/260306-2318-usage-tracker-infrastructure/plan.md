---
title: "UsageTracker Infrastructure - Feature-Level Tracking"
description: "Implementation plan for UsageTracker class với command/feature tracking, deduplication, và CLI integration"
status: pending
priority: P2
effort: 3h
branch: master
tags: [roi, usage-metering, tracking, infrastructure]
created: 2026-03-06
---

# UsageTracker Infrastructure Plan

## Context

- **Project**: mekong-cli
- **Existing**: `src/db/database.py` (DatabaseConnection), `src/lib/usage_meter.py` (UsageMeter)
- **Need**: `src/usage/usage_tracker.py` - Feature-level tracking với decorator pattern

## Requirements

1. UsageTracker class với methods: `track_command()`, `track_feature()`
2. Event schema: timestamp, command, feature_tag, license_key_hash
3. Database persistence via DatabaseConnection
4. Decorator/middleware pattern cho CLI commands
5. Deduplication logic (24h TTL)
6. Unit tests

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  mekong CLI (src/main.py)                               │
│    │                                                     │
│    ▼ @track_usage() decorator                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │  src/usage/usage_tracker.py                      │    │
│  │    - UsageTracker class                          │    │
│  │    - track_command()                             │    │
│  │    - track_feature()                             │    │
│  │    - check_duplicate() (24h TTL cache)           │    │
│  └─────────────────────────────────────────────────┘    │
│    │                                                     │
│    ▼ PostgreSQL                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  usage_events table                              │    │
│  │  - id, key_id, command, feature_tag, timestamp  │    │
│  │  - idempotency_key (unique, 24h TTL)            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: Database Schema & UsageTracker Class

### Tasks

- [ ] **Task 1.1**: Create `usage_events` table schema
  - File: `src/db/schema.py` (hoặc SQL migration file)
  - Columns: id, key_id, license_key_hash, command, feature_tag, timestamp, idempotency_key, metadata
  - Indexes: idx_key_id, idx_timestamp, idx_idempotency_key (unique)

- [ ] **Task 1.2**: Create UsageTracker class
  - File: `src/usage/usage_tracker.py`
  - Methods:
    - `__init__(repository=None)` - inject LicenseRepository
    - `track_command(key_id, command, metadata={})` - record command execution
    - `track_feature(key_id, feature_tag, metadata={})` - record feature usage
    - `_generate_idempotency_key(key_id, event_type, event_data)` - SHA256 hash
    - `_check_duplicate(idempotency_key, ttl_hours=24)` - check dedup cache

- [ ] **Task 1.3**: Add repository methods
  - File: `src/db/repository.py`
  - Methods:
    - `create_usage_event(key_id, event_type, event_data, idempotency_key, metadata)`
    - `get_usage_events(key_id, days=30)` - query events with date range
    - `get_feature_usage(key_id, feature_tag, days=7)` - feature-specific query

### Success Criteria

- [ ] Schema migration runs successfully
- [ ] UsageTracker instantiates correctly
- [ ] Events persist to PostgreSQL
- [ ] Deduplication prevents duplicate inserts

---

## Phase 2: Decorator Pattern & CLI Integration

### Tasks

- [ ] **Task 2.1**: Create `@track_usage()` decorator
  - File: `src/usage/decorators.py`
  - Extract license key from env var
  - Auto-extract command name from Typer context
  - Wrap function calls with tracking

- [ ] **Task 2.2**: Create middleware callback
  - File: `src/main.py` or `src/cli/middleware.py`
  - Add callback to main Typer app
  - Track all top-level commands automatically

- [ ] **Task 2.3**: Integrate vào existing commands
  - Apply decorator cho: `cook`, `plan`, `gateway`, `binh-phap`
  - Verify không breaking existing functionality

### Success Criteria

- [ ] Decorator auto-tracks command execution
- [ ] License key hash extracted automatically
- [ ] No breaking changes to existing commands
- [ ] Tracking events logged correctly

---

## Phase 3: Testing & Validation

### Tasks

- [ ] **Task 3.1**: Write unit tests
  - File: `tests/test_usage_tracker.py`
  - Tests:
    - test_track_command_success
    - test_track_feature_success
    - test_deduplication_24h_ttl
    - test_idempotency_key_generation
    - test_repository_integration

- [ ] **Task 3.2**: Write integration tests
  - File: `tests/test_usage_tracking_integration.py`
  - Tests:
    - test_cli_command_tracking
    - test_decorator_integration
    - test_end_to_end_event_capture

- [ ] **Task 3.3**: Run tests & verify
  - `python3 -m pytest tests/test_usage_tracker.py -v`
  - `python3 -m pytest tests/test_usage_tracking_integration.py -v`
  - All tests pass (expected: 8-10 tests)

### Success Criteria

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No breaking changes to existing tests
- [ ] Code coverage >80% for new files

---

## Implementation Steps

### Step 1: Database Schema

```sql
-- Migration: Create usage_events table
CREATE TABLE IF NOT EXISTS usage_events (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(255) NOT NULL,
    license_key_hash VARCHAR(64) NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'command' or 'feature'
    event_data JSONB NOT NULL,        -- {command, feature_tag, etc.}
    idempotency_key VARCHAR(64) UNIQUE NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_usage_events_key_id ON usage_events(key_id);
CREATE INDEX idx_usage_events_created_at ON usage_events(created_at);
CREATE INDEX idx_usage_events_event_type ON usage_events(event_type);
```

### Step 2: UsageTracker Implementation

```python
# src/usage/usage_tracker.py
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import hashlib

@dataclass
class UsageEvent:
    key_id: str
    event_type: str  # 'command' or 'feature'
    event_data: Dict[str, Any]
    idempotency_key: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

class UsageTracker:
    def __init__(self, repository=None):
        from src.db.repository import get_repository
        self._repo = repository or get_repository()
        self._dedup_cache: Dict[str, datetime] = {}  # In-memory cache

    def track_command(self, key_id: str, command: str, metadata: Optional[Dict] = None) -> bool:
        ...

    def track_feature(self, key_id: str, feature_tag: str, metadata: Optional[Dict] = None) -> bool:
        ...

    def _generate_idempotency_key(self, key_id: str, event_type: str, event_data: Dict) -> str:
        ...

    def _check_duplicate(self, idempotency_key: str, ttl_hours: int = 24) -> bool:
        ...
```

### Step 3: Decorator Implementation

```python
# src/usage/decorators.py
import functools
import os
from src.usage.usage_tracker import UsageTracker, get_tracker

def track_usage(event_type: str = "command"):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract license key
            license_key = os.getenv("RAAS_LICENSE_KEY")
            # Extract command name
            command = func.__name__
            # Track before execution
            if license_key:
                tracker = get_tracker()
                if event_type == "command":
                    tracker.track_command(key_id, command)
                else:
                    tracker.track_feature(key_id, event_type)
            # Execute original function
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database migration conflicts | Medium | Check existing schema first |
| Performance overhead | Low | Use async operations, batch inserts |
| Breaking existing commands | Medium | Test thoroughly, use decorators carefully |
| Dedup cache memory leak | Low | TTL cleanup on each check |

---

## Security Considerations

- License key hash (not raw key) stored in database
- Idempotency key prevents replay attacks
- Input validation on all event data
- Rate limiting considerations for high-frequency commands

---

## Related Files

| File | Purpose |
|------|---------|
| `src/usage/usage_tracker.py` | Main tracker class (NEW) |
| `src/usage/decorators.py` | Decorator patterns (NEW) |
| `src/usage/__init__.py` | Module exports (NEW) |
| `src/db/repository.py` | Add usage event methods |
| `src/db/schema.py` | Add usage_events table |
| `src/main.py` | Integrate middleware |
| `tests/test_usage_tracker.py` | Unit tests (NEW) |
| `tests/test_usage_tracking_integration.py` | Integration tests (NEW) |

---

## Next Steps

1. Create plan folder structure
2. Implement Phase 1 (schema + class)
3. Implement Phase 2 (decorator + integration)
4. Implement Phase 3 (tests)
5. Run full test suite
6. Verify production deployment

---

## Unresolved Questions

1. Should dedup cache be Redis-backed for multi-instance deployments?
2. Should we track failed commands or only successful ones?
3. What metadata fields are essential for analytics?

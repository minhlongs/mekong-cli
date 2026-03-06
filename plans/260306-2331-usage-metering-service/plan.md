---
title: "UsageMeteringService - Real-time Metrics & Backend Analytics"
description: "Implementation plan cho UsageMeteringService với local caching, retry logic, và secure backend transmission"
status: pending
priority: P1
effort: 4h
branch: master
tags: [roi, usage-metering, analytics, backend]
created: 2026-03-06
---

# UsageMeteringService Implementation Plan

## Context

- **Project**: mekong-cli
- **Existing**:
  - `src/usage/usage_tracker.py` (UsageTracker - PostgreSQL tracking)
  - `src/lib/usage_meter.py` (UsageMeter - limits enforcement)
  - `src/core/telemetry_collector.py` (local execution tracing)
- **Need**: `src/usage/usage_metering_service.py` - Real-time metrics collection + backend analytics

## Requirements

1. **UsageMeteringService class** - Metrics collection service
2. **MetricsEvent dataclass** - Structured event format
3. **Metrics**: API calls, feature usage, runtime duration
4. **Local caching**: SQLite buffer cho offline scenarios
5. **Retry logic**: Exponential backoff (1s, 2s, 4s, 8s, 16s), max 5 retries
6. **Circuit breaker**: Prevent cascade failures
7. **Secure transmission**: Sign requests với RAAS_LICENSE_KEY hash
8. **Backend format**: JSON schema cho analytics ingestion

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  mekong CLI (src/main.py)                                   │
│    │                                                         │
│    ▼ @track_usage() decorator                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  src/usage/usage_metering_service.py                 │    │
│  │    - UsageMeteringService                            │    │
│  │    - MetricsEvent dataclass                          │    │
│  │    - Local SQLite cache (offline buffer)             │    │
│  │    - Retry with exponential backoff                  │    │
│  │    - Circuit breaker pattern                         │    │
│  └─────────────────────────────────────────────────────┘    │
│    │                                                         │
│    ▼ HTTPS                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Backend Analytics API                               │    │
│  │    - /api/v1/analytics/usage                         │    │
│  │    - Requires: X-License-Signature header           │    │
│  │    - Payload: {tenant_id, events[], timestamp}      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Core Service & Data Models

### Tasks

- [ ] **Task 1.1**: Create MetricsEvent dataclass
  - File: `src/usage/usage_metering_service.py`
  - Fields: event_id, tenant_id, event_type, timestamp, metadata, license_key_hash
  - Event types: `api_call`, `feature_usage`, `runtime_duration`

- [ ] **Task 1.2**: Create UsageMeteringService class
  - Constructor: Initialize SQLite cache, HTTP session
  - Methods:
    - `collect_event(event: MetricsEvent)` - Buffer event
    - `flush_events()` - Send batch to backend
    - `_send_with_retry(events: list)` - Retry logic
    - `_generate_signature(payload: dict)` - HMAC-SHA256 sign

- [ ] **Task 1.3**: SQLite cache schema
  - Table: `metrics_buffer`
  - Columns: id, event_json, created_at, retry_count, last_attempt
  - Index: created_at, retry_count

### Success Criteria

- [ ] MetricsEvent creates correctly with all fields
- [ ] UsageMeteringService instantiates with SQLite cache
- [ ] Events buffer to SQLite on initialization

---

## Phase 2: Retry Logic & Circuit Breaker

### Tasks

- [ ] **Task 2.1**: Exponential backoff implementation
  - Delays: 1s → 2s → 4s → 8s → 16s (max 5 retries)
  - Jitter: ±20% random variation
  - Timeout: 30s per request

- [ ] **Task 2.2**: Circuit breaker pattern
  - States: CLOSED → OPEN → HALF_OPEN
  - Threshold: 5 failures → OPEN
  - Recovery: 60s timeout → HALF_OPEN
  - Test request: 1 success → CLOSED

- [ ] **Task 2.3**: Error handling
  - NetworkError: Retry with backoff
  - HTTPError 4xx: Don't retry (client error)
  - HTTPError 5xx: Retry with backoff
  - Timeout: Retry with backoff

### Success Criteria

- [ ] Retry delays follow exponential pattern
- [ ] Circuit breaker opens after 5 consecutive failures
- [ ] Circuit breaker closes after successful request in HALF_OPEN

---

## Phase 3: Secure Transmission

### Tasks

- [ ] **Task 3.1**: Request signature generation
  - Algorithm: HMAC-SHA256
  - Key: SHA256(RAAS_LICENSE_KEY)
  - Payload: Canonical JSON (sorted keys)
  - Header: `X-License-Signature: <signature>`

- [ ] **Task 3.2**: HTTPS client setup
  - Base URL: `RAAS_ANALYTICS_URL` env var
  - Default: `https://analytics.raas.mekong.dev/api/v1`
  - Certificate verification: Enabled
  - Timeout: 30s

- [ ] **Task 3.3**: Backend JSON schema
  ```json
  {
    "tenant_id": "string",
    "license_key_hash": "string",
    "timestamp": "ISO8601",
    "events": [
      {
        "event_type": "api_call|feature_usage|runtime_duration",
        "event_data": {},
        "duration_ms": 0
      }
    ],
    "signature": "string"
  }
  ```

### Success Criteria

- [ ] Signature generated correctly with HMAC-SHA256
- [ ] HTTPS requests include X-License-Signature header
- [ ] Backend accepts valid signatures

---

## Phase 4: CLI Integration

### Tasks

- [ ] **Task 4.1**: Decorator integration
  - File: `src/usage/decorators.py`
  - Update `@track_usage()` to use UsageMeteringService
  - Capture runtime duration automatically
  - Buffer events on error (offline mode)

- [ ] **Task 4.2**: Command lifecycle hooks
  - On command start: Record start timestamp
  - On command end: Record duration, flush events
  - On error: Buffer event, increment retry count

- [ ] **Task 4.3**: Environment configuration
  - `RAAS_ANALYTICS_URL`: Backend API URL
  - `RAAS_LICENSE_KEY`: For signature generation
  - `RAAS_TENANT_ID`: Tenant identifier
  - `METRICS_FLUSH_INTERVAL`: Auto-flush interval (default: 30s)

### Success Criteria

- [ ] Commands auto-track runtime duration
- [ ] Events flush on command completion
- [ ] Offline mode buffers events locally

---

## Phase 5: Testing & Validation

### Tasks

- [ ] **Task 5.1**: Unit tests
  - File: `tests/test_usage_metering_service.py`
  - Tests:
    - test_collect_event_success
    - test_flush_events_batch
    - test_retry_exponential_backoff
    - test_circuit_breaker_state_transitions
    - test_signature_generation
    - test_offline_caching

- [ ] **Task 5.2**: Integration tests
  - File: `tests/test_usage_metering_integration.py`
  - Tests:
    - test_cli_command_tracking
    - test_decorator_duration_tracking
    - test_end_to_end_event_transmission

- [ ] **Task 5.3**: Run tests & verify
  - `python3 -m pytest tests/test_usage_metering_service.py -v`
  - `python3 -m pytest tests/test_usage_metering_integration.py -v`

### Success Criteria

- [ ] All unit tests pass (expected: 10-12 tests)
- [ ] All integration tests pass (expected: 5-7 tests)
- [ ] Code coverage >80% for new files

---

## Implementation Steps

### Step 1: Core Service

```python
# src/usage/usage_metering_service.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import hashlib
import hmac
import json
import sqlite3
from enum import Enum

class EventType(str, Enum):
    API_CALL = "api_call"
    FEATURE_USAGE = "feature_usage"
    RUNTIME_DURATION = "runtime_duration"

@dataclass
class MetricsEvent:
    event_id: str
    tenant_id: str
    event_type: EventType
    event_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[float] = None
    license_key_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class UsageMeteringService:
    def __init__(self, analytics_url: Optional[str] = None):
        self._analytics_url = analytics_url or os.getenv(
            "RAAS_ANALYTICS_URL",
            "https://analytics.raas.mekong.dev/api/v1"
        )
        self._license_key = os.getenv("RAAS_LICENSE_KEY", "")
        self._tenant_id = os.getenv("RAAS_TENANT_ID", "")
        self._cache = self._init_sqlite_cache()
        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._circuit_opened_at: Optional[datetime] = None
```

### Step 2: Retry Logic

```python
import asyncio
import random

async def _send_with_retry(self, events: List[MetricsEvent]) -> bool:
    """Send events with exponential backoff."""
    max_retries = 5
    base_delay = 1.0  # seconds

    for attempt in range(max_retries):
        # Check circuit breaker
        if not self._circuit_allows_request():
            return False

        try:
            # Send HTTP request
            success = await self._send_http(events)
            if success:
                self._on_success()
                return True
        except NetworkError:
            # Retry with backoff
            pass
        except HTTPError as e:
            if 400 <= e.status < 500:
                # Client error - don't retry
                return False
            # Server error - retry

        # Calculate delay with jitter
        delay = base_delay * (2 ** attempt)
        jitter = random.uniform(-0.2, 0.2) * delay
        await asyncio.sleep(delay + jitter)

    # All retries exhausted - open circuit
    self._on_failure()
    return False
```

### Step 3: Signature Generation

```python
def _generate_signature(self, payload: dict) -> str:
    """Generate HMAC-SHA256 signature."""
    # Hash license key
    key = hashlib.sha256(self._license_key.encode()).digest()

    # Canonical JSON (sorted keys)
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))

    # HMAC-SHA256
    signature = hmac.new(key, payload_json.encode(), hashlib.sha256).hexdigest()

    return signature

def _prepare_payload(self, events: List[MetricsEvent]) -> dict:
    """Prepare payload for backend."""
    return {
        "tenant_id": self._tenant_id,
        "license_key_hash": self._hash_license_key(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "events": [
            {
                "event_type": e.event_type.value,
                "event_data": e.event_data,
                "duration_ms": e.duration_ms,
                "metadata": e.metadata,
            }
            for e in events
        ],
    }
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Network failures | High | SQLite cache + retry logic |
| Backend downtime | High | Circuit breaker prevents cascade |
| License key exposure | Critical | HMAC signature (never send raw key) |
| Performance overhead | Low | Async operations, batch flush |
| SQLite corruption | Medium | WAL mode, periodic cleanup |

---

## Security Considerations

- **License key never transmitted** - Only SHA256 hash sent
- **HMAC-SHA256 signatures** - Prevents request tampering
- **HTTPS required** - All transmissions encrypted
- **Rate limiting** - Backend-side protection
- **Input validation** - All event data validated before buffering

---

## Related Files

| File | Purpose |
|------|---------|
| `src/usage/usage_metering_service.py` | Main service (NEW) |
| `src/usage/usage_tracker.py` | Existing tracker (integrate) |
| `src/usage/decorators.py` | Update decorators |
| `src/usage/__init__.py` | Module exports |
| `tests/test_usage_metering_service.py` | Unit tests (NEW) |
| `tests/test_usage_metering_integration.py` | Integration tests (NEW) |

---

## Next Steps

1. Create plan folder structure
2. Implement Phase 1 (Core service + data models)
3. Implement Phase 2 (Retry + circuit breaker)
4. Implement Phase 3 (Secure transmission)
5. Implement Phase 4 (CLI integration)
6. Implement Phase 5 (Tests)
7. Run full test suite
8. Verify production deployment

---

## Unresolved Questions

1. **Backend API endpoint**: What is the exact URL for analytics ingestion?
2. **Tenant ID source**: Should tenant_id be extracted from license key or separate env var?
3. **Flush strategy**: Time-based (30s) or count-based (100 events) or both?
4. **Event deduplication**: Should we deduplicate events before sending (similar to UsageTracker)?
5. **Data retention**: How long to keep events in SQLite cache before cleanup?

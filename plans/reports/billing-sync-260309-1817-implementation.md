# Billing Sync Implementation Report

**Date:** 2026-03-09
**Type:** Implementation Report
**Status:** ✅ Complete

---

## Summary

Implemented CLI command `mekong billing sync` để sync usage records từ local SQLite store lên RaaS Gateway v2/usage endpoint.

---

## Features Implemented

### 1. Core Service (`src/raas/billing_sync.py`)

| Component | Description |
|-----------|-------------|
| `BillingSyncService` | Main service class với đầy đủ sync logic |
| `SyncConfig` | Configuration dataclass (db path, gateway URL, retry settings) |
| `SyncResult` | Result dataclass với success/failure status |
| `UsageRecord` | Local usage record schema |

### 2. Key Features

#### Idempotency Key Generation
```python
def generate_idempotency_key(self, records: list[UsageRecord]) -> str:
    # SHA256 hash của sorted event IDs
    # Format: mk_idem_<16 hex chars>
    # Same records → same key (order-independent)
```

#### Payload Schema (RaaS Gateway v2/usage)
```json
{
  "tenant_id": "tenant_123",
  "license_key": "mk_***",
  "events": [...],
  "summary": {
    "total_events": 10,
    "total_input_tokens": 5000,
    "total_output_tokens": 2500,
    "total_duration_ms": 15000.0
  }
}
```

#### Retry Logic với Exponential Backoff
- Max retries: 5
- Backoff: 1s → 2s → 4s → 8s → 16s → 32s (cap at 60s)
- Retry on: 5xx errors, timeouts
- No retry on: 4xx client errors
- Special handling: 429 rate limit với Retry-After header

#### Validation
- Response validation: `status == "accepted"`
- HTTP 200 OK required
- Error logging với telemetry

### 3. CLI Commands (`src/cli/billing_commands.py`)

#### `mekong billing sync`
```bash
# Basic sync
mekong billing sync

# Dry run (preview)
mekong billing sync --dry-run

# Verbose output
mekong billing sync -v

# Force resync
mekong billing sync --force --limit 50

# Custom API key
mekong billing sync -l mk_custom_key
```

**Options:**
- `--license, -l`: Override API key
- `--dry-run, -n`: Simulate without submitting
- `--verbose, -v`: Show detailed info
- `--force, -f`: Force resync synced records
- `--limit`: Limit records to sync

#### `mekong billing sync-status`
```bash
mekong billing sync-status
```

**Displays:**
- API key configuration status
- Gateway URL
- Unsynced records count
- Synced records count
- Last sync timestamp
- Recent sync history (5 entries)

---

## Database Schema

### `usage_records` Table
```sql
CREATE TABLE usage_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    endpoint TEXT,
    model TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    duration_ms REAL DEFAULT 0,
    metadata TEXT,
    synced INTEGER DEFAULT 0,
    sync_attempts INTEGER DEFAULT 0,
    last_sync_error TEXT,
    synced_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### `sync_history` Table
```sql
CREATE TABLE sync_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idempotency_key TEXT UNIQUE NOT NULL,
    records_count INTEGER NOT NULL,
    payload_size INTEGER NOT NULL,
    status TEXT NOT NULL,
    gateway_response TEXT,
    error TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

---

## Tests (`tests/raas/test_billing_sync.py`)

**26 tests, all passing:**

| Category | Tests |
|----------|-------|
| Idempotency Key Generation | 4 tests |
| Payload Building | 4 tests |
| Database Operations | 4 tests |
| Retry Logic | 5 tests |
| Sync to Gateway | 3 tests |
| Sync History | 2 tests |
| Global Service | 2 tests |
| Edge Cases | 2 tests |

**Test Coverage:**
- Unique key generation
- Same records → same key
- Order independence
- Payload schema validation
- Summary calculation
- Fetch unsynced records
- Mark as synced/failed
- Exponential backoff calculation
- Retry on 5xx/timeout
- No retry on 4xx
- Success/failure workflows

---

## Usage Examples

### 1. Check Sync Status
```bash
$ mekong billing sync-status
📊 Billing Sync Status

                       Sync Status
 API Key           ✓ Configured
 Gateway           https://raas.agencyos.network/v2/usage
 Unsynced Records  0
 Synced Records    0
 Last Sync         Never
```

### 2. Dry Run
```bash
$ MEKONG_API_KEY=mk_test_1234 mekong billing sync --dry-run
🔄 Billing Sync - RaaS Gateway

Gateway: https://raas.agencyos.network/v2/usage
API Key: mk_***1234

🛑 Dry run mode - will not submit

Would sync 10 record(s):
  • cli:command - /api/v1/cook - 2026-03-09T10:00:00Z
  • llm:call - /api/v1/plan - 2026-03-09T10:01:00Z
  ...

Payload size: 2048 bytes
```

### 3. Execute Sync
```bash
$ MEKONG_API_KEY=mk_live_xyz mekong billing sync -v
🔄 Billing Sync - RaaS Gateway

Gateway: https://raas.agencyos.network/v2/usage
API Key: mk_***xyz

✓ Synced 10 record(s)
Payload size: 2048 bytes
Elapsed: 342ms
Idempotency key: mk_idem_a1b2c3d4e5f6

Gateway response: accepted
```

---

## Error Handling

### Missing API Key
```
✗ Error: API key not configured
Set MEKONG_API_KEY or RAAS_LICENSE_KEY environment variable
```

### Gateway Timeout
```
✗ Error: Sync failed
Timeout: Connection timeout
Records failed: 10
Retry count: 5
```

### Rate Limit
```
⚠ Rate limit exceeded
Waiting 60s before retry...
```

---

## Configuration

### Environment Variables
```bash
export MEKONG_API_KEY=mk_live_...
# Or
export RAAS_LICENSE_KEY=mk_live_...
```

### SyncConfig Defaults
```python
SyncConfig(
    db_path="~/.mekong/usage.db",
    gateway_url="https://raas.agencyos.network/v2/usage",
    batch_size=100,
    max_retries=5,
    base_backoff_seconds=1.0,
    max_backoff_seconds=60.0,
    request_timeout_seconds=30.0,
)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    mekong billing sync                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  BillingSyncService                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. fetch_unsynced_records()                          │   │
│  │    - SELECT FROM usage_records WHERE synced=0        │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. generate_idempotency_key()                        │   │
│  │    - SHA256(sort(event_ids)) → mk_idem_<hash>        │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. build_payload()                                   │   │
│  │    - Transform to RaaS v2/usage schema               │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. send_to_gateway()                                 │   │
│  │    - POST with retry + exponential backoff           │   │
│  │    - Validate: status == "accepted"                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                    ┌───────┴───────┐                         │
│                    ▼               ▼                         │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ Success              │  │ Failure              │         │
│  │ - mark_as_synced()   │  │ - mark_sync_failed() │         │
│  │ - record_history()   │  │ - record_history()   │         │
│  └──────────────────────┘  └──────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  RaaS Gateway                                                │
│  POST https://raas.agencyos.network/v2/usage                │
│  Headers:                                                    │
│  - Authorization: Bearer mk_...                             │
│  - X-Idempotency-Key: mk_idem_...                           │
│  - Content-Type: application/json                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `src/raas/billing_sync.py` | Created | 450 |
| `src/cli/billing_commands.py` | Modified | +140 |
| `tests/raas/test_billing_sync.py` | Created | 520 |

---

## Unresolved Questions

None - implementation complete.

---

## Next Steps (Optional)

1. **Add telemetry logging** - Track sync metrics to AgencyOS dashboard
2. **Add cron scheduler** - Auto-sync every N minutes
3. **Add compression** - Gzip payload for large batches
4. **Add webhook callback** - Notify on sync complete/failed

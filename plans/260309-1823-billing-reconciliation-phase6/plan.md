# Phase 6: Billing Reconciliation Service - Implementation Plan

**Date:** 2026-03-09
**Status:** Pending Approval

---

## Overview

Implement Phase 6: Billing Reconciliation Service tích hợp BillingSyncService với RaaS Gateway để sync và reconcile usage records.

---

## Requirements

### 1. Billing Reconciliation Service (`src/raas/billing_reconciliation.py`)

- Fetch unsynced records từ local SQLite via `BillingSyncService.get_service()`
- Validate records against RaaS Gateway v2/usage endpoint
- Compare local vs remote usage data
- Resolve discrepancies (missing records, duplicate charges)
- Emit `EventType.BILLING_RECONCILED` events
- Log tất cả steps qua logger và rich Console

### 2. CLI Command (`src/cli/billing_commands.py`)

- `mekong billing reconcile` - Trigger full reconciliation cycle
- Options: `--date`, `--license`, `--all`, `--dry-run`, `--verbose`
- Rich console output với progress indicators
- Display reconciliation results summary

### 3. Integration Points

- `BillingSyncService` - Fetch và sync records
- `BillingEventEmitter` - Emit reconciliation events
- `EventType.BILLING_RECONCILIATION` - Event type (đã có trong event_bus.py)
- RaaS Gateway API - `https://raas.agencyos.network/v2/usage/reconcile`

---

## Implementation Steps

### Step 1: Create BillingReconciliationService

**File:** `src/raas/billing_reconciliation.py`

**Classes:**
- `ReconciliationRecord` - Dataclass cho reconciliation result
- `BillingReconciliationService` - Main service class
- `ReconciliationConfig` - Configuration dataclass

**Methods:**
- `fetch_local_records()` - Get unsynced records from SQLite
- `fetch_remote_records()` - Get records from RaaS Gateway
- `compare_records()` - Compare local vs remote
- `resolve_discrepancies()` - Auto-resolve minor variances
- `reconcile_batch()` - Main reconciliation workflow
- `emit_reconciliation_event()` - Emit events

### Step 2: Update CLI Commands

**File:** `src/cli/billing_commands.py`

**Commands:**
- `billing_reconcile()` - Main reconcile command
- `billing_reconcile_status()` - Show reconciliation status

### Step 3: Add Tests

**File:** `tests/raas/test_billing_reconciliation.py`

**Test Categories:**
- Record comparison logic
- Discrepancy resolution
- RaaS Gateway integration
- CLI command tests
- Event emission tests

---

## Schema Design

### ReconciliationRecord

```python
@dataclass
class ReconciliationRecord:
    record_id: str
    license_key: str
    local_amount: Decimal
    remote_amount: Decimal
    variance: Decimal
    variance_percent: float
    status: str  # 'matched', 'variance', 'missing_remote', 'missing_local'
    discrepancies: List[Dict]
    resolved: bool
    resolved_at: Optional[datetime]
```

### RaaS Gateway Payload

**Request:**
```json
POST /v2/usage/reconcile
{
  "license_key": "mk_...",
  "period_start": "2026-03-08T00:00:00Z",
  "period_end": "2026-03-09T00:00:00Z",
  "local_summary": {
    "total_events": 100,
    "total_amount": "49.00"
  }
}
```

**Response:**
```json
{
  "status": "accepted",
  "remote_summary": {
    "total_events": 100,
    "total_amount": "49.00"
  },
  "discrepancies": []
}
```

---

## Acceptance Criteria

- [ ] `mekong billing reconcile` command hoạt động
- [ ] Fetch được unsynced records từ local SQLite
- [ ] Sync và validate với RaaS Gateway thành công
- [ ] Phát hiện và resolve discrepancies
- [ ] Emit `EventType.BILLING_RECONCILIATION` events
- [ ] Rich console output với progress
- [ ] Tests pass 100%

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/raas/billing_reconciliation.py` | Create | Reconciliation service |
| `src/cli/billing_commands.py` | Modify | Add reconcile commands |
| `tests/raas/test_billing_reconciliation.py` | Create | Tests |
| `plans/reports/billing-reconciliation-phase6-report.md` | Create | Report |

---

## Dependencies

- `BillingSyncService` (đã implement)
- `BillingEventEmitter` (đã có)
- `EventType.BILLING_RECONCILIATION` (đã có)
- RaaS Gateway v2/usage/reconcile endpoint

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gateway endpoint chưa có | High | Mock cho testing, fallback gracefully |
| Rate limiting | Medium | Respect retry-after headers |
| Data mismatch | Medium | Log chi tiết, manual review option |

---

## Next Steps

1. Approve plan này
2. Implement BillingReconciliationService
3. Add CLI commands
4. Write tests
5. Verify production

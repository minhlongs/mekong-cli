---
title: "Automated License Enforcement"
description: "License status checking middleware integration with audit logging"
status: pending
priority: P2
effort: 3h
branch: master
tags: [license, rate-limiting, middleware, audit]
created: 2026-03-07
---

# Automated License Enforcement Plan

## Overview

Implement license enforcement service that validates license status before rate limit checks, with comprehensive audit logging for compliance and analytics.

## Key Insights

- Existing `tier_rate_limit_middleware.py` extracts license key but doesn't validate license **status** (active/suspended/revoked)
- `rate_limit_events` table exists but lacks event types for license enforcement actions
- Need 5-min cache for license status checks to reduce DB load

## Architecture

```
Request → License Enforcement → Rate Limit → Handler
              ↓                    ↓
        Check status          Check quota
        Cache 5-min TTL      Token bucket
              ↓                    ↓
        [suspended?]          [exceeded?]
              ↓                    ↓
        403 Forbidden        429 Too Many
```

## Phases

| Phase | Description | Effort | Status |
|-------|-------------|--------|--------|
| [Phase 1: License Enforcement Service](#phase-1-license-enforcement-service) | Core service with cache | 1h | pending |
| [Phase 2: Middleware Integration](#phase-2-middleware-integration) | Integrate with tier_rate_limit_middleware | 45m | pending |
| [Phase 3: Audit Logging](#phase-3-audit-logging) | Extend rate_limit_events schema | 30m | pending |
| [Phase 4: Testing](#phase-4-testing) | Unit + integration tests | 45m | pending |

---

## Phase 1: License Enforcement Service

**File:** `src/services/license_enforcement.py`

### Requirements

- `check_license_status(license_key)` → `LicenseStatus` enum (ACTIVE, SUSPENDED, REVOKED, EXPIRED, INVALID)
- `is_tier_sufficient(license_key, required_tier)` → bool
- LRU cache with 5-min TTL for status checks
- Database lookup via `raas_license_keys` table

### Implementation Steps

1. Create `src/services/` directory if not exists
2. Implement `LicenseStatus` enum
3. Implement `LicenseEnforcementService` class with:
   - `_check_license_in_db(license_key)` - private DB lookup
   - `check_license_status(license_key)` - public method with cache
   - `is_tier_sufficient(license_key, required_tier)` - tier comparison
   - `_cache_get(key)` / `_cache_set(key, value)` - TTL cache helpers
4. Add global `get_license_enforcement()` function

### Related Files

- Create: `src/services/license_enforcement.py`
- Read: `src/lib/jwt_license_generator.py` (JWT validation patterns)

### Todo

- [ ] Create `src/services/` directory
- [ ] Implement `LicenseStatus` enum
- [ ] Implement `LicenseEnforcementService` class
- [ ] Add LRU cache with 5-min TTL
- [ ] Export via `__all__`

### Success Criteria

- Service validates license status from DB
- Cache reduces DB queries by 80%+
- Unit tests cover all status types

---

## Phase 2: Middleware Integration

**File:** `src/lib/tier_rate_limit_middleware.py`

### Requirements

- Import `LicenseEnforcementService`
- Add license check **before** rate limit check
- Return 403 with `license_suspended` or `license_revoked` error
- Bypass rate limit if license invalid

### Implementation Steps

1. Add import at top:
   ```python
   from src.services.license_enforcement import get_license_enforcement, LicenseStatus
   ```

2. In `dispatch()` method, add license check after extracting license key:
   ```python
   # After line 243: license_key = self._extract_license_key(request)
   license_status = await self._check_license_status(license_key)
   if license_status != LicenseStatus.ACTIVE:
       return self._license_blocked_response(license_status)
   ```

3. Add helper methods:
   - `_check_license_status(license_key)` - call service
   - `_license_blocked_response(status)` - build 403 response

4. Update error response format:
   ```json
   {
     "error": "license_suspended",
     "message": "License suspended - contact support",
     "status": "suspended"
   }
   ```

### Related Files

- Modify: `src/lib/tier_rate_limit_middleware.py`

### Todo

- [ ] Add imports for license enforcement
- [ ] Add `_check_license_status()` helper method
- [ ] Add `_license_blocked_response()` helper method
- [ ] Integrate check before rate limit in `dispatch()`
- [ ] Update response headers for 403

### Success Criteria

- 403 returned for suspended/revoked licenses
- Rate limit skipped for invalid licenses
- Response includes license status in error

---

## Phase 3: Audit Logging

**Files:** `src/db/migrations/007_add_license_enforcement_events.sql`, `src/telemetry/rate_limit_metrics.py`

### Requirements

- Add `license_suspended`, `license_revoked`, `license_blocked` event types
- Log enforcement decisions to `rate_limit_events` table
- Include license status in metadata

### Implementation Steps

1. Create migration `007_add_license_enforcement_events.sql`:
   ```sql
   ALTER TABLE rate_limit_events
   ADD COLUMN license_status VARCHAR(50);

   ALTER TABLE rate_limit_events
   ALTER COLUMN event_type DROP NOT NULL;

   -- Add new event types to CHECK constraint
   ALTER TABLE rate_limit_events
   DROP CONSTRAINT IF EXISTS rate_limit_events_event_type_check;

   ALTER TABLE rate_limit_events
   ADD CONSTRAINT rate_limit_events_event_type_check
   CHECK (event_type IN (
     'override_applied', 'request_allowed', 'rate_limited',
     'license_suspended', 'license_revoked', 'license_blocked'
   ));
   ```

2. Update `RateLimitEvent` dataclass in `src/telemetry/rate_limit_metrics.py`:
   ```python
   @dataclass
   class RateLimitEvent:
       # ... existing fields
       license_status: Optional[str] = None  # NEW
   ```

3. Add logging helper in middleware:
   ```python
   def _log_license_enforcement(self, tenant_id, status, endpoint):
       self._log_rate_limit_event(
           event_type=f"license_{status.value}",
           tenant_id=tenant_id,
           tier="unknown",
           endpoint=endpoint,
           preset="license_check",
           metadata={"license_status": status.value},
       )
   ```

### Related Files

- Create: `src/db/migrations/007_add_license_enforcement_events.sql`
- Modify: `src/telemetry/rate_limit_metrics.py`
- Modify: `src/lib/tier_rate_limit_middleware.py`

### Todo

- [ ] Create SQL migration for new event types
- [ ] Add `license_status` field to `RateLimitEvent`
- [ ] Update CHECK constraint for event_type
- [ ] Add logging call in middleware
- [ ] Run migration on Supabase

### Success Criteria

- Migration runs without errors
- Events logged with correct status
- Dashboard can query license enforcement events

---

## Phase 4: Testing

**Files:** `tests/test_license_enforcement.py`

### Requirements

- Test all `LicenseStatus` types
- Test cache TTL behavior
- Test middleware integration
- Test audit logging

### Test Cases

#### Unit Tests (test_license_enforcement.py)

```python
class TestLicenseStatus:
    - test_check_active_license
    - test_check_suspended_license
    - test_check_revoked_license
    - test_check_expired_license
    - test_check_invalid_license

class TestTierSufficient:
    - test_free_insufficient_for_pro
    - test_pro_sufficient_for_pro
    - test_enterprise_sufficient_for_all

class TestCache:
    - test_cache_hit_reduces_db_calls
    - test_cache_expires_after_5_min
```

#### Integration Tests (test_license_enforcement_middleware.py)

```python
class TestMiddlewareIntegration:
    - test_active_license_passes
    - test_suspended_license_returns_403
    - test_revoked_license_returns_403
    - test_invalid_license_returns_403
    - test_audit_log_created_for_blocked
```

### Related Files

- Create: `tests/test_license_enforcement.py`
- Create: `tests/test_license_enforcement_middleware.py`

### Todo

- [ ] Write unit tests for `LicenseEnforcementService`
- [ ] Write unit tests for cache behavior
- [ ] Write integration tests for middleware
- [ ] Run test suite
- [ ] Fix any failures

### Success Criteria

- All tests pass
- 90%+ code coverage
- No regressions in existing rate limit tests

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cache causes stale license status | Medium | 5-min TTL acceptable trade-off; manual cache invalidation API |
| DB performance under load | Low | Cache reduces 80%+ queries; connection pooling |
| Breaking existing rate limit flow | Medium | Comprehensive test coverage; rollback plan |

## Security Considerations

- License keys MUST NOT be logged in plain text (hash before logging)
- Cache MUST be per-license-key (no cross-tenant leakage)
- 403 responses MUST NOT reveal internal DB structure

## Next Steps

1. Review and approve plan
2. Execute phases in order
3. Run full test suite after Phase 4
4. Deploy with feature flag for gradual rollout

---

## Related Documentation

- `docs/tier-rate-limiting.md` - Rate limiting overview
- `src/lib/jwt_license_generator.py` - JWT validation
- `src/telemetry/rate_limit_metrics.py` - Audit logging

## Unresolved Questions

- Should there be a manual cache invalidation endpoint for support ops?
- Should suspended licenses have a grace period before 403?
- Do we need webhook notifications when license is blocked?

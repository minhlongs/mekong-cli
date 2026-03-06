---
title: "ROIaaS Phase 6c — License Enforcement"
description: "License revocation, expiration handling, and integration tests"
status: completed
priority: P1
effort: 2h
branch: master
tags: [roiaaS, license, enforcement, integration]
created: 2026-03-07
completed: 2026-03-07
---

# ROIaaS Phase 6c — License Enforcement

## Context
- **Project**: mekong-cli
- **Existing**: Basic license gate in `src/lib/raas_gate.py`
- **Gap**: No revocation/expiration handling, unclear error messages
- **Goal**: Production-grade license enforcement with clear user feedback

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              License Gate Entry Point                       │
│                    src/lib/raas_gate.py                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           License Status Checker (NEW)                      │
│          _license_status() → QuotaState                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
  QuotaState         QuotaState              QuotaState
  status="valid"     status="expired"       status="revoked"
  (proceed)          (block + date)          (block + message)
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Quota Cache (Enhanced)                         │
│        Added: status, expires_at_ts fields                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│             Remote API (Polar)                              │
│         401/403/429 handle gracefully                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: License Status Handling

### Tasks
- [x] **Task 1.1**: Add `_license_status()` to `src/lib/raas_gate.py`
  - Check revocation via Polar API/cache
  - Check expiration via JWT exp claim
  - Return `QuotaState` with status field

- [x] **Task 1.2**: Add `_license_expires_at()` to `src/lib/raas_gate.py`
  - Return expiration timestamp for valid licenses
  - Return None for revoked/expired/invalid

- [x] **Task 1.3**: Enhance `QuotaState` in `src/raas/quota_cache.py`
  - Add `status: str` field
  - Add `expires_at_ts: int | None` field
  - Add `is_expired` property

- [x] **Task 1.4**: Create error message helpers in `src/lib/quota_error_messages.py`
  - `format_license_revoked()` - clear revocation message
  - `format_license_expired()` - show expiration date

**Success Criteria**:
- All license states detected (valid/expired/revoked/invalid/unlicensed)
- Error messages are user-friendly
- Expiration dates displayed for expired licenses

---

## Phase 2: Remote API Error Handling

### Tasks
- [x] **Task 2.1**: Handle 401/403 responses from Polar API
  - Map to appropriate license status
  - Cache revocation state for performance

- [x] **Task 2.2**: Handle 429 (rate limit) gracefully
  - Log rate limit event
  - Return appropriate quota state

- [x] **Task 2.3**: Add timeout handling (5s)
  - Detect Polar API timeouts
  - Fallback to last known state

**Success Criteria**:
- All HTTP errors handled without crashes
- Rate limits logged for monitoring
- Graceful degradation when Polar down

---

## Phase 3: Integration Tests

### Tasks
- [x] **Task 3.1**: Create `tests/test_license_gate_integration.py`
  - 21 tests covering all scenarios
  - Mock Polar API responses
  - Test revocation, expiration, valid licenses

- [x] **Task 3.2**: Test quota cache integration
  - Cache retrieval of license state
  - Expiration check in cache

**Success Criteria**:
- All 21 tests passing
- >80% code coverage for new modules
- No regression in existing tests

---

## Success Criteria (Definition of Done)

- [x] **License Status**: All states detected (valid/expired/revoked)
- [x] **Error Messages**: User-friendly messages with remediation steps
- [x] **Remote API**: 401/403/429 handled gracefully
- [x] **Integration Tests**: 21 tests passing
- [x] **Performance**: No impact on valid licenses
- [x] **Documentation**: Updated in plan files

---

## Related Files

### Created
- `tests/test_license_gate_integration.py` - 21 tests
- `src/lib/quota_error_messages.py` (enhanced)

### Modified
- `src/lib/raas_gate.py` - Added _license_status(), _license_expires_at()
- `src/raas/quota_cache.py` - Added status, expires_at_ts to QuotaState

---

## Unresolved Questions

1. Should revoked licenses be cached locally? (Trait: Yes - improves performance)
2. Do we need a CLI command to check license status? (Trade: Yes - for troubleshooting)
3. Should expired licenses show grace period? (Decision: No - strict enforcement)

---

*Status: Completed 2026-03-07*

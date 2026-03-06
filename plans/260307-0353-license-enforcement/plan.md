---
title: "License Enforcement Phase 6 - Offline Grace & Error Messages"
description: "Implement offline grace period (24h), comprehensive logging, and clear error messages for license enforcement"
status: complete
priority: P1
effort: 6h
branch: master
tags: [license, raas, enforcement, offline, analytics]
created: 2026-03-07
completed: 2026-03-07
report: ../plans/reports/fullstack-developer-260307-0353-license-enforcement-phase6.md
---

# License Enforcement Phase 6 - Implementation Plan

## Context

**Currently Implemented (Phase 6a-c):**
- `src/lib/raas_gate.py`: Remote validation, quota checking, rate limiting
- `src/raas/quota_cache.py`: SQLite cache với TTL 5 phút
- `src/raas/violation_tracker.py`: Track violations cho analytics
- `src/lib/raas_gate_validator.py`: Python wrapper gọi TypeScript validator

**Gaps Identified:**
1. ❌ **Offline grace period** - Mới chỉ có 5 phút TTL, cần 24h khi không có network
2. ❌ **Logging validation attempts** - Chưa log đầy đủ cho analytics
3. ❌ **Error messages** - Cần rõ ràng hơn với instructions để renew/upgrade
4. ❌ **Graceful degradation** - Cần cơ chế fallback khi remote API unavailable

## Implementation Strategy

### Phase 6d: Offline Grace Period (24h)
- Extend `QuotaState` với `grace_period_remaining` field
- Khi remote API fail, check nếu cache còn trong grace period (24h) → allow với warning
- Log offline mode event cho analytics

### Phase 6e: Validation Logging
- Tạo `ValidationLogger` class track tất cả validation attempts
- Log: timestamp, key_id, result, duration, error_type, offline_mode
- Store vào PostgreSQL `validation_logs` table

### Phase 6f: Error Message Improvements
- Refactor `format_quota_error` với actionable instructions
- Thêm error messages cho: offline grace, revoked, expired, rate limit
- Include renewal commands và upgrade links

### Phase 6g: Graceful Degradation
- Implement circuit breaker pattern cho remote API
- After 3 failures → switch to offline mode for 24h
- Auto-retry after grace period expires

## Files to Modify

| File | Changes |
|------|---------|
| `src/raas/quota_cache.py` | Add grace period fields, extend TTL to 24h |
| `src/lib/raas_gate.py` | Add offline mode logic, validation logging |
| `src/lib/quota_error_messages.py` | Enhance error messages with instructions |
| `src/raas/violation_tracker.py` | Add validation log tracking |

## Files to Create

| File | Purpose |
|------|---------|
| `src/raas/validation_logger.py` | Log all validation attempts |
| `src/lib/license_error_messages.py` | Centralized error message formatting |
| `tests/test_offline_grace_period.py` | Test offline mode |
| `tests/test_validation_logging.py` | Test logging |

## Success Criteria

- [x] CLI hoạt động trong 24h khi không có network
- [x] Tất cả validation attempts được log
- [x] Error messages hiển thị clear instructions
- [x] Tests coverage > 80% (36 tests, 100% pass)
- [x] Không breaking changes cho existing license flow

## Dependencies

- PostgreSQL database cho validation logs
- TypeScript validator (`src/lib/raas-gate.ts`)
- Credit rate limiter (`src/raas/credit_rate_limiter.py`)

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Offline mode bị abuse | Log tất cả offline usage, flag suspicious patterns |
| Validation logs làm chậm CLI | Async logging, batch writes |
| Error messages quá dài | Simple mode + detailed mode |

---

## Phase Files

- [phase-01-offline-grace-period.md](./phase-01-offline-grace-period.md)
- [phase-02-validation-logging.md](./phase-02-validation-logging.md)
- [phase-03-error-messages.md](./phase-03-error-messages.md)
- [phase-04-graceful-degradation.md](./phase-04-graceful-degradation.md)
- [phase-05-testing.md](./phase-05-testing.md)

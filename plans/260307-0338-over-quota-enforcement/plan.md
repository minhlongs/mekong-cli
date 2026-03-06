---
title: "Phase 6c: Over-Quota Enforcement & Hard Usage Limits"
description: "Real-time quota checks, hard enforcement, upgrade prompts, webhook integration"
status: pending
priority: P1
effort: 8h
branch: master
tags: [raas, quota, enforcement, phase6c, billing]
created: 2026-03-07
---

# Phase 6c: Over-Quota Enforcement - Implementation Plan

## Overview

Implement hard quota enforcement for RaaS CLI with real-time checks, contextual upgrade prompts, and webhook-driven license status synchronization.

## Phases Summary

| Phase | Title | Status | Effort |
|-------|-------|--------|--------|
| [01](#phase-01-real-time-quota-checks) | Real-time Quota Checks | pending | 2h |
| [02](#phase-02-hard-enforcement) | Hard Enforcement | pending | 2h |
| [03](#phase-03-upgrade-prompts) | Upgrade Prompts | pending | 1.5h |
| [04](#phase-04-webhook-integration) | Webhook Integration | pending | 2h |
| [05](#phase-05-testing-validation) | Testing & Validation | pending | 0.5h |

## Dependencies

- ✅ Phase 6a: License Validation (`src/lib/raas_gate.py`)
- ✅ Phase 6b: Usage Metering (`src/lib/usage_meter.py`)
- ✅ Phase 6b: Rate Limiting (`src/raas/credit_rate_limiter.py`)
- ✅ Phase 6b: Violation Tracker (`src/raas/violation_tracker.py`)
- ✅ Phase 6b: Error Messages (`src/lib/quota_error_messages.py`)
- 🔄 algo-trader Polar Webhook Integration (`apps/algo-trader/src/billing/`)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Premium Command Request                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. License Status Check (QuotaCache - 5min TTL)               │
│     • revoked? → BLOCK with support CTA                         │
│     • expired? → BLOCK with renewal CTA                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Sliding Window Rate Limit (SQLite)                          │
│     • daily limit exceeded? → BLOCK with retry_after            │
│     • monthly limit exceeded? → BLOCK with retry_after          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Daily Quota Check (PostgreSQL via UsageMeter)              │
│     • commands_count >= daily_limit? → BLOCK                    │
│     • Record usage increment                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Warning Display (if >= 80% or >= 90%)                       │
│     • Show contextual warning (once per session)                │
│     • Include upgrade CTA                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   ALLOW COMMAND │
                    └─────────────────┘
```

## Unresolved Questions

1. **Monthly quota enforcement**: Current `TIER_LIMITS` has monthly limits but `usage_meter.py` only checks daily quota. Should we add monthly quota checking to UsageMeter?
2. **Webhook cache invalidation**: When webhook syncs license status change, should we invalidate quota cache immediately or wait for 5min TTL?
3. **Grace period**: Should we allow a small buffer (e.g., 5% over quota) for users mid-command, or hard block at exactly 100%?

---

## Phase 01: Real-time Quota Checks

**Priority:** P1 | **Status:** pending | **Effort:** 2h

### Context Links

- Related: `src/lib/raas_gate.py` → `check()` method (lines 246-354)
- Related: `src/raas/quota_cache.py` → `QuotaState` with status tracking
- Related: `src/raas/credit_rate_limiter.py` → `check_limit()` method

### Overview

Add real-time quota validation before every premium command execution. Check license status, rate limits, and daily quota in sequence.

### Key Insights

- Current `check()` method already validates license + rate limit + daily quota
- Missing: Check cached license status (revoked/expired) BEFORE rate limit check
- Missing: Monthly quota check (only daily quota is enforced)

### Requirements

**Functional:**
- Check cached license status first (revoked/expired)
- Check sliding window rate limits (daily + monthly)
- Check daily quota from PostgreSQL
- Return clear error with specific violation type

**Non-functional:**
- All checks complete in < 100ms (cache hits) or < 2s (API calls)
- No external API calls for cached data (5min TTL)

### Related Code Files

**Modify:**
- `src/lib/raas_gate.py` → `check()` method - reorder checks, add monthly quota

**Read:**
- `src/raas/quota_cache.py` → `QuotaState.is_revoked()`, `is_license_expired()`
- `src/raas/credit_rate_limiter.py` → `RateLimitStatus` with monthly_used/monthly_limit

### Implementation Steps

1. **Add monthly quota check to UsageMeter**
   - Update `record_usage()` to check monthly limit before daily limit
   - Return specific error for monthly vs daily quota exceeded

2. **Reorder checks in `RaasLicenseGate.check()`**
   - Move cached license status check to top (before rate limit)
   - Add monthly quota check after rate limit

3. **Add cache refresh on quota check**
   - After successful check, refresh cache with latest usage

### Todo List

- [ ] Update `UsageMeter.record_usage()` to check monthly quota
- [ ] Reorder `RaasLicenseGate.check()` validation sequence
- [ ] Add monthly quota exceeded error context
- [ ] Update `QuotaErrorContext` to include monthly violation type

### Success Criteria

- [ ] Blocked user sees correct error (revoked vs expired vs rate limit vs quota)
- [ ] Monthly quota enforced (not just daily)
- [ ] Cached license status checked first (< 10ms)
- [ ] All error messages include specific retry_after or upgrade CTA

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| PostgreSQL down → quota check fails | High | Fallback to cache, allow if cached state valid |
| Rate limiter DB corruption | Medium | Catch exception, fallback to daily quota only |
| Cache serves stale revoked status | Medium | 5min TTL acceptable, webhook can invalidate |

### Security Considerations

- Never bypass quota checks even on errors (fail closed, not open)
- Log all quota exceeded events to `violation_events` table
- Sanitize error messages (no SQL/stack traces)

### Next Steps

→ Proceed to Phase 02: Hard Enforcement

---

## Phase 02: Hard Enforcement

**Priority:** P1 | **Status:** pending | **Effort:** 2h

### Context Links

- Related: `src/main.py` → `_validate_startup_license()` (lines 67-106)
- Related: `src/lib/raas_gate.py` → `require_license()` function (lines 390-397)
- Related: `src/raas/violation_tracker.py` → `ViolationEvent` recording

### Overview

Block command execution when quota exceeded or license invalid. Ensure no bypass paths exist.

### Key Insights

- Current enforcement in `check()` method returns `(False, error)` but may not block all paths
- `main.py` has separate validation flow that might bypass `check()`
- Need to verify all premium command entry points call `check()`

### Requirements

**Functional:**
- Block ALL premium commands when quota exceeded
- Block ALL premium commands when license revoked/expired
- Show clear error with upgrade/renewal CTA
- Record violation to analytics

**Non-functional:**
- Exit code 1 on blocked command
- No partial execution (check before any side effects)

### Related Code Files

**Modify:**
- `src/main.py` → Ensure `_validate_startup_license()` uses `check()` method
- `src/lib/raas_gate.py` → `require_license()` - ensure it calls `check()` with proper error handling

**Audit:**
- All commands in `src/commands/` - verify they call `require_license()` or `check_license()`

### Implementation Steps

1. **Audit command entry points**
   - List all premium commands from `src/commands/`
   - Verify each calls `require_license()` or `check()`

2. **Unify validation flow**
   - Remove duplicate validation logic
   - All premium commands use single `require_license()` wrapper

3. **Add pre-execution hook**
   - Use Typer callback to validate before command runs
   - Prevents any code execution if blocked

### Todo List

- [ ] Audit all premium command entry points
- [ ] Add Typer pre-execution license check
- [ ] Remove duplicate validation logic
- [ ] Verify violation recording on block

### Success Criteria

- [ ] Zero bypass paths to premium commands
- [ ] Blocked commands exit with code 1
- [ ] Error message displayed before exit
- [ ] Violation recorded for analytics

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Command bypasses license check | High | Add Typer callback at app level |
| Violation recording fails silently | Low | Fire-and-forget with try/except |
| User modifies code to bypass | Medium | Server-side enforcement (gateway) |

### Security Considerations

- Client-side enforcement is advisory only - always verify server-side
- Log all blocked attempts with IP, timestamp, command
- Rate limit repeated blocked attempts (prevent brute force)

### Next Steps

→ Proceed to Phase 03: Upgrade Prompts

---

## Phase 03: Upgrade Prompts

**Priority:** P2 | **Status:** pending | **Effort:** 1.5h

### Context Links

- Related: `src/lib/quota_error_messages.py` → Upgrade prompt templates
- Related: `src/lib/quota_error_messages.py` → `get_upgrade_url()`, `get_renewal_url()`

### Overview

Display contextual upgrade messages when quota exceeded or license expired. Deep-link to pricing/renewal pages.

### Key Insights

- Templates exist in `quota_error_messages.py` but may not include user context
- Current URLs are generic (`/pricing`) - should deep-link with email/tier
- Free tier prompt differs from paid tier upgrade prompt

### Requirements

**Functional:**
- Free tier: Show upgrade to Pro ($29/mo, 1000 commands/day)
- Pro tier: Show upgrade to Enterprise (unlimited)
- Expired license: Show renewal flow with expiry date
- Revoked license: Show support contact (no upgrade link)

**Non-functional:**
- URLs include user context (key_id, tier, email) for deep linking
- Prompts match tier-specific pricing
- Rich console formatting (colored boxes)

### Related Code Files

**Modify:**
- `src/lib/quota_error_messages.py` → `get_renewal_url()` - already supports key_id, tier, email
- `src/lib/quota_error_messages.py` → `format_license_expired_with_renewal()` - already exists
- `src/lib/raas_gate.py` → Pass user context to error formatters

### Implementation Steps

1. **Add user context capture**
   - Extract email from license info or user profile
   - Pass to error formatter functions

2. **Update upgrade prompts**
   - Include specific pricing based on current tier
   - Add deep-linked URLs with user context

3. **Add renewal flow for expired licenses**
   - Use `format_license_expired_with_renewal()` with deep link
   - Pre-fill renewal form with key_id, tier, email

### Todo List

- [ ] Extract user email from license/user profile
- [ ] Update free→pro upgrade prompt with pricing
- [ ] Update pro→enterprise upgrade prompt
- [ ] Add renewal deep-link for expired licenses

### Success Criteria

- [ ] Free users see Pro upgrade ($29/mo, 1000/day)
- [ ] Pro users see Enterprise upgrade (unlimited)
- [ ] Expired users see renewal link with pre-filled form
- [ ] Revoked users see support contact (no upgrade)

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Email not available for deep-link | Low | Fallback to generic URL |
| Pricing outdated in templates | Medium | Use environment variables for pricing |
| Broken deep-link URLs | Low | Test all URL combinations |

### Security Considerations

- Don't expose email in error messages (only in URL params)
- Use HTTPS for all upgrade/renewal URLs
- Sanitize URL params (no XSS via query strings)

### Next Steps

→ Proceed to Phase 04: Webhook Integration

---

## Phase 04: Webhook Integration

**Priority:** P1 | **Status:** pending | **Effort:** 2h

### Context Links

- Related: `apps/algo-trader/src/billing/polar-webhook-event-handler.ts` → `handleCancellation()`, `handleRefundCreated()`
- Related: `src/raas/quota_cache.py` → `invalidate()` method

### Overview

Ensure enforcement respects license license status synced from Stripe/Polar webhooks. Handle tier changes, revocations, expirations.

### Key Insights

- Webhook handler already calls `license_service.deactivate_subscription()` on cancellation
- Missing: Invalidate quota cache when license status changes
- Missing: Sync license status to Python CLI (currently TS-only)

### Requirements

**Functional:**
- Webhook updates license status in PostgreSQL
- Webhook invalidates quota cache (force refresh)
- CLI sees updated status within 5min (cache TTL)
- Handle: subscription.canceled, subscription.revoked, refund.created

**Non-functional:**
- Idempotent webhook processing (handle duplicates)
- Audit log all webhook events

### Related Code Files

**Modify:**
- `apps/algo-trader/src/billing/polar-webhook-event-handler.ts` → Add cache invalidation
- `src/lib/raas_gate.py` → `validate_remote()` - already checks status from remote API

**Read:**
- `apps/algo-trader/src/billing/polar-subscription-service.ts` → `deactivate_subscription()`

### Implementation Steps

1. **Add cache invalidation to webhook handler**
   - When license deactivated, call Python cache invalidation
   - Or: Set cache TTL to 0 to force immediate refresh

2. **Add license status sync to CLI**
   - Ensure `validate_remote()` receives status from webhook-updated DB
   - Update `QuotaState` with latest status

3. **Test webhook scenarios**
   - subscription.canceled → license revoked
   - subscription.revoked → license revoked
   - refund.created → license revoked
   - subscription.updated → tier change

### Todo List

- [ ] Add cache invalidation on webhook deactivation
- [ ] Verify status sync from webhook to CLI
- [ ] Add audit logging for webhook events
- [ ] Test all webhook scenarios

### Success Criteria

- [ ] Webhook deactivation → CLI sees revoked within 5min
- [ ] Tier upgrade → CLI sees new limits immediately
- [ ] Audit log shows all webhook events
- [ ] Idempotent processing (duplicate webhooks ignored)

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|------------|
| Webhook fails to invalidate cache | Medium | User manually runs `mekong license refresh` |
| Duplicate webhook processing | Low | Idempotency key check already exists |
| Webhook signature validation fails | High | Log error, alert on failure threshold |

### Security Considerations

- Always verify webhook signature (HMAC-SHA256)
- Log all webhook events with full payload
- Alert on unusual patterns (mass cancellations)

### Next Steps

→ Proceed to Phase 05: Testing & Validation

---

## Phase 05: Testing & Validation

**Priority:** P1 | **Status:** pending | **Effort:** 0.5h

### Context Links

- Related: `tests/test_quota_cache.py`
- Related: `tests/test_violation_tracker.py`
- Related: `tests/test_license_enforcement.py`

### Test Scenarios

| Test | Description | Expected Result |
|------|-------------|-----------------|
| T1 | Free tier exceeds 10 commands/day | Blocked with upgrade prompt |
| T2 | Pro tier exceeds 1000 commands/day | Blocked with upgrade to Enterprise |
| T3 | Rate limit exceeded (100 requests/min) | Blocked with retry_after |
| T4 | License revoked via webhook | Blocked with support CTA |
| T5 | License expired | Blocked with renewal link |
| T6 | Monthly quota exceeded | Blocked with retry_after |
| T7 | Cached revoked status (5min TTL) | Blocked within TTL window |
| T8 | Webhook invalidates cache | Status updated immediately |
| T9 | Violation recorded on block | Entry in violation_events |
| T10 | Upgrade URL deep-linked | URL contains key_id, tier, email |

### Testing Checklist

- [ ] All 10 test scenarios pass
- [ ] No bypass paths to premium commands
- [ ] Error messages match templates
- [ ] Violations recorded in database
- [ ] Webhook integration tested end-to-end

### Unresolved Questions

1. Monthly quota: Should UsageMeter enforce monthly limits or only daily?
2. Cache invalidation: Immediate or wait for 5min TTL?
3. Grace period: Allow 5% over-quota buffer?

---

## References

- ROIaaS Constitution: `docs/HIEN_PHAP_ROIAAS.md`
- Binh Pháp Master Strategy: `docs/BINH_PHAP_MASTER.md`
- Polar Webhook Docs: https://docs.polar.sh/webhooks
- Phase 6a PRD: `plans/reports/` (if exists)

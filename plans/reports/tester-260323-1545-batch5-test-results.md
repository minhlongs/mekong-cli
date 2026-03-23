# Test Results — Batch 5
**Date:** 2026-03-23
**Scope:** `packages/mekong-cli-core` + `apps/raas-gateway`

---

## Summary

| Target | Test Files | Tests | Passed | Failed | Skipped | Duration |
|--------|-----------|-------|--------|--------|---------|----------|
| mekong-cli-core | 54 / 54 | 1,190 | 1,190 | 0 | 0 | 2.65s |
| raas-gateway | 55 / 56 | 1,405 | 1,403 | 2 | 3 | 8.99s |
| **Total** | **109 / 110** | **2,595** | **2,593** | **2** | **3** | **~12s** |

---

## Gateway tsc: PASS

```
cd apps/raas-gateway && npx tsc --noEmit → ok (no errors)
```

---

## CLI Core Tests: 1,190 / 1,190 PASS

All 4 new openclaw command test files pass:
- `openclaw-benchmark.test.ts` — 15 tests, all pass
- `openclaw-cost.test.ts` — 15 tests, all pass
- `openclaw-health.test.ts` — 18 tests, all pass
- `openclaw-mission.test.ts` — 18 tests, all pass

---

## raas-gateway Tests: 2 FAILED

**File:** `tests/billing-service.test.ts`

### Failure 1 — `POLAR_PRODUCT_CREDITS > should have correct credit mappings`

```
AssertionError: expected { credits: 200, tier: 'starter' } to deeply equal { credits: 50, tier: 'pro' }
```

Test expects key `agencyos-starter` → `{ credits: 50, tier: 'pro' }`.
Actual impl has key `starter` → `{ credits: 200, tier: 'starter' }`.

### Failure 2 — `getProductCredits > should return credits for known product`

```
AssertionError: expected { credits: 1000, tier: 'pro' } to deeply equal { credits: 200, tier: 'pro' }
```

Test calls `getProductCredits('AgencyOS Pro')` → normalizes to key `agencyos-pro`.
Actual impl key is `pro` → `{ credits: 1000, tier: 'pro' }`.

**Root cause:** The test was written expecting `agencyos-*` prefixed keys and old credit values (`50 starter / 200 pro`), but `billing-service.ts` was updated to use short keys (`starter`, `pro`) and new credit values (`200 starter / 1000 pro`) matching the actual Polar pricing tiers. Test was NOT updated to match.

---

## Issues Found

1. **billing-service.test.ts is stale** — written against old product key schema (`agencyos-starter`, `agencyos-pro`, `agencyos-agency`, `agencyos-master`) with old credit allocations. Actual service now uses `starter`/`pro`/`agency`/`enterprise` keys with updated credit amounts. Test assertions on lines 79-84 and 89-90 need to be updated to match current `POLAR_PRODUCT_CREDITS` map.

2. **Minor:** Several `stdout` log lines like `[missionExecutionMetricsService.recordMetric] Error: Metric insert failed` appear during test runs — these are expected error-path logs from mock DB rejections in e2e tests, not actual failures.

---

## Recommendations

- **Fix (not done — report only):** Update `tests/billing-service.test.ts` lines 79-84 to use current keys (`starter`, `pro`, `agency`, `enterprise`) and current credit values (`200`, `1000`, `1000`, `-1`). Update line 89-90 to call `getProductCredits('Pro')` (not `'AgencyOS Pro'`) and expect `{ credits: 1000, tier: 'pro' }`.

---

## Unresolved Questions

- Were the `agencyos-*` prefixed keys intentionally removed from `POLAR_PRODUCT_CREDITS`, or is this a regression from a recent refactor? The git note `fix: unify RaaS pricing across landing + dashboard` (commit `ed2e5711f`) is likely the source — test was not updated alongside that fix.

# Code Quality Audit Report

**Date:** 2026-03-22
**Project:** mekong-cli
**Scope:** packages/ directory

---

## Executive Summary

| Metric | Count | Status |
|--------|-------|--------|
| TODO/FIXME comments | 11 (non-node_modules) | ⚠️ Needs attention |
| console.log/warn/error | 65+ | ❌ High |
| @ts-ignore / :any | 70+ | ❌ High |
| Build status | ✅ Pass | ✅ Green |
| Lint status | ❌ Failed (@mekong/build-optimizer) | ❌ Red |

---

## 1. TODO/FIXME Comments (11 items)

### Critical
- `packages/mekong-engine/src/index.test.ts:2` - Placeholder test (TODO: Add real tests)
- `packages/ui/src/index.test.ts:2` - Placeholder test (TODO: Add real tests)
- `packages/cli-orchestrator/src/index.test.ts:2` - Placeholder test (TODO: Add real tests)
- `packages/openclaw-agents/src/index.test.ts:2` - Placeholder test (TODO: Add real tests)

### Medium
- `packages/mekong-engine/src/routes/onboarding.ts:377` - TODO: Send email via Resend/SendGrid/SES
- `packages/tooling/vibe-dev/scripts/test-sync-up.ts:24` - OPT_TODO status mapping

### Low (Documentation/Reference)
- `packages/core/perception/src/dashboard.ts:69` - Comment about TODOs in health check
- `packages/core/perception/src/health-monitor.ts:131` - Grep pattern for TODO|FIXME

---

## 2. console.log Statements (65+ occurrences)

### Production Code (Should Remove)
| File | Line | Type | Context |
|------|------|------|---------|
| `mekong-engine/src/security/audit-log.ts` | 80 | error | Audit log write failed |
| `mekong-engine/src/observability/metrics.ts` | 160 | error | Structured logging |
| `mekong-engine/src/observability/alerts.ts` | 289,293,296 | error/log | Slack webhook |
| `mekong-engine/src/lib/monitoring.ts` | 20,29,38 | error/warn/log | Structured logger wrapper |
| `mekong-engine/src/routes/onboarding.ts` | 379 | log | Verification email |
| `ui/i18n/scripts/extract.ts` | 6 | all | Logger utility |
| `ui/i18n/scripts/validate.ts` | 5 | all | Logger utility |

### CLI/Dev Tools (Acceptable)
- `tooling/vibe-analytics/` - CLI output (acceptable)
- `tooling/vibe-dev/scripts/` - Test scripts (acceptable)

---

## 3. TypeScript Any Types & @ts-ignore (70+ occurrences)

### Test Files (Acceptable for mocks)
- `mekong-engine/test/rate-limit-middleware.test.ts` - 7 `any` types (test mocks)
- `mekong-engine/test/license-middleware.test.ts` - 6 `any` types (test mocks)

### Production Code (Should Fix)
| File | Line | Issue |
|------|------|-------|
| `mekong-engine/src/security/audit-log.ts` | 146 | `row: any` |
| `mekong-engine/src/observability/metrics.ts` | 302 | `c: any` |
| `mekong-engine/src/observability/alerts.ts` | 323 | `c: any` |
| `tooling/vibe-dev/src/lib/*` | Multiple | Various `any` types |

### node_modules (Ignore)
- 60+ occurrences in `observability/node_modules/` - **Ignore**

---

## 4. Build Status

```
✅ Build: SUCCESS
- 67 packages
- 5 successful (core packages)
- Cached: 4
- Time: 2.292s
```

---

## 5. Lint Status

```
❌ Lint: FAILED
Failed: @mekong/build-optimizer#lint
Error: No files matching the pattern "src/" were found
```

**Root cause:** `packages/build-optimizer/package.json` lint script references non-existent `src/` directory.

---

## Recommendations

### Priority 1 (Critical - Fix Immediately)
1. Fix `@mekong/build-optimizer` lint script
2. Remove console.log from production code in `mekong-engine/src/`
3. Replace `any` types in middleware handlers

### Priority 2 (High - This Sprint)
1. Add real tests to placeholder test files
2. Implement email sending in onboarding route
3. Add proper types to audit-log.ts and observability files

### Priority 3 (Medium - Next Sprint)
1. Remove console.log from i18n scripts or keep as dev utility
2. Document TODO comments with ticket references
3. Set up ESLint to flag `any` types

---

## Unresolved Questions

1. Should `tooling/vibe-dev` scripts keep console.log for debugging?
2. Is `mekong-engine` intended for production or still in development?
3. What is the target test coverage percentage?

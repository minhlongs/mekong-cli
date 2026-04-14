# Monorepo Health Check Report

**Date:** 2026-03-19
**Scope:** Root + 46 packages
**Command:** `pnpm audit`, `pnpm build`, tech debt scan

---

## Executive Summary

| Check | Status | Count |
|-------|--------|-------|
| Security Vulnerabilities | ⚠️ Moderate | 3 |
| Build Status | ✅ PASS | 46/46 tasks |
| Console Statements | ⚠️ Warning | 28 |
| TODO/FIXME Comments | ⚠️ Warning | 8 |
| `any` Types | ❌ Critical | 30+ |

---

## 1. Security Audit (npm audit)

**Severity:** 3 Moderate vulnerabilities

### Vulnerability #1: esbuild (Moderate)
- **Issue:** Development server allows cross-origin requests
- **Package:** `esbuild@0.24.2`
- **Patched:** `>=0.25.0`
- **Paths:** 142 dependency paths via `vite > esbuild`
- **Impact:** Development only, not production
- **Fix:** `pnpm up esbuild@latest`

### Vulnerability #2: ajv (Moderate)
- **Issue:** ReDoS when using `$data` option
- **Package:** `ajv@6.12.6`
- **Patched:** `>=6.14.0`
- **Paths:** 21 paths via `eslint > ajv`
- **Impact:** ESLint validation edge case
- **Fix:** Update `@typescript-eslint/parser` or `eslint`

### Vulnerability #3: hono (Moderate)
- **Issue:** Prototype Pollution via `parseBody({ dot: true })`
- **Package:** `hono@4.12.6`
- **Patched:** `>=4.12.7`
- **Paths:** 3 direct dependencies
  - `apps/algo-trader > @hono/node-server > hono`
  - `apps/algo-trader > hono`
  - `packages/mekong-engine > hono`
- **Impact:** Potential security issue in API handling
- **Fix:** `pnpm up hono@latest` (URGENT)

---

## 2. Build Status

**Result:** ✅ **FULL TURBO** - 46 tasks successful

```
Tasks:    46 successful, 46 total
Cached:   46 cached, 46 total
Time:     103ms >>> FULL TURBO
```

All packages build successfully with no errors.

**Note:** Build warnings about large chunks (>500KB):
- `pdf-engine.DjqSkgtA.js` (853.84 KB)
- `pdf-components.BmvXUsYH.js` (757.52 KB)
- `feature-commission.DlBrC7Ry.js` (538.45 KB)
- `charts.BWYPlVyf.js` (448.52 KB)
- `index.BVOAD67q.js` (391.54 KB)

Recommendation: Review code splitting for these modules.

---

## 3. Tech Debt Scan

### 3.1 Console Statements (28 occurrences)

**Files with console statements:**

| File | Count | Type |
|------|-------|------|
| `packages/tooling/vibe-analytics/src/devops/cli/metrics-command.ts` | 12 | CLI output (acceptable) |
| `packages/tooling/vibe-dev/scripts/test-*.ts` | 8 | Test scripts (acceptable) |
| `packages/tooling/vibe-dev/src/cli.ts` | 1 | Error handling |
| `packages/tooling/vibe-dev/src/lib/github-client.ts` | 2 | Error logging |
| `packages/ui/i18n/scripts/*.ts` | 2 | I18n tooling |
| `packages/mekong-engine/src/types/error.ts` | 3 | Error boundaries |

**Assessment:** Most console statements are in CLI tools and test scripts (acceptable). The 3 in `error.ts` should use proper logging service instead.

### 3.2 TODO/FIXME Comments (8 occurrences)

| File | Context |
|------|---------|
| `packages/core/perception/src/health-monitor.ts` | Health check logic |
| `packages/agi-evolution/src/self-improver.ts` | Self-improvement tracking |
| `packages/mekong-cli-core/src/cli/commands/agi.ts` | AGI commands |
| `packages/tooling/vibe-dev/scripts/test-sync-up.ts` | Test scenarios |

**Assessment:** Low count, mostly in meta-programming/tooling code. Not critical.

### 3.3 `any` Types (30+ occurrences) ❌ CRITICAL

**Hotspots:**

| File | Count | Severity |
|------|-------|----------|
| `packages/mekong-engine/src/routes/equity.ts` | 8 | ❌ Critical |
| `packages/mekong-engine/src/routes/funding.ts` | 9 | ❌ Critical |
| `packages/mekong-engine/src/routes/crm.ts` | 1 | ⚠️ Moderate |
| `packages/tooling/vibe-analytics/src/devops/cli/metrics-command.ts` | 1 | ⚠️ Moderate |
| `packages/tooling/vibe-analytics/src/devops/client/github-client.ts` | 2 | ⚠️ Moderate |
| `packages/tooling/vibe-dev/scripts/*.ts` | 6 | ⚠️ Test files |
| `packages/tooling/vibe-dev/src/cli.ts` | 1 | ⚠️ Moderate |
| `packages/tooling/vibe-dev/src/lib/github-client.ts` | 2 | ⚠️ Moderate |

**Total:** ~30 occurrences in production code

**Impact:** Type safety compromised in critical routes (equity, funding, CRM)

**Recommendation:** Prioritize fixing `mekong-engine` routes as they handle financial/legal data.

---

## 4. Priority Actions

### 🔴 Critical (Fix This Week)

1. **Update `hono` to 4.12.7+** - Security vulnerability in API handling
   ```bash
   pnpm up hono@latest
   ```

2. **Fix `any` types in `mekong-engine/src/routes/equity.ts`** - Financial data handling
3. **Fix `any` types in `mekong-engine/src/routes/funding.ts`** - Investment data

### 🟡 Moderate (Next Sprint)

4. Update `esbuild` to 0.25.0+ (dev dependency)
5. Replace console statements in `error.ts` with proper logging
6. Add explicit types to `crm.ts` route responses

### 🟢 Low (Backlog)

7. Address large chunk warnings in build output
8. Update `ajv` via ESLint dependency chain
9. Clean up test script `any` types

---

## 5. Overall Health Score

| Category | Score | Status |
|----------|-------|--------|
| Security | 7/10 | ⚠️ 3 moderate vulnerabilities |
| Build | 10/10 | ✅ All packages build |
| Type Safety | 5/10 | ❌ 30+ `any` types |
| Code Quality | 8/10 | ✅ Low TODO/FIXME count |
| Performance | 7/10 | ⚠️ Large chunk warnings |

**Total: 37/50 (74%) - Production Ready with Technical Debt**

---

## Next Steps

1. Run `pnpm audit --fix` to auto-fix vulnerabilities
2. Create task to fix `any` types in `mekong-engine` routes
3. Review code splitting configuration for large chunks

---

_Report generated by health check automation_

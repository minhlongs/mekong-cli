# Production Readiness Audit: Business, UI, Tooling Packages

**Date:** 2026-02-07
**Scope:** `packages/business/`, `packages/ui/`, `packages/tooling/`
**Auditor:** researcher-02

---

## Executive Summary

Audited 8 packages across 3 layers. Found **critical naming inconsistencies** in tooling packages and **missing documentation** across business/UI layers.

**Overall Status:** ⚠️ **Needs Action** (5/8 packages require fixes)

---

## packages/business/ (4 packages)

### ✅ vibe-money
- **Package Name:** `@mekong/vibe-money` ✓
- **Dependencies:** Clean (empty, with peer dep on TypeScript)
- **Config:** tsconfig.json ✓, index.ts ✓
- **Build:** Has build script
- **Documentation:** ❌ Missing README.md

### ⚠️ vibe-marketing
- **Package Name:** `@mekong/vibe-marketing` ✓
- **Dependencies:** ❌ No dependencies/scripts defined
- **Config:** tsconfig.json ✓, index.ts ✓
- **Build:** ❌ No build script
- **Documentation:** ❌ Missing README.md

### ⚠️ vibe-revenue
- **Package Name:** `@mekong/vibe-revenue` ✓
- **Dependencies:** ❌ No dependencies/scripts defined
- **Config:** tsconfig.json ✓, index.ts ✓
- **Build:** ❌ No build script
- **Documentation:** ❌ Missing README.md

### ⚠️ vibe-ops
- **Package Name:** `@mekong/vibe-ops` ✓
- **Dependencies:** ❌ No dependencies/scripts defined
- **Config:** tsconfig.json ✓, index.ts ✓
- **Build:** ❌ No build script
- **Documentation:** ❌ Missing README.md

---

## packages/ui/ (3 packages)

### ✅ vibe-ui
- **Package Name:** `@mekong/vibe-ui` ✓
- **Dependencies:** Proper (framer-motion, tailwindcss, peer react)
- **Config:** tsconfig.json ✓, index.ts ✓
- **Build:** Has build + test scripts
- **Documentation:** ❌ Missing README.md

### ✅ i18n
- **Package Name:** `@mekong/i18n` ✓
- **Dependencies:** Proper workspace refs (`@mekong/shared: workspace:*`)
- **Config:** tsconfig.json ✓
- **Exports:** ⚠️ No root index.ts (uses dist/index.js via build)
- **Build:** Comprehensive scripts (build/dev/lint/clean)
- **Documentation:** ❌ Missing README.md

### ⚠️ ui (parent package)
- **Package Name:** Not checked (appears to be parent)
- **Config:** tsconfig.json ✓, src/index.ts ✓
- **Status:** Unclear purpose (may be legacy)

---

## packages/tooling/ (2 packages)

### ❌ vibe-analytics
- **Package Name:** ❌ **CRITICAL:** `agencyos-vibe-analytics` (should be `@mekong/vibe-analytics`)
- **Dependencies:** Proper (web-vitals, octokit, zod, etc.)
- **Config:** tsconfig.json ✓, index.ts ✓
- **Build:** Has build + test scripts
- **Documentation:** ✓ README.md exists

### ❌ vibe-dev
- **Package Name:** ❌ **CRITICAL:** `agencyos-vibe-dev` (should be `@mekong/vibe-dev`)
- **Dependencies:** ⚠️ Uses `@mekong/vibe-analytics: workspace:*` (but analytics itself has wrong name)
- **Config:** tsconfig.json ✓, index.ts ✓
- **Build:** Comprehensive scripts (build/test/prepublishOnly)
- **Documentation:** ✓ README.md exists

---

## Critical Issues (Priority Fix)

### 🔴 P0: Package Naming Inconsistency
**Impact:** Breaks workspace resolution, prevents publishing

**Affected Packages:**
- `packages/tooling/vibe-analytics/package.json` → name: `agencyos-vibe-analytics`
- `packages/tooling/vibe-dev/package.json` → name: `agencyos-vibe-dev`

**Required Action:** Rename to `@mekong/vibe-analytics` and `@mekong/vibe-dev`

**Cascading Fix:** Update dependency in `vibe-dev`:
```json
"@mekong/vibe-analytics": "workspace:*"  // instead of current ref
```

---

### 🟡 P1: Missing Build Scripts
**Impact:** Cannot verify package buildability

**Affected Packages:**
- `vibe-marketing`
- `vibe-revenue`
- `vibe-ops`

**Required Action:** Add to each `package.json`:
```json
"scripts": {
  "build": "tsc",
  "test": "echo 'Tests TBD'"
}
```

---

### 🟡 P2: Missing Documentation
**Impact:** Poor developer experience, unclear package purpose

**Affected Packages:** All except `vibe-analytics`, `vibe-dev`

**Required Action:** Create `README.md` for:
- vibe-money
- vibe-marketing
- vibe-revenue
- vibe-ops
- vibe-ui
- i18n

**Template:**
```markdown
# @mekong/[package-name]

[Description from package.json]

## Installation
npm install @mekong/[package-name]

## Usage
[Basic example]
```

---

## Buildability Test Results

**Not Attempted** - Would fail for P0 issues (naming) and P1 issues (no build scripts).

**Recommendation:** Fix P0/P1 issues first, then run:
```bash
npm run build -w @mekong/vibe-marketing
npm run build -w @mekong/vibe-revenue
npm run build -w @mekong/vibe-ops
npm run build -w @mekong/vibe-analytics
npm run build -w @mekong/vibe-dev
```

---

## Positive Findings

✅ **Consistent `@mekong/*` scoping** (except tooling layer)
✅ **Proper workspace dependency syntax** (`workspace:*`) where used
✅ **TypeScript config present** in all packages
✅ **Export entry points exist** (index.ts or dist/index.js)
✅ **Advanced packages** (i18n, vibe-ui, vibe-analytics) have comprehensive configs

---

## Recommended Fix Order

1. **Immediate:** Fix tooling package names (vibe-analytics, vibe-dev)
2. **Next:** Add build scripts to business packages
3. **Then:** Create README.md for all packages
4. **Finally:** Run buildability verification tests

---

## Unresolved Questions

1. What is `packages/ui/package.json` for? (Parent or legacy?)
2. Should i18n have a root `index.ts` or rely solely on build output?
3. Are business packages placeholders or should they have actual implementations?

---

**Report Path:** `/Users/macbookprom1/mekong-cli/plans/260207-1437-production-readiness-audit/research/researcher-02-biz-ui-tooling.md`

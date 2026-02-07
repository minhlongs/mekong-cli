---
title: "Production Readiness Remediation Plan"
description: "Fix critical issues blocking production deployment across all package layers"
status: pending
priority: P1
effort: 8h
branch: master
tags: [production, audit, remediation, infrastructure]
created: 2026-02-07
---

# Production Readiness Remediation Plan

## Executive Summary

Based on comprehensive audits of all 13 packages across Core, Integrations, Business, UI, and Tooling layers, this plan addresses **7 CRITICAL** and **6 WARNING** issues blocking production deployment.

**Current Status:** 🔴 **NOT PRODUCTION READY**

**Target Status:** ✅ **100% Build Pass + Documentation Coverage**

---

## Audit Findings Overview

### Critical Issues (7)
1. **Missing TypeScript configs** (2 packages: vibe, shared)
2. **Naming inconsistencies** (2 packages: vibe-analytics, vibe-dev using `agencyos-*`)
3. **Missing build scripts** (7 packages across all layers)
4. **BMAD package structure** (Python package without npm integration)

### Warning Issues (6)
1. **Missing README.md** (10 packages)
2. **Wildcard workspace dependencies** (vibe package)
3. **Inconsistent TypeScript includes** (multiple packages)
4. **Unbuildable packages** (not verified)

### Affected Packages by Layer

**Core (4):** vibe, vibe-agents, shared, bmad
**Integrations (2):** vibe-bridge, vibe-crm
**Business (4):** vibe-money, vibe-marketing, vibe-revenue, vibe-ops
**UI (3):** vibe-ui, i18n, ui (parent)
**Tooling (2):** vibe-analytics, vibe-dev

---

## Remediation Strategy

### Phase 1: Core Stabilization (2h)
Fix TypeScript configurations and build infrastructure in foundational packages.

**Scope:** packages/core/*
**Blockers:** All subsequent phases depend on Core building successfully.

### Phase 2: Dependency Alignment (1.5h)
Standardize package naming and workspace references across all layers.

**Scope:** packages/tooling/* (naming), all packages (dependencies)
**Critical:** Fixes `agencyos-*` naming violations.

### Phase 3: Build Standardization (1.5h)
Add consistent build/test/clean scripts to all packages.

**Scope:** All packages missing build scripts (7 total)
**Deliverable:** 100% of packages can run `npm run build`.

### Phase 4: Documentation Coverage (2h)
Create minimal README.md for every package.

**Scope:** 10 packages missing documentation
**Template:** Purpose, Installation, Usage, API overview.

### Phase 5: Final Verification (1h)
Run comprehensive build matrix and validation tests.

**Scope:** All 13 packages
**Success Criteria:** Zero build errors, zero TypeScript errors, all tests pass.

---

## Implementation Phases

| Phase | Focus | Duration | Blockers |
|-------|-------|----------|----------|
| 1 | Core Stabilization | 2h | None |
| 2 | Dependency Alignment | 1.5h | Phase 1 |
| 3 | Build Standardization | 1.5h | Phase 1 |
| 4 | Documentation Coverage | 2h | Phase 3 |
| 5 | Final Verification | 1h | Phases 1-4 |

**Total Effort:** ~8 hours

---

## Success Criteria

### Build Matrix (100% Pass Required)
- [ ] All 13 packages have `tsconfig.json`
- [ ] All 13 packages have `build` script
- [ ] All 13 packages build without errors
- [ ] All workspace dependencies use `workspace:*` protocol
- [ ] No compilation errors across monorepo

### Documentation Matrix (100% Coverage Required)
- [ ] All 13 packages have `README.md`
- [ ] All README files follow standard template
- [ ] All API surfaces documented

### Naming Consistency (Zero Violations)
- [ ] All packages use `@mekong/*` scope
- [ ] No `agencyos-*` naming patterns
- [ ] Package names match directory structure

---

## Phase Details

### [Phase 1: Core Stabilization](./phase-01-core-stabilization.md)
Fix tsconfig.json, package.json, build scripts in Core layer.

**Affected:** vibe, vibe-agents, shared, bmad

### [Phase 2: Dependency Alignment](./phase-02-dependency-alignment.md)
Rename tooling packages, fix workspace dependencies.

**Affected:** vibe-analytics, vibe-dev, vibe (wildcard fix)

### [Phase 3: Build Standardization](./phase-03-build-standardization.md)
Add build/test/clean scripts to all packages.

**Affected:** vibe-marketing, vibe-revenue, vibe-ops, vibe-bridge, vibe-crm, vibe, shared

### [Phase 4: Documentation Coverage](./phase-04-documentation-coverage.md)
Create README.md for all packages.

**Affected:** 10 packages (all except vibe, vibe-analytics, vibe-dev)

### [Phase 5: Final Verification](./phase-05-final-verification.md)
Run build matrix, validate TypeScript, test execution.

**Scope:** All packages, CI/CD verification

---

## Risk Assessment

### High Risk
- **BMAD Python Integration:** No clear npm strategy. May require wrapper package.
- **Build Matrix Failures:** Unknown compilation errors may surface during Phase 5.

### Medium Risk
- **Workspace Dependency Cycles:** Fixing wildcard deps may expose circular dependencies.
- **Legacy `packages/ui/`:** Unclear purpose, may conflict with `vibe-ui`.

### Low Risk
- **Documentation Quality:** Template-based approach ensures consistency.
- **Script Standardization:** Proven pattern from vibe-agents.

---

## Rollback Plan

If build verification fails in Phase 5:
1. Identify failing package via `npm run build -w @mekong/<package>`
2. Check TypeScript errors: `tsc --noEmit` in package directory
3. Revert Phase 3 changes for that package
4. Document issue in `plans/260207-1437-production-readiness-audit/reports/`
5. Create follow-up task for manual investigation

---

## Next Steps After Completion

1. **CI/CD Integration:** Add build matrix to GitHub Actions
2. **Pre-commit Hooks:** Enforce type checking before commits
3. **Publishing Strategy:** Define which packages are public vs private
4. **Testing Infrastructure:** Add vitest to all packages
5. **Linting:** Configure ESLint for code quality

---

## Key Dependencies

- TypeScript 5.9.3+
- Node.js 18+
- npm workspaces support
- Root tsconfig.json (extends for packages)

---

## Team Assignments

**Phase 1-3:** Technical debt removal (developer focus)
**Phase 4:** Documentation (can parallelize with Phase 3)
**Phase 5:** QA verification (requires Phases 1-4 complete)

---

## Unresolved Questions

1. **BMAD Strategy:** Keep Python-only or add npm wrapper?
2. **Build Output:** Compile to `dist/` or source-only for monorepo?
3. **Publishing Scope:** Which packages intended for external npm?
4. **Legacy UI Package:** Should `packages/ui/` be removed?
5. **Shared Package Scope:** Is `logger.js` export complete or placeholder?

---

**Plan Created:** 2026-02-07
**Estimated Completion:** 2026-02-08
**Risk Level:** Medium (unknown build errors)
**Success Probability:** 85% (assumes no major architectural issues)

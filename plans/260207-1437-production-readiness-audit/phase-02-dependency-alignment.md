# Phase 02: Dependency Alignment

**Priority:** P0 (Critical)
**Status:** Pending
**Estimated Duration:** 1.5 hours
**Depends On:** Phase 1 (Core Stabilization)

---

## Context Links

- **Audit Report:** `research/researcher-02-biz-ui-tooling.md`
- **Naming Violations:** `packages/tooling/vibe-analytics/`, `packages/tooling/vibe-dev/`
- **Workspace Protocol:** npm workspaces documentation

---

## Overview

Fix critical package naming inconsistencies in tooling layer and standardize all workspace dependency references across the monorepo.

**Critical Issues:**
- 2 packages use `agencyos-*` naming instead of `@mekong/*`
- Cascading dependency breaks (vibe-dev depends on misnamed vibe-analytics)
- Inconsistent workspace protocol usage

---

## Key Insights

1. **Tooling packages violate naming convention:** Only layer with `agencyos-*` prefix
2. **Breaks workspace resolution:** npm workspaces can't find misnamed packages
3. **Prevents publishing:** npm registry rejects non-scoped names in monorepo
4. **Cascading fix required:** vibe-dev references vibe-analytics by wrong name

---

## Requirements

### Functional Requirements
- All packages must use `@mekong/*` scope
- All workspace dependencies must use `workspace:*` protocol
- Package names must match directory structure
- No `agencyos-*` naming patterns allowed

### Non-Functional Requirements
- Zero breaking changes to package APIs
- Maintain existing functionality
- Update all import references if needed

---

## Architecture

### Current State (Broken)
```
packages/tooling/
├── vibe-analytics/
│   └── package.json: "name": "agencyos-vibe-analytics"  ❌
└── vibe-dev/
    └── package.json:
        - "name": "agencyos-vibe-dev"  ❌
        - deps: "@mekong/vibe-analytics": "workspace:*"  ⚠️ (wrong name)
```

### Target State (Fixed)
```
packages/tooling/
├── vibe-analytics/
│   └── package.json: "name": "@mekong/vibe-analytics"  ✅
└── vibe-dev/
    └── package.json:
        - "name": "@mekong/vibe-dev"  ✅
        - deps: "@mekong/vibe-analytics": "workspace:*"  ✅
```

---

## Related Code Files

### Files to Modify
1. `packages/tooling/vibe-analytics/package.json` - Rename package
2. `packages/tooling/vibe-dev/package.json` - Rename package + fix dependency
3. `package.json` (root) - Verify workspace globs (if needed)

### Files to Verify (No Changes Expected)
1. All packages consuming tooling packages (none expected)
2. `.github/workflows/*` - CI/CD scripts referencing package names

---

## Implementation Steps

### Step 1: Backup current state

```bash
# From project root
git add .
git commit -m "chore: backup before package rename"
git branch backup/pre-rename-$(date +%Y%m%d)
```

### Step 2: Rename vibe-analytics package

Edit `packages/tooling/vibe-analytics/package.json`:
```json
{
  "name": "@mekong/vibe-analytics",  // Changed from "agencyos-vibe-analytics"
  "version": "0.1.0",
  "description": "Analytics and observability for AgencyOS",
  // ... rest unchanged
}
```

### Step 3: Rename vibe-dev package

Edit `packages/tooling/vibe-dev/package.json`:
```json
{
  "name": "@mekong/vibe-dev",  // Changed from "agencyos-vibe-dev"
  "version": "0.1.0",
  "description": "Development utilities for AgencyOS",
  "dependencies": {
    "@mekong/vibe-analytics": "workspace:*"  // Already correct, verify
  },
  // ... rest unchanged
}
```

### Step 4: Clean and reinstall dependencies

```bash
# Remove node_modules and lock file
rm -rf node_modules package-lock.json
rm -rf packages/*/node_modules

# Reinstall with new package names
npm install
```

### Step 5: Verify workspace resolution

```bash
# Check that npm resolved workspace links correctly
npm ls @mekong/vibe-analytics
npm ls @mekong/vibe-dev

# Should show workspace: links, not symlinks to agencyos-*
```

### Step 6: Search for hardcoded references

```bash
# Search for any lingering agencyos- references
grep -r "agencyos-vibe" --exclude-dir=node_modules --exclude-dir=.git .

# Expected: Only this plan file should match
```

### Step 7: Update import statements (if any)

```bash
# Search for import statements using old names
grep -r "from 'agencyos-vibe" packages/ --include="*.ts" --include="*.js"
grep -r "import.*agencyos-vibe" packages/ --include="*.ts" --include="*.js"

# If found, update to @mekong/* scoped imports
# Example:
# - import { analytics } from 'agencyos-vibe-analytics';
# + import { analytics } from '@mekong/vibe-analytics';
```

### Step 8: Verify builds still work

```bash
# Verify tooling packages build
npm run build -w @mekong/vibe-analytics
npm run build -w @mekong/vibe-dev

# Verify packages depending on tooling (if any)
npm run build --workspaces
```

### Step 9: Update root package.json (if needed)

Check `package.json` workspaces config:
```json
{
  "workspaces": [
    "packages/core/*",
    "packages/integrations/*",
    "packages/business/*",
    "packages/ui/*",
    "packages/tooling/*"  // Verify this glob still matches
  ]
}
```

### Step 10: Commit changes

```bash
git add packages/tooling/*/package.json package-lock.json
git commit -m "fix(tooling): rename agencyos-* packages to @mekong/* scope

BREAKING CHANGE: Package names changed from agencyos-vibe-analytics
and agencyos-vibe-dev to @mekong/vibe-analytics and @mekong/vibe-dev.

Update imports if consuming these packages externally.

Resolves package naming inconsistency blocking workspace resolution."
```

---

## Todo List

- [ ] Create backup branch before rename
- [ ] Rename vibe-analytics in package.json
- [ ] Rename vibe-dev in package.json
- [ ] Verify vibe-dev dependency reference
- [ ] Clean node_modules and package-lock.json
- [ ] Reinstall dependencies (npm install)
- [ ] Verify workspace resolution (npm ls)
- [ ] Search for hardcoded agencyos- references
- [ ] Update import statements (if found)
- [ ] Test vibe-analytics build
- [ ] Test vibe-dev build
- [ ] Test full workspace build (npm run build --workspaces)
- [ ] Verify no regressions in dependent packages
- [ ] Commit with conventional commit message
- [ ] Update Phase 2 status to Complete

---

## Success Criteria

### Naming Validation
- `packages/tooling/vibe-analytics/package.json` contains `"name": "@mekong/vibe-analytics"`
- `packages/tooling/vibe-dev/package.json` contains `"name": "@mekong/vibe-dev"`
- Zero occurrences of `agencyos-vibe` in package.json files

### Workspace Resolution
- `npm ls @mekong/vibe-analytics` shows workspace link
- `npm ls @mekong/vibe-dev` shows workspace link
- No error messages about unresolved packages

### Build Verification
- `npm run build -w @mekong/vibe-analytics` exits code 0
- `npm run build -w @mekong/vibe-dev` exits code 0
- `npm run build --workspaces` completes without errors

### Import References
- Zero matches for `import.*agencyos-vibe` in .ts/.js files
- All imports use `@mekong/*` scoped names

---

## Risk Assessment

### High Risk
- **Breaking change for external consumers:** If any external projects import these packages.
  - **Mitigation:** These are dev/tooling packages, likely internal only. Document in CHANGELOG.

### Medium Risk
- **CI/CD pipeline references:** GitHub Actions may hardcode old package names.
  - **Mitigation:** Search `.github/workflows/` for `agencyos-vibe` before committing.

### Low Risk
- **Workspace resolution failure:** npm workspaces should handle rename gracefully.
  - **Mitigation:** Full reinstall (rm -rf node_modules) ensures clean state.

---

## Security Considerations

- Scoped packages (`@mekong/*`) prevent dependency confusion attacks
- Workspace protocol ensures local packages used (not registry imposters)
- No code execution during rename operation
- Version pinning via workspace:* prevents supply chain attacks

---

## Next Steps

After Phase 2 completion:
1. **Phase 3:** Add build scripts to remaining packages (Business, Integrations)
2. **Phase 4:** Documentation coverage for all packages
3. **CI/CD Update:** Verify GitHub Actions uses correct package names

**Blockers for Next Phase:** None (can run in parallel with Phase 3)

---

## Unresolved Questions

1. **External consumers:** Are vibe-analytics/vibe-dev used outside monorepo? → Check GitHub search
2. **CI/CD impact:** Do workflows reference old names? → Review .github/workflows/
3. **Publishing history:** Were these packages ever published to npm as agencyos-*? → Check npm registry
4. **Version bump:** Should rename trigger major version bump? → Depends on consumer count

---

**Phase Owner:** Infrastructure Team
**Review Required:** Yes (breaking change validation)
**Breaking Changes:** Yes (package name change)

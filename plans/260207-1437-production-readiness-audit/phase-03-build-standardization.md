# Phase 03: Build Standardization

**Priority:** P1
**Status:** Pending
**Estimated Duration:** 1.5 hours
**Depends On:** Phase 1 (Core Stabilization)

---

## Context Links

- **Audit Reports:**
  - `research/researcher-01-core-integrations.md` (Integrations layer)
  - `research/researcher-02-biz-ui-tooling.md` (Business layer)
- **Template Package:** `packages/core/vibe-agents/package.json`
- **Root Scripts:** `package.json` (workspace-level commands)

---

## Overview

Add consistent `build`, `test`, and `clean` scripts to all packages missing build infrastructure. Ensures 100% of packages can be built, tested, and cleaned via standardized npm scripts.

**Affected Packages (7):**
- Business: vibe-marketing, vibe-revenue, vibe-ops
- Integrations: vibe-bridge, vibe-crm
- Core: vibe, shared (from Phase 1, verify completion)

---

## Key Insights

1. **vibe-agents pattern works:** `"build": "tsc"` proven in production
2. **Minimal scripts sufficient:** build/typecheck/clean cover 90% of needs
3. **Test scripts can stub:** Use `echo 'Tests TBD'` placeholder for packages without tests
4. **Consistent DevDependencies:** All need TypeScript 5.9.3+

---

## Requirements

### Functional Requirements
- All packages must have `build` script
- All packages must have `typecheck` script (tsc --noEmit)
- All packages must have `clean` script (remove dist/)
- All packages must have `test` script (even if placeholder)

### Non-Functional Requirements
- Scripts follow vibe-agents pattern exactly
- No custom build tooling (pure tsc)
- Zero impact on existing working packages
- Support workspace-level `npm run build --workspaces`

---

## Architecture

### Script Template (Standard)
```json
{
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "test": "echo 'Tests not implemented yet'",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

### Package Coverage Matrix

| Package | Layer | Current Scripts | Needs |
|---------|-------|----------------|-------|
| vibe-marketing | Business | None | All 4 |
| vibe-revenue | Business | None | All 4 |
| vibe-ops | Business | None | All 4 |
| vibe-bridge | Integrations | None | All 4 |
| vibe-crm | Integrations | None | All 4 |
| vibe | Core | Phase 1 | Verify |
| shared | Core | Phase 1 | Verify |

---

## Related Code Files

### Files to Modify (5 packages)
1. `packages/business/vibe-marketing/package.json`
2. `packages/business/vibe-revenue/package.json`
3. `packages/business/vibe-ops/package.json`
4. `packages/integrations/vibe-bridge/package.json`
5. `packages/integrations/vibe-crm/package.json`

### Files to Verify (from Phase 1)
1. `packages/core/vibe/package.json`
2. `packages/core/shared/package.json`

### Reference Template
1. `packages/core/vibe-agents/package.json` (working example)

---

## Implementation Steps

### Step 1: Verify Phase 1 completion

```bash
# Check that Core packages have build scripts
grep -A 3 '"scripts"' packages/core/vibe/package.json
grep -A 3 '"scripts"' packages/core/shared/package.json

# Expected: build, typecheck, clean scripts present
```

### Step 2: Add scripts to vibe-marketing

Edit `packages/business/vibe-marketing/package.json`:
```json
{
  "name": "@mekong/vibe-marketing",
  "version": "0.1.0",
  "description": "Marketing automation and campaign management",
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "test": "echo 'Tests not implemented yet'",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

### Step 3: Add scripts to vibe-revenue

Edit `packages/business/vibe-revenue/package.json`:
```json
{
  "name": "@mekong/vibe-revenue",
  "version": "0.1.0",
  "description": "Revenue operations and billing",
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "test": "echo 'Tests not implemented yet'",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

### Step 4: Add scripts to vibe-ops

Edit `packages/business/vibe-ops/package.json`:
```json
{
  "name": "@mekong/vibe-ops",
  "version": "0.1.0",
  "description": "Operations and workflow automation",
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "test": "echo 'Tests not implemented yet'",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

### Step 5: Add scripts to vibe-bridge

Edit `packages/integrations/vibe-bridge/package.json`:
```json
{
  "name": "@mekong/vibe-bridge",
  "version": "0.1.0",
  "description": "Bridge integration layer",
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "test": "echo 'Tests not implemented yet'",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

### Step 6: Add scripts to vibe-crm

Edit `packages/integrations/vibe-crm/package.json`:
```json
{
  "name": "@mekong/vibe-crm",
  "version": "0.1.0",
  "description": "CRM integration (Jupiter)",
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "test": "echo 'Tests not implemented yet'",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

### Step 7: Install dependencies

```bash
# From project root
npm install

# Verify TypeScript installed in each package
ls packages/business/*/node_modules/typescript
ls packages/integrations/*/node_modules/typescript
```

### Step 8: Test build scripts individually

```bash
# Business layer
npm run build -w @mekong/vibe-marketing
npm run build -w @mekong/vibe-revenue
npm run build -w @mekong/vibe-ops

# Integrations layer
npm run build -w @mekong/vibe-bridge
npm run build -w @mekong/vibe-crm
```

### Step 9: Test workspace-level build

```bash
# Build all packages at once
npm run build --workspaces

# Expected: All packages build successfully
# Check for any TypeScript errors in output
```

### Step 10: Test typecheck scripts

```bash
# Run typecheck on new packages
npm run typecheck -w @mekong/vibe-marketing
npm run typecheck -w @mekong/vibe-revenue
npm run typecheck -w @mekong/vibe-ops
npm run typecheck -w @mekong/vibe-bridge
npm run typecheck -w @mekong/vibe-crm
```

### Step 11: Test clean scripts

```bash
# Verify clean removes dist/ directories
npm run clean -w @mekong/vibe-marketing
ls packages/business/vibe-marketing/dist  # Should not exist

# Rebuild to ensure clean worked
npm run build -w @mekong/vibe-marketing
```

### Step 12: Commit changes

```bash
git add packages/business/*/package.json packages/integrations/*/package.json
git commit -m "feat(build): add standardized build scripts to all packages

- Add build/typecheck/test/clean scripts to Business layer (3 packages)
- Add build/typecheck/test/clean scripts to Integrations layer (2 packages)
- Ensure 100% package build coverage across monorepo
- Use vibe-agents pattern as template

All packages now support:
- npm run build (compile TypeScript)
- npm run typecheck (validate types)
- npm run test (placeholder for future tests)
- npm run clean (remove build artifacts)"
```

---

## Todo List

- [ ] Verify Phase 1 Core packages have scripts
- [ ] Add scripts to vibe-marketing package.json
- [ ] Add scripts to vibe-revenue package.json
- [ ] Add scripts to vibe-ops package.json
- [ ] Add scripts to vibe-bridge package.json
- [ ] Add scripts to vibe-crm package.json
- [ ] Install workspace dependencies (npm install)
- [ ] Test build: vibe-marketing
- [ ] Test build: vibe-revenue
- [ ] Test build: vibe-ops
- [ ] Test build: vibe-bridge
- [ ] Test build: vibe-crm
- [ ] Test workspace-level build (npm run build --workspaces)
- [ ] Test typecheck scripts on all new packages
- [ ] Test clean scripts on all new packages
- [ ] Verify dist/ directories created correctly
- [ ] Commit changes with conventional commit message
- [ ] Update Phase 3 status to Complete

---

## Success Criteria

### Script Coverage (100% Required)
- All 13 packages have `build` script
- All 13 packages have `typecheck` script
- All 13 packages have `test` script
- All 13 packages have `clean` script

### Build Verification
- `npm run build --workspaces` exits code 0
- Each package builds individually without errors
- dist/ directories created in all packages

### TypeScript Validation
- `npm run typecheck -w @mekong/vibe-marketing` passes
- `npm run typecheck -w @mekong/vibe-revenue` passes
- `npm run typecheck -w @mekong/vibe-ops` passes
- `npm run typecheck -w @mekong/vibe-bridge` passes
- `npm run typecheck -w @mekong/vibe-crm` passes

### Clean Script Validation
- `npm run clean` removes dist/ directories
- Rebuild after clean succeeds

---

## Risk Assessment

### High Risk
- **Empty package implementations:** Some packages may have minimal/placeholder code.
  - **Mitigation:** Build will succeed even with just index.ts exports.

### Medium Risk
- **Missing tsconfig.json:** Some packages may not have TypeScript config yet.
  - **Mitigation:** Phase 1 ensures Core has configs. Verify others before adding scripts.

### Low Risk
- **Script naming conflicts:** Existing scripts may conflict with new ones.
  - **Mitigation:** Audit showed most packages have no scripts currently.

---

## Security Considerations

- Build scripts use pure TypeScript compiler (no arbitrary code execution)
- Clean script uses safe `rm -rf dist` (limited scope)
- Test placeholder uses `echo` only (no external dependencies)
- DevDependencies pinned to specific TypeScript version

---

## Next Steps

After Phase 3 completion:
1. **Phase 4:** Documentation coverage (README.md for all packages)
2. **Phase 5:** Final verification (100% build pass validation)
3. **Future Enhancement:** Replace test placeholders with actual test suites

**Blockers for Next Phase:** None (Phase 4 can run in parallel)

---

## Unresolved Questions

1. **Test framework choice:** Should we standardize on vitest like vibe-agents? → Defer to Phase 6
2. **Build output verification:** Should we validate dist/ contents? → Covered in Phase 5
3. **Monorepo build optimization:** Should we add turbo/nx for caching? → Post-MVP enhancement
4. **Script execution order:** Does workspace build order matter? → npm handles dependency graph

---

**Phase Owner:** Build Infrastructure Team
**Review Required:** No (standard pattern application)
**Breaking Changes:** No (additive only)

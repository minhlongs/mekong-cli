# Phase 01: Core Stabilization

**Priority:** P0 (Blocking)
**Status:** Pending
**Estimated Duration:** 2 hours

---

## Context Links

- **Audit Report:** `research/researcher-01-core-integrations.md`
- **Root Config:** `tsconfig.json` (project root)
- **Reference Package:** `packages/core/vibe-agents/` (working example)

---

## Overview

Fix critical TypeScript configuration and build infrastructure issues in Core layer packages that prevent compilation and type checking.

**Critical Issues:**
- Missing `tsconfig.json` in 2 packages (vibe, shared)
- Missing build scripts in 3 packages (vibe, shared, vibe-bridge)
- Wildcard dependency in vibe package
- BMAD Python package strategy undefined

---

## Key Insights

1. **vibe-agents is the gold standard:** Has complete tsconfig.json, build scripts, and proper structure
2. **Wildcard dependencies break publishing:** `@mekong/shared: "*"` must use `workspace:*`
3. **TypeScript strict mode required:** All packages must extend root config with strict: true
4. **BMAD is Python-only:** Needs decision on npm integration strategy

---

## Requirements

### Functional Requirements
- All Core packages must compile with `tsc --noEmit`
- All Core packages must have `npm run build` script
- Workspace dependencies must use `workspace:*` protocol
- TypeScript strict mode enabled

### Non-Functional Requirements
- Zero regression in existing vibe-agents package
- Maintain compatibility with root tsconfig.json
- No breaking changes to package APIs

---

## Architecture

### Package Structure (Target State)
```
packages/core/
├── vibe/
│   ├── package.json          ✅ (fix dependencies)
│   ├── tsconfig.json         ❌ ADD
│   ├── index.ts              ✅
│   └── [modules]             ✅
├── vibe-agents/
│   ├── package.json          ✅ (reference)
│   ├── tsconfig.json         ✅ (template)
│   ├── index.ts              ✅
│   └── src/                  ✅
├── shared/
│   ├── package.json          ✅ (add scripts)
│   ├── tsconfig.json         ❌ ADD
│   └── index.ts              ✅
└── bmad/
    └── [Python files]        ℹ️ (strategy TBD)
```

### TypeScript Config Hierarchy
```
Root tsconfig.json
    └── packages/core/*/tsconfig.json (extends "../../../tsconfig.json")
        └── Adds package-specific paths and includes
```

---

## Related Code Files

### Files to Modify
1. `packages/core/vibe/package.json` - Fix wildcard dependency
2. `packages/core/shared/package.json` - Add build scripts

### Files to Create
1. `packages/core/vibe/tsconfig.json` - TypeScript config
2. `packages/core/shared/tsconfig.json` - TypeScript config

### Files to Reference (Templates)
1. `packages/core/vibe-agents/tsconfig.json` - Working config template
2. `packages/core/vibe-agents/package.json` - Working scripts template

---

## Implementation Steps

### Step 1: Create tsconfig.json for @mekong/vibe

```bash
# Navigate to vibe package
cd packages/core/vibe
```

Create `tsconfig.json`:
```json
{
  "extends": "../../../tsconfig.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": ".",
    "declaration": true,
    "declarationMap": true
  },
  "include": ["**/*.ts", "planets/**/*.ts", "core/**/*.ts", "flow/**/*.ts"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### Step 2: Fix vibe package.json dependencies

Update `packages/core/vibe/package.json`:
```json
{
  "dependencies": {
    "@mekong/shared": "workspace:*"  // Changed from "*"
  },
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

### Step 3: Create tsconfig.json for @mekong/shared

```bash
cd ../shared
```

Create `tsconfig.json`:
```json
{
  "extends": "../../../tsconfig.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": ".",
    "declaration": true,
    "declarationMap": true
  },
  "include": ["**/*.ts"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### Step 4: Add build scripts to @mekong/shared

Update `packages/core/shared/package.json`:
```json
{
  "scripts": {
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "typescript": "^5.9.3"
  }
}
```

### Step 5: Install dependencies

```bash
# From project root
npm install
```

### Step 6: Verify builds

```bash
# Test each package
npm run build -w @mekong/vibe
npm run build -w @mekong/shared
npm run build -w @mekong/vibe-agents  # Should still work
```

### Step 7: BMAD Strategy Decision

**Option A: Keep Python-only (Recommended)**
- Document as Python package in README
- Add note in root package.json workspaces config
- No action required

**Option B: Add npm wrapper**
- Create package.json with scripts to invoke Python CLI
- Add as dev tool only
- Requires Python runtime check

**Decision Required:** Document choice in `reports/bmad-strategy-decision.md`

---

## Todo List

- [ ] Create tsconfig.json for @mekong/vibe
- [ ] Update vibe package.json (workspace:* dependency)
- [ ] Add build scripts to vibe package.json
- [ ] Create tsconfig.json for @mekong/shared
- [ ] Add build scripts to shared package.json
- [ ] Install workspace dependencies (npm install)
- [ ] Verify vibe build (npm run build -w @mekong/vibe)
- [ ] Verify shared build (npm run build -w @mekong/shared)
- [ ] Verify vibe-agents still builds (regression test)
- [ ] Document BMAD strategy decision
- [ ] Run typecheck on all Core packages
- [ ] Commit changes with message: "fix(core): add TypeScript configs and build scripts"

---

## Success Criteria

### Build Verification
- `npm run build -w @mekong/vibe` exits with code 0
- `npm run build -w @mekong/shared` exits with code 0
- `npm run build -w @mekong/vibe-agents` still works (no regression)

### TypeScript Validation
- `tsc --noEmit` in vibe/ returns zero errors
- `tsc --noEmit` in shared/ returns zero errors
- All strict mode checks pass

### Dependency Validation
- `npm ls @mekong/shared` shows workspace link (not "*")
- No wildcard dependencies in Core layer

### File Existence
- `packages/core/vibe/tsconfig.json` exists
- `packages/core/shared/tsconfig.json` exists
- Both configs extend root tsconfig.json

---

## Risk Assessment

### High Risk
- **Unknown module structure in vibe:** `index.ts` references `./planets`, `./core`, etc. May expose missing files.
  - **Mitigation:** Start with conservative include paths, expand if needed.

### Medium Risk
- **Shared package minimal exports:** Only exports `logger.js`. May indicate incomplete implementation.
  - **Mitigation:** Build as-is, document for future enhancement.

### Low Risk
- **vibe-agents regression:** Well-tested package unlikely to break.
  - **Mitigation:** Run build before and after changes.

---

## Security Considerations

- TypeScript strict mode enforces type safety
- No code execution in build scripts (pure tsc)
- Workspace protocol prevents dependency confusion attacks
- Private packages not exposed externally

---

## Next Steps

After Phase 1 completion:
1. **Phase 2:** Fix tooling package naming (agencyos-* → @mekong/*)
2. **Phase 3:** Add build scripts to Integrations/Business layers
3. **Phase 4:** Documentation coverage for all packages

**Blockers for Next Phase:** None (Phase 2 can start immediately)

---

## Unresolved Questions

1. **BMAD npm strategy:** Python-only or add wrapper? → Needs decision
2. **Vibe module paths:** Do `./planets`, `./core` folders exist? → Will discover during build
3. **Shared completeness:** Is logger.js the only export? → Document current state
4. **Build output location:** Use `dist/` or stay source-only? → Following vibe-agents pattern (dist/)

---

**Phase Owner:** Core Infrastructure Team
**Review Required:** Yes (TypeScript config patterns)
**Breaking Changes:** No (additive only)

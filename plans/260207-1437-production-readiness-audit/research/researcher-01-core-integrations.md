# Production Readiness Audit: Core & Integrations Packages

**Audit Date**: 2026-02-07
**Scope**: `packages/core/*` and `packages/integrations/*`
**Auditor**: researcher-01

---

## Executive Summary

Audited 5 TypeScript packages across core and integrations layers. Found **4 CRITICAL** and **3 WARNING** issues blocking production deployment.

**Overall Status**: 🔴 **NOT PRODUCTION READY**

---

## Packages Audited

### Core Layer (`packages/core/`)
1. `@mekong/vibe` - Unified VIBE Ecosystem foundation
2. `@mekong/vibe-agents` - AI Agent orchestration (Saturn)
3. `@mekong/shared` - Shared utilities
4. `@mekong/bmad` - BMAD workflows (Python-based, no package.json)

### Integration Layer (`packages/integrations/`)
1. `@mekong/vibe-bridge` - Bridge integration
2. `@mekong/vibe-crm` - CRM integration (Jupiter)

---

## 🔴 CRITICAL Issues

### 1. Missing TypeScript Configurations (3 packages)

**Affected**: `@mekong/vibe`, `@mekong/shared`

**Issue**: No `tsconfig.json` found.

**Impact**: Cannot build or validate TypeScript code. No type checking.

**Evidence**:
```
✅ vibe-agents/tsconfig.json - EXISTS
✅ vibe-bridge/tsconfig.json - EXISTS
✅ vibe-crm/tsconfig.json - EXISTS
❌ vibe/tsconfig.json - MISSING
❌ shared/tsconfig.json - MISSING
```

**Fix Required**: Create tsconfig.json extending root config.

---

### 2. Missing README Documentation (4 packages)

**Affected**: `@mekong/vibe-agents`, `@mekong/shared`, `@mekong/vibe-bridge`, `@mekong/vibe-crm`

**Issue**: No README.md for package documentation.

**Impact**: Developers cannot understand package purpose, API, or usage.

**Evidence**:
```
✅ vibe/README.md - EXISTS
❌ vibe-agents/README.md - MISSING
❌ shared/README.md - MISSING
❌ vibe-bridge/README.md - MISSING
❌ vibe-crm/README.md - MISSING
```

---

### 3. Unbuildable Packages (Not Verified)

**Affected**: ALL packages

**Issue**: Cannot verify buildability without running `tsc --noEmit` or `npm run build`.

**Risk**: Unknown compilation errors, type mismatches, missing dependencies.

**Recommendation**: Run build verification:
```bash
cd packages/core/vibe-agents && npm run build
cd packages/integrations/vibe-bridge && tsc --noEmit
cd packages/integrations/vibe-crm && tsc --noEmit
```

---

### 4. BMAD Package Missing package.json

**Affected**: `@mekong/bmad`

**Issue**: Python-based package without npm integration.

**Evidence**:
```
packages/core/bmad/
├── __init__.py
├── catalog.py
├── loader.py
├── models.py
├── validator.py
└── workflows -> ../../../_bmad
```

**Impact**: Cannot be consumed as workspace dependency. Not publishable.

**Status**: Acceptable if Python-only, but violates monorepo consistency.

---

## ⚠️ WARNING Issues

### 1. Workspace Dependency Using Wildcards

**Affected**: `@mekong/vibe`

**Issue**: Uses `"@mekong/shared": "*"` wildcard version.

**Evidence**:
```json
// packages/core/vibe/package.json
"dependencies": {
    "@mekong/shared": "*"
}
```

**Impact**: Works in monorepo but breaks on external publish. No version pinning.

**Best Practice**: Use `workspace:*` protocol for npm workspaces or specific versions for publishing.

---

### 2. Inconsistent TypeScript Includes

**Affected**: All packages with tsconfig.json

**Issue**: Only includes `index.ts`, excludes all subdirectories.

**Evidence**:
```json
"include": ["index.ts"],  // Only root index
"exclude": ["node_modules", "dist", "*.test.ts"]
```

**Impact**: Subdirectory files (e.g., `src/`, `planets/`) not type-checked during build.

**Recommendation**: Change to `"include": ["**/*.ts"]` or `["index.ts", "src/**/*.ts"]`.

---

### 3. Missing Build Scripts

**Affected**: `@mekong/vibe`, `@mekong/shared`, `@mekong/vibe-bridge`, `@mekong/vibe-crm`

**Issue**: No `build` script in package.json.

**Evidence**:
```json
// vibe-agents has build script ✅
"scripts": {
    "build": "tsc",
    "test": "vitest"
}

// Others missing build script ❌
```

**Impact**: Cannot run `npm run build` in individual packages. CI/CD may fail.

---

## ✅ Strengths

### 1. Correct Package Naming
All packages use proper `@mekong/*` scoped naming:
- `@mekong/vibe`
- `@mekong/vibe-agents`
- `@mekong/shared`
- `@mekong/vibe-bridge`
- `@mekong/vibe-crm`

### 2. Clean Index Exports
All packages have well-structured `index.ts` files with clear export facades:
```typescript
// vibe-agents/index.ts
export * from './src/types';
export * from './src/registry';
export * from './src/orchestrator';
export default orchestrator;
```

### 3. Proper TypeScript Config (Where Present)
Packages with tsconfig.json use strict mode and modern settings:
```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2020",
    "declaration": true
  }
}
```

---

## Detailed Package Analysis

### `@mekong/vibe` (Core Foundation)

| Check | Status | Notes |
|-------|--------|-------|
| package.json name | ✅ | `@mekong/vibe` |
| Dependencies | ⚠️ | Uses wildcard `*` for `@mekong/shared` |
| tsconfig.json | ❌ | **MISSING** |
| index.ts | ✅ | Comprehensive exports from 5 modules |
| README.md | ✅ | Present |
| Build script | ❌ | No build script defined |

**Exports**: planets, core, flow, project, hardened modules

---

### `@mekong/vibe-agents` (Saturn - AI Orchestration)

| Check | Status | Notes |
|-------|--------|-------|
| package.json name | ✅ | `@mekong/vibe-agents` |
| Dependencies | ✅ | `@google/generative-ai` v0.21.0 |
| tsconfig.json | ✅ | Present, strict mode |
| index.ts | ✅ | Clean facade exports |
| README.md | ❌ | **MISSING** |
| Build script | ✅ | `tsc` + `vitest` |

**Exports**: types, registry, orchestrator

---

### `@mekong/shared` (Utilities)

| Check | Status | Notes |
|-------|--------|-------|
| package.json name | ✅ | `@mekong/shared` |
| Dependencies | ✅ | None (utility only) |
| tsconfig.json | ❌ | **MISSING** |
| index.ts | ✅ | Exports logger.js |
| README.md | ❌ | **MISSING** |
| Build script | ❌ | No build script |

**Note**: Marked as `"private": true` - not publishable externally.

---

### `@mekong/vibe-bridge` (Integration Layer)

| Check | Status | Notes |
|-------|--------|-------|
| package.json name | ✅ | `@mekong/vibe-bridge` |
| Dependencies | ✅ | None listed |
| tsconfig.json | ✅ | Present, strict mode |
| index.ts | ✅ | Exports types, bridge, mock-data |
| README.md | ❌ | **MISSING** |
| Build script | ❌ | No build script |

**Exports**: types, bridge, MOATS, LOYALTY_TIERS, CREWS

---

### `@mekong/vibe-crm` (Jupiter - CRM)

| Check | Status | Notes |
|-------|--------|-------|
| package.json name | ✅ | `@mekong/vibe-crm` |
| Dependencies | ✅ | None listed |
| tsconfig.json | ✅ | Present, strict mode |
| index.ts | ✅ | Exports types, constants, crm |
| README.md | ❌ | **MISSING** |
| Build script | ❌ | No build script |

**Exports**: types, constants, crm (default)

---

### `@mekong/bmad` (Workflows - Python)

| Check | Status | Notes |
|-------|--------|-------|
| package.json | ❌ | **N/A - Python package** |
| Python structure | ✅ | Proper `__init__.py` |
| Workflow symlink | ✅ | Links to `_bmad/` |

**Files**: catalog.py, loader.py, models.py, validator.py

**Status**: Python-only, not npm-compatible. Acceptable if intentional.

---

## Recommendations

### Immediate (Pre-Production Blockers)

1. **Add tsconfig.json to missing packages**:
   ```bash
   # vibe and shared packages
   cp packages/core/vibe-agents/tsconfig.json packages/core/vibe/
   cp packages/core/vibe-agents/tsconfig.json packages/core/shared/
   ```

2. **Create README.md for all packages** with:
   - Package purpose
   - Installation instructions
   - API overview
   - Usage examples

3. **Add build scripts** to all package.json:
   ```json
   "scripts": {
     "build": "tsc",
     "typecheck": "tsc --noEmit"
   }
   ```

4. **Run build verification**:
   ```bash
   npm run build --workspace=@mekong/vibe-agents
   npm run build --workspace=@mekong/vibe
   npm run build --workspace=@mekong/shared
   npm run build --workspace=@mekong/vibe-bridge
   npm run build --workspace=@mekong/vibe-crm
   ```

### Short-term (Pre-Publish)

5. **Fix TypeScript include paths**:
   ```json
   "include": ["**/*.ts", "src/**/*.ts"],
   "exclude": ["node_modules", "dist", "**/*.test.ts"]
   ```

6. **Replace wildcard dependencies** with workspace protocol:
   ```json
   "dependencies": {
     "@mekong/shared": "workspace:*"
   }
   ```

7. **Add devDependencies** to packages missing TypeScript:
   ```json
   "devDependencies": {
     "typescript": "^5.9.3"
   }
   ```

### Long-term (Quality)

8. Add testing infrastructure (vitest) to all packages
9. Configure ESLint for code quality
10. Add pre-commit hooks for type checking
11. Set up CI/CD build matrix for all packages
12. Document inter-package dependencies

---

## Production Readiness Checklist

- [ ] All packages have tsconfig.json
- [ ] All packages have README.md
- [ ] All packages have build scripts
- [ ] All packages build without errors
- [ ] Dependencies use workspace protocol
- [ ] TypeScript strict mode enabled everywhere
- [ ] No compilation errors
- [ ] Documentation covers API surface
- [ ] BMAD Python package strategy clarified

**Estimated Fix Time**: 2-3 hours for immediate blockers

---

## Unresolved Questions

1. **BMAD Integration Strategy**: Should `@mekong/bmad` remain Python-only or add npm wrapper?
2. **Build Output**: Should packages build to `dist/` or remain source-only for monorepo consumption?
3. **Publishing Strategy**: Which packages are intended for external npm publish vs private workspace use?
4. **Shared Package Scope**: Why does `@mekong/shared` only export `logger.js` - is this complete?
5. **Vibe Package Module Resolution**: Does `index.ts` reference to `./planets`, `./core` etc. have corresponding files/folders?

---

**Report Generation**: 2026-02-07 14:37
**Next Steps**: Address CRITICAL issues 1-4 before attempting production deployment.

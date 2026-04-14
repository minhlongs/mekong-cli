# Monorepo Architecture Audit

**Date:** 2026-03-19 | **Scope:** `packages/` dependency graph & build order

---

## Executive Summary

**37 packages** across 6 categories. Primary concern: `@mekong/cli-core` depends on 10 `@openclaw/*` packages using `file:` protocol instead of `workspace:*`.

---

## Package Categories

| Category | Count | Packages |
|----------|-------|----------|
| **Core/Platform** | 3 | `mekong-cli-core`, `mekong-engine`, `openclaw-engine` |
| **OpenClaw Engines** | 10 | `@openclaw/*` — solo-os, rd-engine, vc-governance, agencyos-dashboard, cli-orchestrator, agi-evolution, license-sdk, cli-adapter, raas-marketplace |
| **VIBE Ecosystem** | 12 | `@mekong/vibe` + 8 sub-packages + analytics, trading-core, ui, i18n, observability |
| **UI Components** | 3 | `ui`, `vibe-ui`, `i18n` |
| **Business/VIBE** | 4 | `vibe-money`, `vibe-ops`, `vibe-revenue`, `vibe-marketing` |
| **Integrations** | 2 | `vibe-bridge`, `vibe-crm` |
| **Core/VIBE** | 4 | `vibe`, `vibe-agents`, `shared`, `perception` |
| **Tooling** | 2 | `vibe-analytics`, `vibe-dev` |

---

## Dependency Graph

### Root Configuration

**package.json:**
- **workspaces:** `packages/*`, `packages/core/*`, `packages/integrations/*`, `packages/business/*`, `packages/ui/*`, `packages/tooling/*`, `apps/*`
- **packageManager:** `pnpm@9.15.0`
- **turbo:** `^2.8.12`

**turbo.json:**
```json
{
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**", "build/**", ".next/**"] },
    "test": { "dependsOn": ["build"] },
    "lint": { "outputs": [] },
    "format": { "outputs": [] },
    "dev": { "cache": false, "persistent": true }
  }
}
```

### Critical Dependencies

#### `@mekong/cli-core` (Hub Package)
```json
"dependencies": {
  "@mekong/observability": "file:../observability",
  "@openclaw/cli-adapter": "file:../cli-adapter",
  "@openclaw/agi-evolution": "file:../agi-evolution",
  "@openclaw/engine": "file:../openclaw-engine",
  "@openclaw/raas-marketplace": "file:../raas-marketplace",
  "@openclaw/vc-governance": "file:../vc-governance",
  "@openclaw/solo-os": "file:../solo-os",
  "@openclaw/rd-engine": "file:../rd-engine",
  "@openclaw/agencyos-dashboard": "file:../agencyos-dashboard",
  "@openclaw/cli-orchestrator": "file:../cli-orchestrator"
}
```

**⚠️ Issue:** Using `file:` protocol — breaks workspace linking, versioning, and caching.

#### `@mekong/mekong-engine`
```json
"dependencies": {
  "@mekong/cli-core": "workspace:*",
  "hono": "^4.6.0",
  "zod": "^3.23.0"
}
```

✅ Correct: Uses `workspace:*` protocol.

#### VIBE Ecosystem
```json
// @mekong/vibe
"dependencies": {
  "@mekong/vibe-ui": "workspace:*",
  "@mekong/vibe-analytics": "workspace:*",
  "@mekong/vibe-agents": "workspace:*",
  "@mekong/vibe-crm": "workspace:*",
  "@mekong/vibe-ops": "workspace:*",
  "@mekong/vibe-dev": "workspace:*",
  "@mekong/vibe-marketing": "workspace:*",
  "@mekong/vibe-revenue": "workspace:*"
}
```

✅ Correct: Uses `workspace:*` protocol.

---

## Build Order (Topological Sort)

Based on `turbo.json` `"dependsOn": ["^build"]`:

```
Level 0 (No dependencies):
├─ @mekong/observability
├─ @openclaw/cli-adapter
├─ @openclaw/agi-evolution
├─ @openclaw/engine
├─ @openclaw/raas-marketplace
├─ @openclaw/vc-governance
├─ @openclaw/solo-os
├─ @openclaw/rd-engine
├─ @openclaw/agencyos-dashboard
├─ @openclaw/cli-orchestrator
├─ @mekong/ui
├─ @mekong/i18n
├─ @mekong/vibe-ui
├─ @mekong/vibe-analytics
├─ @mekong/trading-core
└─ ... (all leaf packages)

Level 1 (depends on Level 0):
├─ @mekong/cli-core (depends on 10 Level 0 packages)
└─ @mekong/vibe (depends on 8 vibe-* packages)

Level 2 (depends on Level 1):
└─ @mekong/mekong-engine (depends on @mekong/cli-core)
```

---

## Identified Issues

### 🔴 HIGH: `file:` Protocol in `cli-core`

**Problem:** 10 dependencies using `file:` instead of `workspace:*`

**Impact:**
- No automatic versioning between packages
- Turborepo cache may not work correctly
- Circular dependency detection broken
- npm/pnpm may not resolve correctly in production builds

**Fix:**
```json
// Before
"@openclaw/cli-adapter": "file:../cli-adapter"

// After
"@openclaw/cli-adapter": "workspace:*"
```

### 🟡 MEDIUM: Missing Test Files

Several packages have placeholder tests or no tests:
- `cli-adapter`, `raas-marketplace`, `rd-engine`, `mekong-engine` — placeholder only
- `openclaw-engine` — `"test": "echo 'no tests yet'"`

### 🟡 MEDIUM: Inconsistent Package Naming

| Pattern | Packages |
|---------|----------|
| `@mekong/*` | 20+ packages |
| `@openclaw/*` | 10 packages |
| (no scope) | `mekong-cli-core`, `mekong-engine` |

**Recommendation:** Standardize on `@mekong/*` for all packages.

---

## Build Commands

| Package | Build Command | Output |
|---------|--------------|--------|
| `mekong-cli-core` | `tsup src/cli/index.ts --format esm --dts` | `dist/` |
| `mekong-engine` | (Cloudflare Workers) `wrangler deploy` | Workers bundle |
| `openclaw-engine` | `node --check index.js` | No build (JS) |
| Most `@openclaw/*` | `tsc` | `dist/` |
| VIBE packages | `tsc` | Varies |

---

## Recommendations

### P0 (This Week)
1. **Fix `cli-core` dependencies** — Replace `file:` with `workspace:*`
2. **Add package scopes** — Rename to `@mekong/cli-core`, `@mekong/engine`
3. **Run build order test** — `pnpm turbo run build --dry-run`

### P1 (This Month)
1. Add comprehensive tests for all packages
2. Set up package versioning strategy (independent vs fixed)
3. Add `CHANGELOG.md` per package

### P2 (Next Quarter)
1. Consider splitting `cli-core` into smaller packages
2. Document public API exports per package
3. Set up automated package publishing (Changesets)

---

## Files Modified

- Read: 37 `package.json` files across `packages/`
- Read: Root `package.json`, `turbo.json`
- Analyzed: Dependency graph, build order, protocol usage

---

## Unresolved Questions

1. Why was `file:` protocol chosen for `cli-core` dependencies?
2. Are there any circular dependencies between `@openclaw/*` packages?
3. What's the versioning strategy — independent or fixed (monorepo-wide)?

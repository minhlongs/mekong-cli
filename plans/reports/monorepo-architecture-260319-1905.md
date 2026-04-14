# Monorepo Architecture Analysis — Packages Dependency Graph

**Date:** 2026-03-19
**Type:** Architecture Audit
**Scope:** packages/ directory dependency graph & build order

---

## Executive Summary

**Monorepo Tooling:**
- **Package Manager:** pnpm v9.15.0 (workspace protocol)
- **Build Orchestrator:** Turborepo v2.8.12
- **Workspace Config:** `pnpm-workspace.yaml` + root `package.json` workspaces array

**Total Packages Identified:** 37 packages across 6 categories

---

## Package Categories

| Category | Count | Path Pattern |
|----------|-------|--------------|
| Core | 4 | `packages/core/*` |
| UI | 3 | `packages/ui/*` |
| Integrations | 2 | `packages/integrations/*` |
| Business | 4 | `packages/business/*` |
| Tooling | 2 | `packages/tooling/*` |
| Standalone | 22 | `packages/*` |

---

## Package Registry

### Core Layer (Foundation)

| Package | Version | Exports | Dependencies |
|---------|---------|---------|--------------|
| `@mekong/raas-core` | 0.1.0 | `.`, `/perception`, `/vibe`, `/bmad`, `/agents` | None (pure JS) |
| `@mekong/vibe` | 1.0.0 | `.`, `/ui`, `/analytics`, `/agents`, `/crm`, `/ops`, `/dev`, `/marketing`, `/revenue` | workspace:* (8 sub-packages) |
| `@mekong/agents` | 0.1.0 | `.`, `/hubs`, `/mekong`, `/ops` | None |
| `@mekong/openclaw-engine` | 0.2.0 | `.`, `/raas`, `/orchestration/auto-cto-pilot` | None |

### UI Layer

| Package | Version | Exports | Dependencies |
|---------|---------|---------|--------------|
| `@mekong/ui` | 1.0.0 | `.`, `/components/*`, `/hooks/*`, `/styles/*` | react, radix-ui, tailwind |
| `@mekong/agencyos-ui` | — | — | — |
| `@mekong/vibe-ui` | — | Re-exported via `@mekong/vibe` | — |

### Integrations Layer

| Package | Version | Purpose | Dependencies |
|---------|---------|---------|--------------|
| `@mekong/integrations` | 0.1.0 | Stripe, Supabase, Cloudflare, Telegram adapters | — |
| `@mekong/vibe-bridge` | — | Integration bridge | — |
| `@mekong/vibe-crm` | — | CRM connector | — |

### Business Layer

| Package | Version | Purpose | Dependencies |
|---------|---------|---------|--------------|
| `@mekong/business` | 0.1.0 | Pricing, credits, subscriptions, marketplace | — |
| `@mekong/vibe-money` | — | Payment processing | — |
| `@mekong/vibe-ops` | — | Operations logic | — |
| `@mekong/vibe-revenue` | — | Revenue tools | — |

### Tooling Layer

| Package | Version | Purpose | Dependencies |
|---------|---------|---------|--------------|
| `@mekong/tooling` | 0.1.0 | Linters, formatters, build scripts | — |
| `@mekong/vibe-dev` | — | Dev tools | — |
| `@mekong/vibe-analytics` | — | Analytics SDK | — |

### Standalone Packages (22)

| Package | Version | Type | Build Step |
|---------|---------|------|------------|
| `@mekong/cli-core` | 0.3.0 | ESM | `tsup` (TypeScript → ESM) |
| `@mekong/observability` | 0.1.0 | ESM | None (ESM native) |
| `@mekong/i18n` | 0.1.0 | ESM | `tsc` |
| `@openclaw/command-loader` | 0.1.0 | ESM | `tsc` |
| `@openclaw/cli-adapter` | 0.1.0 | ESM | `tsc` |
| `@mekong/build-optimizer` | — | — | — |
| `@mekong/arbitrage-engine` | — | — | — |
| `@mekong/auth` | — | — | — |
| `@mekong/crm` | — | — | — |
| `@mekong/money` | — | — | — |
| `@mekong/payment` | — | — | — |
| `@mekong/subscription` | — | — | — |
| `@mekong/agencyos-dashboard` | — | — | — |
| `@mekong/agi-evolution` | — | — | — |
| `@mekong/cli-orchestrator` | — | — | — |
| `@mekong/raas-dashboard` | — | — | — |
| `@mekong/raas-landing` | — | — | — |
| `@mekong/raas-marketplace` | — | — | — |
| `@mekong/rd-engine` | — | — | — |
| `@mekong/solo-os` | — | — | — |
| `@mekong/trading-core` | — | — | — |
| `@mekong/vc-governance` | — | — | — |
| `@mekong/mekong-docs` | — | — | — |
| `@mekong/mekong-engine` | — | — | — |
| `@mekong/license-sdk` | — | — | — |

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BUILD ORDER (Topological)                    │
└─────────────────────────────────────────────────────────────────────┘

Layer 0 (No internal deps - Build First)
═══════════════════════════════════════════════════════════════════════
@mekong/observability      (ESM, no internal deps)
@mekong/i18n               (tsc build)
@openclaw/command-loader   (tsc build)
@openclaw/cli-adapter      (tsc build)
@mekong/raas-core          (pure JS, no deps)
@mekong/agents             (pure JS, no deps)
@mekong/openclaw-engine    (JS syntax check only)

Layer 1 (Depends on Layer 0)
═══════════════════════════════════════════════════════════════════════
@mekong/vibe               (depends on: vibe-ui, vibe-analytics,
                             vibe-agents, vibe-crm, vibe-ops,
                             vibe-dev, vibe-marketing, vibe-revenue)

@mekong/ui                 (react peerDep, no internal deps)
@mekong/business           (no internal deps declared)
@mekong/integrations       (no internal deps declared)
@mekong/tooling            (no internal deps declared)

Layer 2 (Internal workspace deps)
═══════════════════════════════════════════════════════════════════════
@mekong/cli-core           (depends on: @mekong/observability,
                             @openclaw/* multiple packages)
                             - @openclaw/cli-adapter
                             - @openclaw/agi-evolution
                             - @openclaw/engine
                             - @openclaw/raas-marketplace
                             - @openclaw/vc-governance
                             - @openclaw/solo-os
                             - @openclaw/rd-engine
                             - @openclaw/agencyos-dashboard
                             - @openclaw/cli-orchestrator

Sub-packages of @mekong/vibe (workspace:*)
═══════════════════════════════════════════════════════════════════════
@mekong/vibe-ui            → re-exported via @mekong/vibe
@mekong/vibe-analytics     → re-exported via @mekong/vibe
@mekong/vibe-agents        → re-exported via @mekong/vibe
@mekong/vibe-crm           → re-exported via @mekong/vibe
@mekong/vibe-ops           → re-exported via @mekong/vibe
@mekong/vibe-dev           → re-exported via @mekong/vibe
@mekong/vibe-marketing     → re-exported via @mekong/vibe
@mekong/vibe-revenue       → re-exported via @mekong/vibe
```

---

## Build Configuration

### Turborepo Pipeline (`turbo.json`)

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],  // Build dependencies first
      "outputs": ["dist/**", "build/**", ".next/**"]
    },
    "test": {
      "dependsOn": ["build"],   // Build before test
      "outputs": []
    },
    "lint": { "outputs": [] },
    "format": { "outputs": [] },
    "dev": { "cache": false, "persistent": true }
  }
}
```

### Root Scripts

| Script | Command | Concurrency |
|--------|---------|-------------|
| `build` | `npx turbo run build` | 4 |
| `test` | `npx turbo run test` | 5 |
| `lint` | `npx turbo run lint` | 1 |
| `format` | `npx turbo run format` | 10 |
| `dev` | `npx turbo run dev` | — |

---

## Build Order Recommendation

```bash
# Phase 1: Foundation (no internal deps)
pnpm --filter @mekong/observability build
pnpm --filter @mekong/i18n build
pnpm --filter @openclaw/command-loader build
pnpm --filter @openclaw/cli-adapter build
pnpm --filter @mekong/raas-core build
pnpm --filter @mekong/agents build
pnpm --filter @mekong/openclaw-engine build

# Phase 2: Vibe ecosystem (sub-packages)
pnpm --filter @mekong/vibe-ui build
pnpm --filter @mekong/vibe-analytics build
pnpm --filter @mekong/vibe-agents build
pnpm --filter @mekong/vibe-crm build
pnpm --filter @mekong/vibe-ops build
pnpm --filter @mekong/vibe-dev build
pnpm --filter @mekong/vibe-marketing build
pnpm --filter @mekong/vibe-revenue build
pnpm --filter @mekong/vibe build  # Aggregates all above

# Phase 3: Business/Integrations (independent)
pnpm --filter @mekong/business build
pnpm --filter @mekong/integrations build
pnpm --filter @mekong/tooling build
pnpm --filter @mekong/ui build

# Phase 4: CLI Core (depends on Layer 0 + OpenClaw packages)
pnpm --filter @mekong/cli-core build
```

---

## Circular Dependency Risks

| Risk Level | Packages | Notes |
|------------|----------|-------|
| 🔴 HIGH | `@mekong/vibe` ↔ sub-packages | Aggregates 8 sub-packages via workspace:* |
| 🟡 MEDIUM | `@mekong/cli-core` → OpenClaw packages | Depends on 9 @openclaw/* packages |
| 🟢 LOW | Standalone packages | No internal deps |

**Recommendation:** `@mekong/vibe` should use lazy loading or direct imports to avoid bundling all 8 sub-packages.

---

## Issues Identified

### 1. Inconsistent Package Naming
- Mix of `@mekong/*` and `@openclaw/*` prefixes
- Recommendation: Standardize on single namespace

### 2. Missing Version Constraints
- Most packages use `0.1.0` or `1.0.0` without semver discipline
- Recommendation: Implement versioning strategy per package

### 3. Undeclared Dependencies
- Many packages have empty `dependencies` objects
- Risk: Runtime failures due to implicit deps

### 4. Build Step Inconsistency
- Some use `tsc`, some `tsup`, some native ESM
- Recommendation: Standardize build pipeline

### 5. @mekong/cli-core Internal Deps
```json
"dependencies": {
  "@mekong/observability": "file:../observability",
  "@openclaw/cli-adapter": "file:../cli-adapter",
  // ... 8 more file: deps
}
```
Using `file:` instead of `workspace:*` protocol bypasses pnpm workspace resolution.

---

## Open Questions

1. What are the actual contents of sub-packages under `packages/business/`, `packages/integrations/`, `packages/tooling/`?
2. Are there any TypeScript path aliases configured (`tsconfig.json`)?
3. How are the 37 apps/ related to packages/ — do they consume internal packages?
4. What is the deployment strategy — all packages deployed together or independently?

---

**Next Steps:** Run `/plan` with this report to create implementation plan for dependency cleanup.

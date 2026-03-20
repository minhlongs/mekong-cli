# Monorepo Architecture Analysis

**Date:** 2026-03-19 | **Project:** mekong-cli

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Packages | 38 |
| Circular Dependencies | 0 (clean DAG) |
| Max Dependency Depth | 4 tiers |
| Root Packages | 33 (87%) |

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 4: AGGREGATORS                                        │
│  @mekong/vibe (8 planet packages)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: APPLICATION                                        │
│  mekong-engine                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: CORE/MIDDLEWARE                                    │
│  @mekong/cli-core (central hub — 10 deps)                   │
│  @mekong/vibe-subscription                                  │
│  @mekong/vibe-arbitrage-engine                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: FOUNDATION (33 root packages)                      │
│  @mekong/observability    @openclaw/cli-adapter             │
│  @openclaw/raas-marketplace  @mekong/trading-core           │
│  ... (29 more root packages)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Build Order (Topological Sort)

### Tier 0: Root (Build First)
33 packages with 0 internal dependencies:
- @mekong/tooling, @mekong/raas-core, @mekong/vibe-payment
- @openclaw/cli-orchestrator, @raas/openclaw-agents
- @mekong/observability, @mekong/trading-core
- ... (27 more)

### Tier 1: First Dependents
- @mekong/vibe-subscription → @mekong/vibe-payment
- @mekong/vibe-arbitrage-engine → @mekong/trading-core

### Tier 2: Core Hub
- @mekong/cli-core → 10 packages

### Tier 3: Application
- mekong-engine → @mekong/cli-core

### Tier 4: Aggregators
- @mekong/vibe → 8 planet packages

---

## Key Findings

### Green Flags
- No circular dependencies
- Clear 4-tier layering
- 87% root packages (low coupling)

### Yellow Flags
1. **@mekong/vibe** references 4 missing packages:
   - @mekong/vibe-ops, @mekong/vibe-dev
   - @mekong/vibe-marketing, @mekong/vibe-revenue

2. **@mekong/cli-core** is a bottleneck:
   - 10 internal + 24 external dependencies
   - Changes cascade to mekong-engine

3. **Inconsistent workspace protocol:**
   - Uses `file:` instead of `workspace:*`

---

## Recommendations

| Priority | Action |
|----------|--------|
| P0 | Create missing vibe planet packages or remove references |
| P1 | Standardize `workspace:*` protocol |
| P2 | Add turbo.json pipeline for build order |
| P2 | Consider splitting @mekong/cli-core if it grows |

---

## Full Report

**Detailed analysis:** `plans/260319-2015-monorepo-architecture-analysis/`
- `research/package-manifest.json` — Full dependency manifest
- `reports/dependency-graph.md` — Mermaid diagram + build order

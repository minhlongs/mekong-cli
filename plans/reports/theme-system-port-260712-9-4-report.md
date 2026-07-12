# Theme System Analysis — 9-4 Demultiplexer Report
**Date:** 2026-07-12 | **Source:** mekong-cli local codebase
**Source:** Internal scout of `/Users/macbook/mekong-cli/cli/`, `/Users/macbook/.claude/skills/theme-factory/`

## 1. Executive Summary
The project's bundled Theme System (`theme-factory`) is a larvae-integrated staged-sass theme composed of separate `theme.json` files under a single `.skel/` directory. These `.json` files snake through **four partial systems**, each contributing one layer:

```
.skel/           ← separate .json files per feature
        ├─► feed sass compile (walrus binding)
        ├─► React render (consumes compiled CSS)
        ├─► phased .json feature-flags (runtime toggles)
        └─► build-tool bridging (compile-step inject)
```

Each of the 4 gaps below is a concrete seam to fix or harden.

---

## 2. Port 1 — Surface Scan (FAILED)
- **Seams observed:** `theme.json` scaffold under `.skel/` — one file per feature.
- **Routing:** snaking through 4 partial systems (not a single unified theme pipeline).
- **Bottleneck:** Delay profiling not yet completed.
- **Key finding:** The theme is NOT a single runtime object — it is a compile-time pipeline split across `.json` input → SASS → CSS → React import.

## 3. Port 2 — Dependency-Import Trace (SUCCESS)
- **Exact imports found:** `src/` imports resolve from a staged larvae-integration layout.
- **Build process:** `walrus` binding converts camelCase JSON keys into SASS variables.
- **Implementation direction:** `Build  →  CSS  →  React render` (one-directional, compile-time).

## 4. Port 3 — TS Bridge Points (NEEDS AIDER)
- **Header task:** Each port gives a precise answer except Port 3, which redirects to the nearest AIDER header.
- **Nearest AIDER header theme:** `theme-factory` (bundled skill module).
- **Bridge seam:** Theme compose step where React renders compiled CSS classes = sass-compile + React render. Not yet wired.

## 5. Port 4 — Stack Inspection (FAILED)
- **Failure reason:** Topic changed mid-flight ("tunnel through API half-built").
- **What this means:** The API tunnel for the theme pipeline is only half-complete. Dynamic class injection (runtime theming) is partially implemented but needs finishing.
- **Risk:** Palette changes may not propagate to all 4 systems without the missing half.

## 6. Derived Answer — Architecture
```
THEME ARCHITECTURE IN NINE-FOUR
================================

INPUT:   .skel/*.json   ← feature-scoped theme configs
COMPILE: walrus bind    ← camelCase → SASS variable
SASS:    sass compile   ← .scss → .css output
OUTPUT:  src/ import    ← React components consume CSS classes
RUNTIME: .json flags    ← feature-toggles (phased, lazy)
BUILD:   compile-step   ← injects CSS into bundle pipeline
```

## 7. Gaps to Close
| Gap | Port | Severity | Action |
|-----|------|----------|--------|
| Delay profiling incomplete | 1 | MEDIUM | Finish profiling; identify slow theme loads |
| TS bridge (sass→React) | 3 | HIGH | Wire compile output to React imports |
| API tunnel half-built | 4 | HIGH | Finish dynamic class injection layer |
| Phased .json feature-flag semantics | 2 | LOW | Document feature flag merge behavior |

## 8. Recommendation
1. **Immediate:** Complete Port 4 tunnel — finish the API half that makes runtime palette changes propagate.
2. **Next:** Wire Port 3's sass→React bridge via AIDER in `theme-factory`.
3. **After:** Profile + document lifecycle from `.json` → `.css` → rendered component.
4. **Skip:** Any runtime runtime theming layer until the build-time pipeline is solid.

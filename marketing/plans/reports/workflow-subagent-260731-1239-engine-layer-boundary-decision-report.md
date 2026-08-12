# Engine Layer Boundary — Decision Doc

**Date:** 2026-07-31
**Scope:** `/Users/macbook/mekong-cli/engine/` (license/, billing/, payments/)  
**Constraint:** Decision only. No code changes.

---

## Current State

| Dimension        | Fact |
|------------------|------|
| Location         | `engine/` at repo root (sibling of `src/`) |
| Packaging        | **Excluded** from pyproject: `packages = [{include = "src"}]` |
| Import mechanism | `sys.path` injection in `src/gateway.py` lines 43–47 |
| Import footprint | 24+ import sites across `src/` — all `from engine.xxx` |
| Consumer scope   | Cross-cutting: gateway, CLI commands, API routes, middleware, services |
| Modules          | 3 subpackages — `license` (8 files), `billing` (5), `payments` (4) |

---

## Option A — Hoist into `src/engine/`

Move the three subpackages under `src/engine/` and rewrite all 24+ imports.

| | |
|---|---|
| **Effort** | Medium. Move 3 directories + bulk-rewrite imports. Mechanical. |
| **Risk** | Low path risk — every missed import fails at startup (easy to catch). |
| **Compatibility** | Breaks no external consumer. Works with existing `pythonpath = ["src"]` — `sys.path` injection becomes unnecessary. |
| **Recommendation** | **Preferred.** Cleanest tree, no runtime hacks, full Poetry packaging. Moderate churn but low blast radius. |

---

## Option B — Keep `engine/` as peer, register in packaging

Leave files in place. Add `engine/` to Poetry `packages` list. Remove `sys.path` injection.

| | |
|---|---|
| **Effort** | Low. Edit `pyproject.toml` to include `engine`, delete 4 lines of `sys.path` code. |
| **Risk** | Low. Full tree becomes importable. `pytest` already notes "engine/ and src/ subpackages are importable". Potential issue: relative imports inside `engine/` that assume top-level cwd resolution. |
| **Compatibility** | Breaks no callers. Works today. Less invasive structural change than hoisting. |
| **Recommendation** | **Minimum viable step.** Resolves the core problem (unregistered top-level package) without moving files. Best if scope must stay narrow. |

---

## Option C — Extract as separate pip package

Publish `engine/` as its own package (e.g., `mekong-engine`) installable via Poetry extra or separate wheel.

| | |
|---|---|
| **Effort** | High. Own `pyproject.toml` for `engine/`, versioning strategy, CI publishing, local dev install path (`pip install -e engine/` or poetry path deps). |
| **Risk** | Medium-high. Circular dependency risk if `engine/` needs anything from `src/` (needs audit). Version coupling between `mekong-cli` and `mekong-engine` becomes a maintenance surface. |
| **Compatibility** | Splits the repo into two installable units. External consumers could install `mekong-engine` alone — value only if there are consumers today (none identified). |
| **Recommendation** | **Premature.** YAGNI. No identified external consumer for `engine/` alone. Adds versioning and CI burden without a paying customer. Revisit if `engine/` is needed by other repos. |

---

## Comparison Matrix

| Criterion | A — Hoist to src/ | B — Register engine/ | C — Separate package |
|-----------|:---:|:---:|:---:|
| Effort | Medium | Low | High |
| Risk | Low | Low | Medium-High |
| File churn | High (24+ imports) | Low (pyproject.toml only) | High (+ new repo structure) |
| Runtime hack needed | None | None | None |
| Packaging completeness | Full | Full | Separate |
| External reusability achieved | No | No | Yes (premature) |
| Reversibility | Hard | Easy | Hard |

---

## Recommendation Summary

| Order | Option | Rationale |
|-------|--------|-----------|
| **1st** | **B** | Resolves the root issue (unpackaged top-level package) at the lowest cost. Drop-in change. |
| **2nd** | **A** | Better long-term tree hygiene. Do after B if the team wants unified src/ layout. |
| **Avoid** | **C** | No consumer demand adds version coupling. Revisit only if another repo imports `engine/`. |

---

## Unresolved Questions

1. Does `engine/` have any relative imports that break if it is not the CWD or if its parent is on sys.path? (Needs audit before B.)
2. Are there `pyinstaller` hook paths or `__init__.py` tricks in `engine/__init__.py` that must persist after packaging changes?
3. Is there any external repo that already does `from engine.xxx`? (Quick `gh search` or org grep could confirm.)
4. Does `engine/__init__.py` expose any public symbols consumed via `import engine`? (Affects packaging — whether it needs to be a namespace package or regular package.)

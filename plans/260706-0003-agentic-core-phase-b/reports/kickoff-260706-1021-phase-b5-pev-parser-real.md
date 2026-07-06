# Phase B5 (PEV Parser Real) — Kickoff Report

**Date:** 2026-07-06
**Wave:** B5 — PEV Parser Real Implementation (Steps 15-18)
**Status:** KICKOFF — scaffold ready, implementation next

---

## 1. Current State

- `src/harness/pev/parser.py` — **STUB**: `parse_steps()` returns `[]`, `parse()` returns empty Recipe object
- `src/harness/pev/executor.py` — exists but not wired to parser
- `src/harness/pev/verifier.py` — exists but not wired to parser
- `src/harness/pev/planner.py` — exists but disconnected
- No recipe directory or format standard exists

---

## 2. Architecture Decisions

### Recipe Format
Standard Markdown with YAML frontmatter for metadata + `## Steps` sections for executable instructions.

### Parser Strategy
- **Phase B5.1:** Build real Markdown → Step list parser
- **Phase B5.2:** Wire planner → executor → verifier loop
- **Phase B5.3:** NLU integration (intent classification routes BUILD/FIX/DEPLOY to PEV)
- **Phase B5.4:** Full pipeline tests with mocked LLM

### Files to Create
| File | Purpose |
|------|---------|
| `src/harness/pev/recipes/__init__.py` | Package init |
| `src/harness/pev/recipes/hello-world.md` | First real recipe |
| `src/harness/pev/recipes/__template__.md` | Recipe authoring template |
| `docs/pev-recipes.md` | Authoring guide |

### Files to Modify
- `src/harness/pev/parser.py` — replace stub with real implementation
- `src/harness/pev/executor.py` — wire to parser output

---

## 3. Acceptance Criteria for B5

1. `parse("## Goal\nBuild X\n## Steps\n1. Do Y")` → 1 step with description "Do"
2. Full pipeline with mocked LLM: `run_goal("build a hello world app")` → executes steps, returns results
3. Existing PEV tests still pass
4. At least 1 real recipe in `recipes/` directory
5. Recipe format documented in `docs/pev-recipes.md`

---

## 4. Risks

- **HIGH:** Stub → production; LLM-dependent pipeline
- **MEDIUM:** Parser format changes affect downstream executor/verifier
- **LOW:** New recipe files are additive only

---

## 5. Constraint Preserved

`claude-opus-4-8` alias mapping — no changes to routing or model config this phase.

---

## Unresolved Questions

1. Should parser support multiple recipe formats (YAML frontmatter only, YAML + body, pure Markdown)?
2. Should recipe execution be retried on failure (MAX_RETRIES_PER_STEP=5 per original spec)?

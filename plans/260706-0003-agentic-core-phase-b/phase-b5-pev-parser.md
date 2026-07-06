# Phase B5: PEV Parser Real Implementation (Steps 15-18)

## Goal
Replace stub parser with real Markdown recipe → executable pipeline.

## Current State
- `harness/pev/parser.py` — STUB: `parse_steps()` returns `[]`, `parse()` returns empty Recipe
- `harness/pev/planner.py` — exists, needs wire-up
- `harness/pev/executor.py` — exists, needs wire-up
- `harness/pev/verifier.py` — exists, needs wire-up

## Implementation
1. **Build recipe parser** — Markdown → list[Step]:
   - Parse `## Goal`, `## Steps`, `## Verification` sections
   - Each step: `{id, description, expected_output, dependencies}`
   - Support inline `$var` substitution
2. **Wire planner → executor → verifier loop:**
   - Planner: decompose goal into steps (LLM-assisted)
   - Executor: run steps with MAX_RETRIES_PER_STEP=5
   - Verifier: check outputs against expected_output
3. **Integration with NLU** — pre-classify intent, route to PEV if BUILD/FIX/DEPLOY
4. **Tests for full pipeline** — mock LLM, verify: plan → execute → verify flow

## Verification
- `parse("## Goal\nBuild X\n## Steps\n1. Do Y")` → 1 step with description "Do Y"
- Full pipeline with mocked LLM: `run_goal("build a hello world app")` → executes steps, returns results
- Existing PEV tests pass

## Risk: HIGH (stub → production, LLM-dependent)

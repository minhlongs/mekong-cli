---
status: pending
track: 25-step-ideation
phase: B
steps: 11-18
title: Phase B Close-Out (B4) + B5 Kickoff (PEV Parser Real)
created: 2026-07-06
---

# Plan: Phase B4 Close-Out + B5 Kickoff

## Selected Approach (Option B — End-to-End Cooking)

### Scope Decision (Q1: End-to-End)
- **B4:** Completion write-up (report + journal + git commit)
- **B5:** Kickoff — real parser implementation scaffold

### Lint Gate (Q2: Advisory)
- ruff results reported in completion log
- NOT a hard-stop for commit; surfaced to user before finalize

### Tracking (Q3: Separate Report File)
- `reports/b4-completion-report.md` — link from plan.md
- `plan.md` updated with B4=done, B5=in_progress

---

## Tracks

| Track | Owner | Work |
|-------|-------|------|
| T1 | docs-manager | `reports/b4-completion-report.md` — artifacts, decisions, metrics |
| T2 | docs-manager | `reports/b5-kickoff-report.md` — architecture decisions, scope |
| T3 | fullstack-dev | `plan.md` update — B4 status, B5 status |
| T4 | research | B5 implementation scaffold — `src/harness/pev/recipes/` + docs |
| T5 | tester | Full Phase B test run — capture before/after |

---

## Acceptance Criteria

1. `reports/b4-completion-report.md` exists with quality gate results
2. `reports/b5-kickoff-report.md` documents architecture decisions for B5
3. `plan.md` reflects B4=done, B5=in_progress
4. `src/harness/pev/recipes/` stubbed with empty real recipe + first stub recipe
5. `docs/pev-recipes.md` documents recipe format and authoring
6. `pytest tests/core/test_memory_bridge_integration.py` still passes (72/72 green)
7. Journal entry written for Phase B4 close-out

---

## Dependencies

- T1, T2, T3, T5 → independent, can run in parallel
- T4 depends on T2 (architecture confirmed → implement scaffold)
- T5 runs last, after T1-T4

---

## Risks

- **LOW:** T1-T3 are documentation/planning only, no runtime impact
- **MEDIUM:** T5 test run may surface pre-existing B5+B6+B7 failures (expected; log only)
- **LOW:** T4 scaffold is additive only (new files, no changes to existing)

---

## Phase Files

- [reports/b4-completion-report.md](reports/b4-completion-report.md)
- [reports/b5-kickoff-report.md](reports/b5-kickoff-report.md)

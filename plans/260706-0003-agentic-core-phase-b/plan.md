---
status: in_progress
track: 25-step-ideation
phase: B
steps: 6-25
title: Phase B — Agentic Core
waves: 7
created: 2026-07-06
updated: 2026-07-06
---

# Phase B Plan: Agentic Core (Steps 6-25)

## Status

`in_progress` — B4 complete, B5 scaffolded, B6-B7 pending

## Waves

| Wave | Name | Steps | File | Risk | Status |
|------|------|-------|------|------|--------|
| B1 | Dead Code Scrub | 6-7 | phase-b1-scrub-dead-code.md | LOW | pending |
| B2 | Usage Tracker Merge | 8 | phase-b2-merge-usage-tracker.md | MEDIUM | pending |
| B3 | NLU Unification | 9-10 | phase-b3-nlu-unification.md | LOW | pending |
| B4 | Memory Bridge | 11-14 | phase-b4-memory-bridge.md | HIGH | **done** |
| B5 | PEV Parser Real | 15-18 | phase-b5-pev-parser.md | HIGH | **scaffolded** |
| B6 | Agent Factory | 19-23 | phase-b6-agent-factory.md | HIGH | pending |
| B7 | Integration + Validation | 24-25 | phase-b7-integration.md | MEDIUM | pending |

## Dependencies

- B1 → B2 → B3 can run in parallel (independent cleanups)
- B4 depends on B3 (NLU unified before memory bridge)
- B5 depends on B3 (NLU for intent classification)
- B6 depends on B4, B5 (factory needs memory + parser)
- B7 depends on B6 (integration needs factory)

## Acceptance Criteria

1. `pytest tests/seed/` → 0 failures (hold from Phase A)
2. `pytest tests/test_pev_*.py` → all pass
3. `pytest tests/test_pipeline_manager.py` → pass
4. No dead files in `src/zenpay/`, `src/metering/`, `src/core/pev_*`
5. Single usage tracker: `from src.usage import track_usage`
6. End-to-end: goal → CEO plan → Developer exec → Tester verify → memory persist

## Phase Files

- [phase-b1-scrub-dead-code.md](phase-b1-scrub-dead-code.md)
- [phase-b2-merge-usage-tracker.md](phase-b2-merge-usage-tracker.md)
- [phase-b3-nlu-unification.md](phase-b3-nlu-unification.md)
- [phase-b4-memory-bridge.md](phase-b4-memory-bridge.md)
- [phase-b5-pev-parser.md](phase-b5-pev-parser.md)
- [phase-b6-agent-factory.md](phase-b6-agent-factory.md)
- [phase-b7-integration.md](phase-b7-integration.md)

## Completion Reports

- [reports/completion-260706-1021-phase-b4-closeout-report.md](reports/completion-260706-1021-phase-b4-closeout-report.md)
- [reports/kickoff-260706-1021-phase-b5-pev-parser-real.md](reports/kickoff-260706-1021-phase-b5-pev-parser-real.md)

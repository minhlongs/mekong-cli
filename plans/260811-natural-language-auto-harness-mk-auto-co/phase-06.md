# Phase 06 — 01.06

**Date:** 260811 · **Status:** pending

## Task
Write tests: intent classifier fixtures (20 cases covering task_types, danger_levels, confidence thresholds). Graph tests: DAG execution, resume from checkpoint, rollback on failure, budget limits, parallel node execution.

## Files

- tests/test_router.py
- tests/test_graph.py
- tests/fixtures/intent_fixtures.json

## Acceptance criteria

pytest passes 100%: 20 intent fixtures, 15 graph tests (DAG, resume, rollback, budget, parallel); coverage ≥90% on core/router.py and core/graph.py

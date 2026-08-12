# Phase 01 — 01.01

**Date:** 260811 · **Status:** pending

## Task
Implement intent classifier using Claude Haiku with JSON-strict output. Extract task_type, skill_hint, target_agent, danger_level, confidence. Apply HITL gate when confidence < 0.7. Add structured prompt template and response validation.

## Files

- core/router.py

## Acceptance criteria

router.classify('deploy to production') returns JSON with all 5 fields; confidence < 0.7 raises HitlGate exception; unit tests pass with 10 fixtures covering each task_type

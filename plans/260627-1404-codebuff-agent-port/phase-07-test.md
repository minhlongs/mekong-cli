---
phase: 7
title: "Test"
status: pending
priority: P2
dependencies: [6]
---

# Phase 7: Test

## Overview
Comprehensive testing of all new components: agent schema, tool restriction, event SDK, pipeline stages, and integration.

## Requirements
- Unit tests for each new module
- Integration tests for pipeline composition
- Backward compatibility tests (existing agents unchanged)
- Event streaming tests (SDK client)

## Implementation Steps
1. Unit tests: AgentBase new fields, ToolRegistry filtering, schema validation
2. Integration tests: full pipeline run (FilePicker → Planner → Editor → Reviewer)
3. Backward compat tests: existing agents register and run without changes
4. SDK tests: event streaming, RunState serialization
5. Run full test suite: `python3 -m pytest tests/` + `pnpm test` for TS packages

## Success Criteria
- [ ] All new unit tests pass
- [ ] All existing tests pass (no regressions)
- [ ] Integration test covers full pipeline flow
- [ ] SDK package tests pass (type check + unit)
- [ ] Coverage ≥ 80% for new code

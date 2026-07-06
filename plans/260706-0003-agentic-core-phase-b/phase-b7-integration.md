# Phase B7: Integration + Validation (Steps 24-25)

## Goal
End-to-end AGI loop test + full green suite.

## Integration Test Scenario
```
Input:  "Build a hello world Python script"
Flow:   NLU classify → BUILD intent
        → AgentFactory creates CEO + Developer + Tester
        → CEO.create_plan() → ["write file", "verify syntax"]
        → Developer.execute_plan() → writes hello.py
        → Tester.verify() → checks output
        → MemoryBridge.remember() → persists execution record
Output: {task, plan, outputs, test_result, memory_id}
```

## Validation Checklist
- [ ] `pytest tests/seed/` → 0 failures (hold from Phase A)
- [ ] `pytest tests/test_pev_*.py` → all pass
- [ ] `pytest tests/test_pipeline_manager.py` → pass
- [ ] `pytest tests/test_planner.py` → pass
- [ ] No dead files: `src/zenpay/`, `src/metering/`, `src/core/pev_*`
- [ ] Single usage import: `from src.usage import track_usage`
- [ ] Memory bridge: all 7 modules use `MemoryBridge` interface
- [ ] Agent factory: all agents creatable from config
- [ ] Full E2E: goal → plan → execute → verify → memory
- [ ] `pytest tests/` → 0 regressions (full suite green)

## Risk: MEDIUM (E2E integration, multiple systems)

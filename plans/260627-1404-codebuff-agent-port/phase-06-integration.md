---
phase: 6
title: "Integration"
status: pending
priority: P2
dependencies: [5]
---

# Phase 6: Integration — Wire Everything Together

## Overview
Connect the new agent schema, tool restriction, event SDK, and pipeline stages into a cohesive system. Ensure backward compatibility — existing agents and workflows must work without modification.

## Requirements
- AgentBase extensions don't break existing agent subclasses
- Tool restriction is opt-in (empty allowedTools = all tools)
- Event SDK hooks into RecipeExecutor without changing its public API
- Pipeline stages compose into PEV without replacing it
- CLI commands can invoke the new pipeline via existing `mekong` entry points

## Architecture
```
CLI: mekong cook <goal>
  → HybridRouter (unchanged)
    → RecipePlanner (optionally uses FilePicker)
      → RecipeExecutor (optionally uses EditorAgent + emits events)
        → RecipeVerifier (optionally uses ReviewerAgent)
          → Event stream to SDK consumer (if connected)
```

## Related Code Files
- Modify: `src/core/orchestrator.py` — wire pipeline stages into PEV loop
- Modify: `src/core/hybrid_router.py` — pass event emitter through to executor
- Modify: `cli/` — add `--pipeline` flag to enable specialized stages
- Modify: `packages/` root package.json — add agent-sdk workspace entry

## Implementation Steps
1. Wire event emitter from RecipeExecutor → HybridRouter → CLI output
2. Add `--pipeline` CLI flag to enable/disable specialized stages
3. Ensure AgentBase.__init__ handles missing new fields gracefully
4. Run full test suite, fix any regressions
5. Update CLAUDE.md namespace section if new public paths added

## Success Criteria
- [ ] `mekong cook "task"` works unchanged (backward compat)
- [ ] `mekong cook "task" --pipeline` uses specialized stages
- [ ] Event stream visible in CLI output when SDK connected
- [ ] All 5,713 existing tests pass
- [ ] No breaking changes to public APIs

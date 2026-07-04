---
phase: 5
title: "Pipeline Stages"
status: pending
priority: P2
dependencies: [3, 4]
---

# Phase 5: Pipeline Stages — Specialized Agents Within PEV

## Overview
Add 4 specialized pipeline stages (FilePicker → Planner → Editor → Reviewer) as optional sub-steps within mekong-cli's existing PEV loop. Each stage is a specialized agent configuration, not a new agent class.

## Requirements
- FilePicker: scans codebase, surfaces relevant files (uses `read_files`, `glob`, `code_search`)
- Planner: determines modification order (uses `think_deeply`, `write_todos`)
- Editor: performs precise code edits (uses `write_file`, `str_replace`, `run_terminal_command`)
- Reviewer: validates changes, checks regressions (uses `code_search`, `read_files`)
- Stages compose into PEV: Plan phase uses FilePicker+Planner, Execute uses Editor, Verify uses Reviewer

## Architecture
```
PEV Loop (existing)
├── Plan (RecipePlanner)
│   ├── Stage 1: FilePickerAgent (optional pre-step)
│   └── Stage 2: PlannerAgent (existing, enhanced)
├── Execute (RecipeExecutor)
│   └── Stage 3: EditorAgent (optional specialized executor)
└── Verify (RecipeVerifier)
    └── Stage 4: ReviewerAgent (optional post-step)
```

## Related Code Files
- Create: `src/core/pipeline_stages.py` — stage definitions and composition
- Create: `src/agents/file_picker_agent.py` — file-picker specialization
- Create: `src/agents/editor_agent.py` — editor specialization
- Create: `src/agents/reviewer_agent.py` — reviewer specialization
- Modify: `src/core/planner.py` — accept optional FilePicker pre-step
- Modify: `src/core/verifier.py` — accept optional Reviewer post-step

## Implementation Steps
1. Define pipeline stage configs (tool restrictions, prompts, model preferences)
2. Create specialized agent subclasses inheriting AgentBase
3. Wire FilePicker into RecipePlanner as optional pre-processing step
4. Wire Reviewer into RecipeVerifier as optional post-validation step
5. Add pipeline composition helper (`compose_pipeline(stages)`)
6. Write integration tests for full pipeline flow

## Success Criteria
- [ ] FilePicker surfaces relevant files for a given task
- [ ] Editor makes precise edits using restricted tool set
- [ ] Reviewer catches regressions after edits
- [ ] Pipeline stages are optional (opt-in via config)
- [ ] Existing PEV loop works unchanged when stages disabled

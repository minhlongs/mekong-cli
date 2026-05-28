---
name: "source-command-cook-auto"
description: "Durable autonomous goal runner — create, execute, checkpoint, and verify a persisted goal."
---

# source-command-cook-auto

Use this skill when the user asks to run the migrated source command
`cook-auto`.

## Command Template

# /cook-auto — Durable Autonomous Goal Runner

Create a persisted goal, run its task graph, record checkpoints/events/memory,
and verify the final state through the autonomous goal engine.

## Execution

```bash
mekong cook-auto "$ARGUMENTS" --profile smoke --auto
```

## Pipeline

```
SEQUENTIAL:
  ├── goal-create             → persisted goal + task graph
  ├── task-execution          → completed ready tasks + checkpoints
  └── verification            → persisted verification run
```

## Output

Final goal id, status, task completion count, verification run count,
`verification_passed`, `failed_gates`, `status_command`, `resume_command`,
`verify_command`, `status_json_command`, `resume_json_command`, and
`verify_json_command`. A non-`satisfied` final status exits nonzero, while the
goal remains persisted for inspection and retry. `--auto` is accepted for
AGY/slash-command compatibility.

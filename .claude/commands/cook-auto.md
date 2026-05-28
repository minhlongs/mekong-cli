---
description: "Durable autonomous goal runner — create, execute, checkpoint, and verify a persisted goal."
argument-hint: [goal description]
allowed-tools: Read, Write, Bash, Task
---

# /cook-auto — Durable Autonomous Goal Runner

Create a persisted goal, run its task graph, record checkpoints/events/memory,
and verify the final state through the autonomous goal engine.

## Execution

```bash
mekong cook-auto "$ARGUMENTS" --profile smoke --auto
```

## Options

- `--profile standard` runs the full blocking verification profile.
- `--profile smoke` runs fast CLI import proof.
- `--profile none` is reserved for tests and controlled dry integration.
- `--execute-commands` permits task commands when they are present.
- `--auto` is accepted for AGY/slash-command compatibility; execution is already non-interactive.
- Unknown profiles are rejected before a goal is created.

## Output

The command returns a final goal id, status, task completion count,
verification run count, `verification_passed`, `failed_gates`,
`status_command`, `resume_command`, `verify_command`, `status_json_command`,
`resume_json_command`, and `verify_json_command`. A non-`satisfied` final
status exits nonzero, while the goal remains persisted for inspection and
retry. `--auto` is accepted for AGY/slash-command compatibility.

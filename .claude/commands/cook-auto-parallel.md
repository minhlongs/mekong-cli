---
description: "Durable parallel autonomous goal runner — create, execute independent tasks in parallel, checkpoint, and verify a persisted goal."
argument-hint: [goal description]
allowed-tools: Read, Write, Bash, Task
---

# /cook-auto-parallel — Durable Parallel Autonomous Goal Runner

Create a persisted goal, run its task graph in parallel (max 3 concurrent worker threads), record checkpoints/events/memory,
and verify the final state through the autonomous goal engine.

## Execution

```bash
python3 -m src.main cook-auto-parallel "$ARGUMENTS" --profile smoke --auto
```

## Options

- `--profile standard` runs the full blocking verification profile.
- `--profile smoke` runs fast CLI import proof.
- `--profile none` is reserved for tests and controlled dry integration.
- `--execute-commands` permits task commands when they are present.
- `--workers <count>` sets the concurrency ceiling (default is 3).
- `--auto` is accepted for compatibility; execution is already non-interactive.

## Output

The command returns a final goal id, status, task completion count,
verification run count, `verification_passed`, `failed_gates`,
`status_command`, `resume_command`, `verify_command`, `status_json_command`,
`resume_json_command`, and `verify_json_command`.

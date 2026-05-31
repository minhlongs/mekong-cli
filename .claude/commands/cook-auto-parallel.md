---
description: "Durable parallel autonomous goal runner — create, execute independent tasks in parallel, checkpoint, and verify a persisted goal."
argument-hint: [goal description]
allowed-tools: Read, Write, Bash, Task
---

# /cook-auto-parallel — Durable Parallel Autonomous Goal Runner

Create a persisted goal with parallel task execution. Run independent tasks concurrently, record checkpoints/events/memory, and verify the final state through the autonomous goal engine.

## Execution
```bash
python3 -m src.main cook-auto-parallel "$ARGUMENTS" --profile smoke --auto
```

## Options
- `--profile standard` runs the full blocking verification profile.
- `--profile smoke` runs fast CLI import proof.
- `--profile none` is reserved for tests and controlled dry integration.
- `--execute-commands` permits task commands when they are present.
- `--auto` is accepted for AGY/slash-command compatibility; execution is already non-interactive.
- Unknown profiles are rejected before a goal is created.

## Output
Returns goal id, status, task completion count, verification run count, `verification_passed`, `failed_gates`, and resume/verify commands. A non-`satisfied` final status exits nonzero.

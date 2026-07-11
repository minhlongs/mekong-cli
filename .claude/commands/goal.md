---
description: "Goal: persistent autonomous mission execution with ultracode orchestration"
argument-hint: "[subcommand] [args...]"
allowed-tools: Bash
---

# /goal — Persistent Autonomous Mission Execution

Run goal engine commands for mission execution with AI orchestration.

## Execution

```bash
python3 -m src.main goal $ARGUMENTS
```

## Subcommands

| Subcommand | Purpose |
|------------|---------|
| `create <title>` | Create a new mission goal |
| `run <goal-id>` | Execute a goal with AI orchestration |
| `run-parallel <goal-id>` | Execute goal steps in parallel |
| `resume <goal-id>` | Resume paused goal |
| `verify <goal-id>` | Verify goal completion |
| `status [goal-id]` | Show goal status |
| `list` | List all goals |
| `cancel <goal-id>` | Cancel running goal |
| `get <goal-id>` | Get goal details |

## Ultracode Mode

When invoked with `ultracode` flag, the engine auto-spawns subagents for:
- Research phases → researcher agents
- Implementation → fullstack-developer agents
- Testing → tester agents
- Review → code-reviewer agents

Example:
- `/goal create "Build auth system"`
- `/goal run abc123 --auto --deep --parallel`

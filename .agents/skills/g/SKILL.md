---
name: g
description: >-
  Goal alias: persistent autonomous mission execution with ultracode orchestration
---

# /g — Persistent Autonomous Mission Execution (Alias for /goal)

Run goal engine commands for mission execution with AI orchestration.

## Execution

```bash
mekong g $ARGUMENTS
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
- `/g create "Build auth system"`
- `/g run abc123 --auto --deep --parallel`

description: "SDD implementation runner -- mekong implement run <feature>"
argument-hint: "<feature-slug> [--agent <agent-name>]"
---
Execute implementation for a feature using prior SDD task context.

Runs `mekong implement run` which dispatches to an agent with spec and task context loaded. By default uses `fullstack-developer` agent.

**Options:**
- `--agent` — agent to dispatch (default: fullstack-developer)

Loads context from: `SPEC.md` → `plan.md` → `tasks.md` in the feature output directory.

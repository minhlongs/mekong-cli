---
name: mk-plan
description: >-
  Plan implementations via Mekong CLI. Optionally request Sun Tzu strategist review before committing to an approach.
---

# /mk:plan — Mekong plan bridge

Default: delegate to `mekong plan`.

Optional strategist mode:
- `--sun-tzu` — before committing to the plan approach, spawn Sun Tzu
  for review of architecture / tech-stack trade-offs.

## Execution

\`\`\`bash
mekong plan $ARGUMENTS
\`\`\`

## Sun Tzu escalation

When `--sun-tzu` is in \`$ARGUMENTS\`:

1. Run the normal Mekong plan first
2. Then spawn Sun Tzu with the plan summary and the original task as prompt
3. Append Sun Tzu's counsel as a note in the plan output before returning to the user

Sun Tzu invocation example:

\`\`\`bash
Task(
  subagent_type="sun-tzu",
  prompt="Review this plan for architectural risks and trade-offs:\n\n${ARGUMENTS}",
  description="Sun Tzu plan review"
)
\`\`\`

## Usage

```bash
// turbo
mekong mk plan $ARGUMENTS
```

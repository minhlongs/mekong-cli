---
name: mk-cook
description: >-
  Implement via Mekong cook workflow. Supports Sun Tzu strategist gate before high-risk implementation.
---

# /mk:cook — Mekong cook bridge

Delegates to Mekong CLI cook workflow.

New optional gate:
- `--sun-tzu` — pause before implementation and ask Sun Tzu to review
  the plan / approach for risks, missing acceptance criteria, or better alternatives.

## Execution

\`\`\`bash
mekong cook $ARGUMENTS
\`\`\`

## Sun Tzu gate behavior

If `--sun-tzu` is present:

1. Load the plan being cooked
2. Spawn Sun Tzu with: "Review this implementation plan. Surface risks,
   missing acceptance criteria, and alternative approaches before we code."
3. Present Sun Tzu's counsel to the user
4. On user confirmation, continue with the actual `mekong cook` run

Sun Tzu invocation:

\`\`\`bash
Task(
  subagent_type="sun-tzu",
  prompt="Review implementation plan:\n\n<plan content>\n\nTask: ${ARGUMENTS}",
  description="Sun Tzu pre-cook review"
)
\`\`\`

Confirm to the caller that `/mk:cook` routes through `mekong cook` with an optional Sun Tzu review gate.

## Usage

```bash
// turbo
mekong mk cook $ARGUMENTS
```

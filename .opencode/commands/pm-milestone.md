---
description: "Milestone tracking and status. 2 credits, ~5 min."
argument-hint: [task or context]
allowed-tools: Read, Write, Bash, Task
---

# /pm:milestone — Milestone Tracking

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:milestone → dev:* → worker:*
OUTPUT: reports/pm/milestone/
```

## Estimated: 2 credits, ~5 minutes

## Execution

Load recipe: `recipes/pm/milestone.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

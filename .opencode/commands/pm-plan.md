---
description: "Create implementation plan with phases. 5 credits, ~15 min."
argument-hint: [task or context]
allowed-tools: Read, Write, Bash, Task
---

# /pm:plan — Implementation Plan

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:plan → dev:* → worker:*
OUTPUT: reports/pm/plan/
```

## Estimated: 5 credits, ~15 minutes

## Execution

Load recipe: `recipes/pm/plan.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

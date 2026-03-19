---
description: "Break task and delegate to dev level. 3 credits, ~10 min."
argument-hint: [task or context]
allowed-tools: Read, Write, Bash, Task
---

# /pm:delegate — Task Delegation

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:delegate → dev:* → worker:*
OUTPUT: reports/pm/delegate/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/pm/delegate.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

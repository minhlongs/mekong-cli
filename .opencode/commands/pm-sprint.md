---
description: "Sprint planning — backlog to sprint tasks. 3 credits, ~15 min."
argument-hint: [task or context]
allowed-tools: Read, Write, Bash, Task
---

# /pm:sprint — Sprint Planning

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:sprint → dev:* → worker:*
OUTPUT: reports/pm/sprint/
```

## Estimated: 3 credits, ~15 minutes

## Execution

Load recipe: `recipes/pm/sprint.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

---
description: "Daily standup report. 1 credit, ~5 min."
argument-hint: [task or context]
allowed-tools: Read, Write, Bash, Task
---

# /pm:standup — Daily Standup

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:standup → dev:* → worker:*
OUTPUT: reports/pm/standup/
```

## Estimated: 1 credits, ~5 minutes

## Execution

Load recipe: `recipes/pm/standup.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

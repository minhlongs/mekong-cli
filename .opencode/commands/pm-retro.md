---
description: "Sprint retrospective. 3 credits, ~10 min."
argument-hint: [task or context]
allowed-tools: Read, Write, Bash, Task
---

# /pm:retro — Retrospective

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:retro → dev:* → worker:*
OUTPUT: reports/pm/retro/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/pm/retro.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

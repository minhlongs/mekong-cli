---
description: "Set/review OKRs and key results. 3 credits, ~10 min."
argument-hint: [task or context]
allowed-tools: Read, Write, Bash, Task
---

# /pm:okr — OKR Review

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:okr → dev:* → worker:*
OUTPUT: reports/pm/okr/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/pm/okr.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

---
description: "Add new project to portfolio. 8 credits, ~30 min."
argument-hint: [context or goal]
allowed-tools: Read, Write, Bash, Task
---

# /studio:invest — New Investment

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:invest → cto:* → dev:* → worker:*
OUTPUT: reports/studio/invest/
```

## Estimated: 8 credits, ~30 minutes

## Execution

Load recipe: `recipes/studio/invest.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

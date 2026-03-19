---
description: "Archive/sunset a portfolio project. 5 credits, ~15 min."
argument-hint: [context or goal]
allowed-tools: Read, Write, Bash, Task
---

# /studio:divest — Project Divestment

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:divest → cto:* → dev:* → worker:*
OUTPUT: reports/studio/divest/
```

## Estimated: 5 credits, ~15 minutes

## Execution

Load recipe: `recipes/studio/divest.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

---
description: "Generate investor report (weekly/monthly). 5 credits, ~20 min."
argument-hint: [context or goal]
allowed-tools: Read, Write, Bash, Task
---

# /studio:report — Investor Report

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:report → cto:* → dev:* → worker:*
OUTPUT: reports/studio/report/
```

## Estimated: 5 credits, ~20 minutes

## Execution

Load recipe: `recipes/studio/report.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

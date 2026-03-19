---
description: "Full portfolio ROI audit across all projects. Delegates cto:review per project. 10 credits, ~60 min."
argument-hint: [context or goal]
allowed-tools: Read, Write, Bash, Task
---

# /studio:audit — Portfolio Audit

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:audit → cto:* → dev:* → worker:*
OUTPUT: reports/studio/audit/
```

## Estimated: 10 credits, ~60 minutes

## Execution

Load recipe: `recipes/studio/audit.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

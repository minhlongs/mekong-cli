---
description: "ROI scorecard across all projects. 3 credits, ~10 min."
argument-hint: [context or goal]
allowed-tools: Read, Write, Bash, Task
---

# /studio:roi — ROI Scorecard

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:roi → cto:* → dev:* → worker:*
OUTPUT: reports/studio/roi/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/studio/roi.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

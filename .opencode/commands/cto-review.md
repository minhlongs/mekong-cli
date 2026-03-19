---
description: "Full project health review. 5 credits, ~20 min."
argument-hint: [project or context]
allowed-tools: Read, Write, Bash, Task
---

# /cto:review — Project Health Review

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:review → pm:* / dev:* → worker:*
OUTPUT: reports/cto/review/
```

## Estimated: 5 credits, ~20 minutes

## Execution

Load recipe: `recipes/cto/review.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

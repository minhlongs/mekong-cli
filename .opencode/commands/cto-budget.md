---
description: "MCU budget allocation within project. 3 credits, ~10 min."
argument-hint: [project or context]
allowed-tools: Read, Write, Bash, Task
---

# /cto:budget — Budget Allocation

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:budget → pm:* / dev:* → worker:*
OUTPUT: reports/cto/budget/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/cto/budget.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

---
description: "Architecture decision record (ADR). 5 credits, ~15 min."
argument-hint: [project or context]
allowed-tools: Read, Write, Bash, Task
---

# /cto:architect — Architecture Decision

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:architect → pm:* / dev:* → worker:*
OUTPUT: reports/cto/architect/
```

## Estimated: 5 credits, ~15 minutes

## Execution

Load recipe: `recipes/cto/architect.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

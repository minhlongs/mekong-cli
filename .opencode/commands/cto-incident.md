---
description: "Incident response orchestration. 8 credits, ~20 min."
argument-hint: [project or context]
allowed-tools: Read, Write, Bash, Task
---

# /cto:incident — Incident Response

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:incident → pm:* / dev:* → worker:*
OUTPUT: reports/cto/incident/
```

## Estimated: 8 credits, ~20 minutes

## Execution

Load recipe: `recipes/cto/incident.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

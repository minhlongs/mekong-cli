---
description: "Production deployment decision + execution. 5 credits, ~15 min."
argument-hint: [project or context]
allowed-tools: Read, Write, Bash, Task
---

# /cto:deploy — Production Deploy

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:deploy → pm:* / dev:* → worker:*
OUTPUT: reports/cto/deploy/
```

## Estimated: 5 credits, ~15 minutes

## Execution

Load recipe: `recipes/cto/deploy.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

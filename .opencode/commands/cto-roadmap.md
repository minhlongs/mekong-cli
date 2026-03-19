---
description: "Technical roadmap generation. 5 credits, ~20 min."
argument-hint: [project or context]
allowed-tools: Read, Write, Bash, Task
---

# /cto:roadmap — Technical Roadmap

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:roadmap → pm:* / dev:* → worker:*
OUTPUT: reports/cto/roadmap/
```

## Estimated: 5 credits, ~20 minutes

## Execution

Load recipe: `recipes/cto/roadmap.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

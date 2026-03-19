---
description: "Onboard new project to OpenClaw. 8 credits, ~30 min."
argument-hint: [project or context]
allowed-tools: Read, Write, Bash, Task
---

# /cto:onboard — Project Onboarding

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:onboard → pm:* / dev:* → worker:*
OUTPUT: reports/cto/onboard/
```

## Estimated: 8 credits, ~30 minutes

## Execution

Load recipe: `recipes/cto/onboard.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

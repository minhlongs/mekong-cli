---
description: "Strategic planning session. 8 credits, ~30 min."
argument-hint: [context or goal]
allowed-tools: Read, Write, Bash, Task
---

# /studio:strategy — Strategic Planning

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:strategy → cto:* → dev:* → worker:*
OUTPUT: reports/studio/strategy/
```

## Estimated: 8 credits, ~30 minutes

## Execution

Load recipe: `recipes/studio/strategy.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

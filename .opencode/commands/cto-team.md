---
description: "Team capacity planning and task routing. 3 credits, ~10 min."
argument-hint: [project or context]
allowed-tools: Read, Write, Bash, Task
---

# /cto:team — Team Planning

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:team → pm:* / dev:* → worker:*
OUTPUT: reports/cto/team/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/cto/team.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$INPUT</goal>

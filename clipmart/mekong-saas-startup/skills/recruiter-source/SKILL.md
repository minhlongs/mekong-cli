---
name: recruiter-source
description: "Job requirements, candidate search, outreach. 2 commands, ~10 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Job requirements, candidate search, outreach. 2 commands, ~10 min."
argument-hint: [role or job description]
allowed-tools: Read, Write, Bash, Task
---

# /recruiter:source — Candidate Sourcing

**IC super command** — chains 2 commands via DAG pipeline.

## Pipeline

```
[process] ─────────────────────────────────────── SEQUENTIAL
  ├── leadgen --talent         → candidate-list.md
  └── email --recruit          → outreach-sent.md
```

## Estimated: 5 credits, 10 minutes

## Execution

Load recipe: `recipes/recruiter/source.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

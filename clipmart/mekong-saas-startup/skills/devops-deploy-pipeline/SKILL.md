---
name: devops-deploy-pipeline
description: "Lint → test → build → staging → smoke → production deployment pipeline"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Lint → test → build → staging → smoke → production deployment pipeline"
argument-hint: [service or tag to deploy]
allowed-tools: Read, Write, Bash, Task
---

# /devops:deploy-pipeline — Deployment Pipeline

**Super command** — chains 6 commands via DAG pipeline.

## Pipeline

```
[lint] ══╗
[typecheck] ╣ (parallel)
[test --all] ╝
              ▼
     [deploy-staging]
              │
              ▼
          [smoke]
              │
              ▼
       [deploy-prod]
```

## Estimated: 18 credits, 30 minutes

## Execution

Load recipe: `recipes/devops/deploy-pipeline.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

---
name: audit-plan
description: "Risk-based audit planning"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Risk-based audit planning"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /audit:plan — Audit Planning

**IC super command** — Risk-based audit planning

## Pipeline

```
SEQUENTIAL: risk-rank → select-audits → allocate-resources
    |
OUTPUT: reports/audit/plan/
```

## Trigger

Runs recipe `recipes/audit/plan.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/audit:plan [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

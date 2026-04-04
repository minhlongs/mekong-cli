---
name: iam-rbac
description: "Role-based access control matrix management"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Role-based access control matrix management"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /iam:rbac — RBAC Management

**IC super command** — Role-based access control matrix management

## Pipeline

```
SEQUENTIAL: extract-roles → analyze-coverage → update-matrix
    |
OUTPUT: reports/iam/rbac/
```

## Trigger

Runs recipe `recipes/iam/rbac.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/iam:rbac [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

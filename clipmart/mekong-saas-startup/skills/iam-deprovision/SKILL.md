---
name: iam-deprovision
description: "Immediate access revocation on termination"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Immediate access revocation on termination"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /iam:deprovision — Access Revocation

**IC super command** — Immediate access revocation on termination

## Pipeline

```
SEQUENTIAL: revoke-all-access → archive-data → generate-evidence
    |
OUTPUT: reports/iam/deprovision/
```

## Trigger

Runs recipe `recipes/iam/deprovision.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/iam:deprovision [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

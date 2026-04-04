---
name: sec-policy
description: "Policy-as-code enforcement"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /sec:policy — Policy Enforcement

**IC super command** — Policy-as-code enforcement

## Pipeline

```
SEQUENTIAL: policy-scan → drift-detect → enforce
    |
OUTPUT: reports/sec/policy/
```

## Trigger

Runs recipe `recipes/sec/policy.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:policy [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

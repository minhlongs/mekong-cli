---
name: risk-fraud-detect
description: "Anti-fraud monitoring"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Anti-fraud monitoring"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /risk:fraud-detect — Fraud Detection

**IC super command** — Anti-fraud monitoring

## Pipeline

```
SEQUENTIAL: detect-anomalies → flag-violations
    |
OUTPUT: reports/risk/fraud-detect/
```

## Trigger

Runs recipe `recipes/risk/fraud-detect.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/risk:fraud-detect [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

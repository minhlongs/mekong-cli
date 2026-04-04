---
name: sec-access-review
description: "SOX quarterly access recertification"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /sec:access-review — Access Review

**IC super command** — SOX quarterly access recertification

## Pipeline

```
SEQUENTIAL: extract-access → send-review → collect-attestation → remediate
    |
OUTPUT: reports/sec/access-review/
```

## Trigger

Runs recipe `recipes/sec/access-review.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:access-review [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

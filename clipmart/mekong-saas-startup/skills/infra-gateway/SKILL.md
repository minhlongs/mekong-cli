---
name: infra-gateway
description: "API gateway configuration — routes, auth, rate limiting"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "API gateway configuration — routes, auth, rate limiting"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /infra:gateway — API Gateway

**IC super command** — API gateway configuration — routes, auth, rate limiting

## Pipeline

```
SEQUENTIAL: scan-routes → configure-auth → set-rate-limits
```

## Trigger

Runs recipe `recipes/infra/gateway.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/infra:gateway [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

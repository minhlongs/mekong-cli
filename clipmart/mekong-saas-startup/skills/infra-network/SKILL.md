---
name: infra-network
description: "Network architecture audit — segmentation, firewall, DNS"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Network architecture audit — segmentation, firewall, DNS"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /infra:network — Network Audit

**IC super command** — Network architecture audit — segmentation, firewall, DNS

## Pipeline

```
PARALLEL: scan-firewall + scan-dns + scan-segments\nSEQUENTIAL: audit-report
```

## Trigger

Runs recipe `recipes/infra/network.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/infra:network [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

---
name: sec-soc
description: "Security operations center dashboard"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Security operations center dashboard"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:soc — SOC Dashboard

**IC super command** — Security operations center dashboard

## Pipeline

```
SEQUENTIAL: siem-ingest → correlate-alerts → threat-detect
    |
OUTPUT: reports/sec/soc/
```

## Trigger

Runs recipe `recipes/sec/soc.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:soc [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

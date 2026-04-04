---
name: sec-audit
description: "Continuous compliance monitoring (SOC2/ISO27001)"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Continuous compliance monitoring (SOC2/ISO27001)"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:audit — Compliance Audit

**IC super command** — Continuous compliance monitoring (SOC2/ISO27001)

## Pipeline

```
SEQUENTIAL: evidence-collect → gap-analyze → remediation-plan
    |
OUTPUT: reports/sec/audit/
```

## Trigger

Runs recipe `recipes/sec/audit.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:audit [goal]
```

## Estimated: 5 credits, 20 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

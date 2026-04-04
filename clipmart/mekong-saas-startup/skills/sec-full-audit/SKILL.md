---
name: sec-full-audit
description: "Complete security audit — scan, vuln, access review, compliance report"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /sec:full-audit — Full Security Audit

**Super command** — chains multiple commands via DAG pipeline.

## Pipeline

```
PARALLEL: /sec:scan + /sec:vuln + /sec:access-review
    |
SEQUENTIAL: /sec:compliance-report
    |
OUTPUT: reports/sec/full-audit/
```

## Trigger

Runs recipe `recipes/sec/full-audit.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Spawn parallel subagents via Task tool
3. Wait for all groups to complete
4. Compile into summary report

## Usage

```
/sec:full-audit [goal]
```

## Estimated: 14 credits, 25 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

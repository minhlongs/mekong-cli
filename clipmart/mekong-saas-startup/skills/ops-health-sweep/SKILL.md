---
name: ops-health-sweep
description: "System-wide health audit — services, security, performance, sync status. 5 commands, ~15 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "System-wide health audit — services, security, performance, sync status. 5 commands, ~15 min."
argument-hint: [ops context or goal]
---

# Full Health Sweep

> Trigger: `/ops:health-sweep $ARGUMENTS`
> Estimated: ~15 min

## Execution

Load recipe: `recipes/ops/health-sweep.json`

Run the DAG workflow:

### Full System Scan (parallel)
- `health`
- `security`
- `benchmark`
- `status`

### Compiled Report (sequential)
- `report`


## Instructions

1. Read recipe DAG definition
2. Execute groups in dependency order
3. Parallel groups run simultaneously
4. Write outputs to `reports/health-sweep`
5. Report completion with summary

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

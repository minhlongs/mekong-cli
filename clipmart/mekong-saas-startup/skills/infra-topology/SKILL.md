---
name: infra-topology
description: "Map infrastructure topology — services, dependencies, traffic"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Map infrastructure topology — services, dependencies, traffic"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /infra:topology — Infra Topology

**IC super command** — Map infrastructure topology — services, dependencies, traffic

## Pipeline

```
PARALLEL: scan-services + scan-deps\nSEQUENTIAL: topology-map
```

## Trigger

Runs recipe `recipes/infra/topology.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/infra:topology [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

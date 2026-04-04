---
name: gateway-key
description: "API key provisioning, rotation, and revocation"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "API key provisioning, rotation, and revocation"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /gateway:key — API Key Management
**IC super command** — API key provisioning, rotation, and revocation
## Pipeline
```
SEQUENTIAL: provision → set-scopes → monitor-usage
```
## Trigger
Runs recipe `recipes/gateway/key.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/gateway:key [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

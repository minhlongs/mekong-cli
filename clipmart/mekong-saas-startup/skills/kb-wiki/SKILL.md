---
name: kb-wiki
description: "Internal wiki creation, organization, and search"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Internal wiki creation, organization, and search"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /kb:wiki — Wiki Management
**IC super command** — Internal wiki creation, organization, and search
## Pipeline
```
SEQUENTIAL: create-page → categorize → index
```
## Trigger
Runs recipe `recipes/kb/wiki.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/kb:wiki [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*

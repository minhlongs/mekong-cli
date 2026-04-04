---
description: "Structured blameless postmortem generation"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /incident:postmortem — Postmortem Generator
**IC super command** — Structured blameless postmortem generation
## Pipeline
```
SEQUENTIAL: collect-timeline → analyze-cause → generate-doc
```
## Trigger
Runs recipe `recipes/incident/postmortem.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/incident:postmortem [goal]
```
## Estimated: 3 credits, 10 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

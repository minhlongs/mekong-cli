---
name: "source-command-ops-status"
description: "Operations status report — uptime, incidents, SLA compliance, team velocity. 2 steps, ~10 min."
---

# source-command-ops-status

Use this skill when the user asks to run the migrated source command `ops-status`.

## Command Template

# /ops:ops-status — Operations Status

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── metrics-gather          → ops-metrics.md
  └── status-report           → ops-status.md
```

## Output directory: reports/ops/ops-status/

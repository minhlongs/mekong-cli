---
description: "Operations status report — uptime, incidents, SLA compliance, team velocity. 2 steps, ~10 min."
argument-hint: [time period or team]
allowed-tools: Read, Write, Bash, Task
---

# /ops:ops-status — Operations Status

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── metrics-gather          → ops-metrics.md
  └── status-report           → ops-status.md
```

## Output directory: reports/ops/ops-status/

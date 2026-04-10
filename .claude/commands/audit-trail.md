---
description: "Audit trail extraction — event log, access history, change tracking. 2 steps, ~10 min."
argument-hint: [system or time period]
allowed-tools: Read, Write, Bash, Task
---

# /compliance:audit-trail — Audit Trail

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── event-extraction        → event-log.md
  └── trail-analysis          → audit-trail-report.md
```

## Output directory: reports/compliance/audit-trail/

---
name: "source-command-audit-trail"
description: "Audit trail extraction — event log, access history, change tracking. 2 steps, ~10 min."
---

# source-command-audit-trail

Use this skill when the user asks to run the migrated source command `audit-trail`.

## Command Template

# /compliance:audit-trail — Audit Trail

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── event-extraction        → event-log.md
  └── trail-analysis          → audit-trail-report.md
```

## Output directory: reports/compliance/audit-trail/

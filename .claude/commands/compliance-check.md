---
description: "Compliance check against framework — gap identification, risk scoring, action items. 2 steps, ~15 min."
argument-hint: [framework: GDPR / CCPA / SOX / PCI-DSS]
allowed-tools: Read, Write, Bash, Task
---

# /compliance:compliance-check — Compliance Check

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── framework-scan          → gaps.md
  └── action-plan             → compliance-actions.md
```

## Output directory: reports/compliance/compliance-check/

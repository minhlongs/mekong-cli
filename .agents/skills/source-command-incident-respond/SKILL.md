---
name: "source-command-incident-respond"
description: "Incident response — triage, investigation, mitigation, post-mortem template. 4 steps, ~20 min."
---

# source-command-incident-respond

Use this skill when the user asks to run the migrated source command `incident-respond`.

## Command Template

# /ops:incident-respond — Incident Response

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── triage                  → severity-assessment.md
  ├── investigation           → root-cause.md
  ├── mitigation              → action-plan.md
  └── post-mortem             → post-mortem.md
```

## Output directory: reports/ops/incident-respond/

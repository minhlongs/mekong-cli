---
description: "Incident response — triage, investigation, mitigation, post-mortem template. 4 steps, ~20 min."
argument-hint: [incident description or alert]
allowed-tools: Read, Write, Bash, Task
---

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

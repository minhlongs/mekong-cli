---
name: "source-command-founder-okr"
description: "Founder OKR setting — vision alignment, quarterly objectives, key results, scoring. 3 steps, ~15 min."
---

# source-command-founder-okr

Use this skill when the user asks to run the migrated source command `founder-okr`.

## Command Template

# /venture:founder-okr — Founder OKRs

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── vision-alignment        → vision.md
  ├── objective-setting       → objectives.md
  └── key-results             → okrs.md
```

## Output directory: reports/venture/founder-okr/

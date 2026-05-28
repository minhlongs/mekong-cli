---
name: "source-command-data-pipeline"
description: "Data pipeline setup — source config, transform logic, destination mapping, validation. 4 steps, ~20 min."
---

# source-command-data-pipeline

Use this skill when the user asks to run the migrated source command `data-pipeline`.

## Command Template

# /data:data-pipeline — Data Pipeline

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── source-config           → source-schema.md
  ├── transform-logic         → transforms.md
  ├── destination-mapping     → mapping.md
  └── validation-rules        → validation.md
```

## Output directory: reports/data/data-pipeline/

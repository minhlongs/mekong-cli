---
name: "source-command-data-query"
description: "Data analysis query — SQL/query generation, execution plan, result interpretation. 2 steps, ~10 min."
---

# source-command-data-query

Use this skill when the user asks to run the migrated source command `data-query`.

## Command Template

# /data:data-query — Data Query Analyst

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── query-generation        → query.sql
  └── result-interpretation   → analysis.md
```

## Output directory: reports/data/data-query/

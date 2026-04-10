---
description: "Data analysis query — SQL/query generation, execution plan, result interpretation. 2 steps, ~10 min."
argument-hint: [question about data or dataset]
allowed-tools: Read, Write, Bash, Task
---

# /data:data-query — Data Query Analyst

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── query-generation        → query.sql
  └── result-interpretation   → analysis.md
```

## Output directory: reports/data/data-query/

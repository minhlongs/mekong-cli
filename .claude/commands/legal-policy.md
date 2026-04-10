---
description: "Legal policy creation — terms of service, privacy policy, acceptable use. 3 steps, ~25 min."
argument-hint: [policy type: ToS / privacy / AUP]
allowed-tools: Read, Write, Bash, Task
---

# /legal:legal-policy — Legal Policy Draft

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── requirements-gather     → requirements.md
  ├── policy-draft            → policy-draft.md
  └── legal-review            → final-policy.md
```

## Output directory: reports/legal/legal-policy/

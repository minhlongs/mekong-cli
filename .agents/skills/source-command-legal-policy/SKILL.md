---
name: "source-command-legal-policy"
description: "Legal policy creation — terms of service, privacy policy, acceptable use. 3 steps, ~25 min."
---

# source-command-legal-policy

Use this skill when the user asks to run the migrated source command `legal-policy`.

## Command Template

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

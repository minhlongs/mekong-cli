---
description: "Cross-artifact consistency check (spec vs plan vs tasks). Detects mismatches between SDD artifacts. Read-only, zero file modifications."
argument-hint: "<feature-slug>"
allowed-tools: Bash, Read
---
# /analyze — ck:analyze

Cross-artifact consistency check for SDD workflow. Validates that spec.md, plan.md, and tasks.md for a feature are synchronized and consistent.

## Execution

```bash
mekong analyze check $ARGUMENTS
```

## What It Checks

- **Artifact presence** — all three SDD files exist (spec.md, plan.md, tasks.md)
- **Feature slug match** — each artifact references the given feature slug
- **Task coverage** — tasks declared in tasks.md correspond to phases in plan.md
- **Requirement alignment** — plan phases address spec requirements

## Output

Returns structured report:
- **OK** — all artifacts consistent
- **Mismatch list** — specific files + what diverges

Zero file modifications. Pure validation.

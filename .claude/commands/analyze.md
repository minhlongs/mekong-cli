description: "Cross-artifact consistency check -- mekong analyze check <feature>"
argument-hint: "<feature-slug>"
---
Validate consistency across spec.md, plan.md, and tasks.md for a feature.

Runs `mekong analyze check` — read-only validation that checks:
- All three artifacts exist (SPEC.md, plan.md, tasks.md)
- Each artifact mentions the feature slug
- Task count is reported

Returns structured OK/mismatch output. No file modifications.

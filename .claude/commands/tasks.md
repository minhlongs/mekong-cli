---
description: "SDD tasks -- generate TDD-ordered task list from spec"
---

# SDD Tasks

Generate a TDD-ordered task list from the spec for a feature.

## Usage

```
/tasks run <feature_slug>
```

## Workflow

1. **Find spec** -- locate `specs/NNN-<feature_slug>/spec.md`
2. **Generate tasks** -- render `tasks-template.md` with TDD ordering:
   - **Test tasks** (all `[P]` = parallel-safe)
   - **Implementation tasks** (sequential)
   - **Integration tasks** (sequential)
3. **Write output** -- `specs/NNN-<feature_slug>/tasks.md`

## TDD Ordering

```
### Tests (Prerequisites)          <- [P] all — run concurrently
### Implementation                 <- sequential dependency chain
### Integration                    <- run last, validates everything
```

`[P]` = parallel-safe (no shared state with sibling tasks).
Execute in order; `[P]` tasks within the same group can run concurrently.

## Related Commands

- `/specify run <description>` -- create the spec first
- `/tasks run <feature_slug>` -- generate tasks from spec
- `/implement run <feature_slug>` -- execute implementation wrapping goal engine

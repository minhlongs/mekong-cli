description: "SDD implement -- execute implementation from task list via goal engine"
---
# SDD Implement

Execute implementation for a feature by wrapping the goal engine with spec context.

## Usage

```
/implement run <feature_slug>
```

## Workflow

1. **Find spec dir** -- locate `specs/NNN-<feature_slug>/`
2. **Validate prerequisites** -- ensure `spec.md` and `tasks.md` exist
3. **Create goal** -- goal titled `SDD: implement <slug> -- NNN-slug`
4. **Inject context** -- write spec + tasks content to `.mekong/context/<goal_id>.json`
5. **Delegate to goal engine** -- runs `mekong goal run <id> --auto`

## Delegation (No Duplication)

The implement runner does NOT duplicate goal logic:
- Goal creation delegates to `GoalEngine.create_goal()`
- Execution delegates to `mekong goal run --auto`
- Only adds: spec context injection + TDD task preview

## Related Commands

- `/specify run <description>` -- create the spec
- `/tasks run <feature_slug>` -- generate TDD-ordered tasks
- `/implement run <feature_slug>` -- this: delegate to goal engine

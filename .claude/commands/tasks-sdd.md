description: "SDD task generation -- mekong tasks new <feature> (TDD-ordered)"
argument-hint: "<feature-slug> [--feature-dir/--no-feature-dir]"
---
Generate a TDD-ordered task list from the SDD tasks template.

Runs `mekong tasks new` with the provided feature slug. Produces tasks.md with test-first ordering: tests before implementation, `[P]` marks parallel-safe tasks.

**Options:**
- `--feature-dir` — write to `.mekong/features/<NNN>-<feature>/tasks.md`
- `--no-feature-dir` — write to `.mekong/tasks.md`

> Note: This is the SDD pipeline task generator. For the general task manager (`/tasks todo`, `/tasks create-prd`), use `/tasks` instead.

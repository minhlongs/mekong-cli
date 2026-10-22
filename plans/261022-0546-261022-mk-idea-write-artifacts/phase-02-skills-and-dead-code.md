---
title: "Phase 2: Thin the skills and remove dead code"
status: todo
---

# Phase 2: Thin the skills and remove dead code

## Overview

The skills are the reason the context burn happens: they mandate inline emission the CLI
never persists. Turn both into thin wrappers around the command, and remove the code that
implies absent features.

## Requirements

- [ ] `.agents/skills/idea/SKILL.md` invokes `mk idea` and reports its output; no "AUTO-EXECUTE", no "WRITE ALL 25 FILES NOW"
- [ ] `.agents/skills/project-idea/SKILL.md` likewise drops the batch-emission mandates
- [ ] `_is_ultracode_mode()` deleted (defined at src/cli/idea_commands.py:30, called nowhere in the repo)
- [ ] `--auto` and `--parallel` either implemented or removed from the command signature and help
- [ ] `IDEA_AUTOPILOT.md` retired or reduced to a pointer (it documents a CF-only flow no command triggers)

## Implementation Steps

1. Rewrite `.agents/skills/idea/SKILL.md`: "Run `mk idea "<text>" -o plans/company-blueprint`, then read the written files and summarise." Keep stage detection and tri-layer framing as *reading* context for the agent, not as an emission script.
2. Rewrite the matching sections of `.agents/skills/project-idea/SKILL.md` the same way.
3. Delete `_is_ultracode_mode`.
4. Delete `auto` and `parallel` from `idea_run`'s signature and the `flags` dict — they are read by nothing and advertising them is the most damaging kind of no-op.
5. Point `IDEA_AUTOPILOT.md` at the CLI wrapper, or delete it if nothing references it.

## Files

- `.agents/skills/idea/SKILL.md` (162 lines today)
- `.agents/skills/project-idea/SKILL.md` (252 lines today)
- `IDEA_AUTOPILOT.md` (216 lines today)
- `src/cli/idea_commands.py`

## Todo

- [ ] both SKILL.md rewritten as wrappers
- [ ] `grep -c "WRITE ALL\|AUTO-EXECUTE"` on both files returns 0
- [ ] `_is_ultracode_mode` gone
- [ ] `--auto`/`--parallel` resolved
- [ ] `IDEA_AUTOPILOT.md` handled

## Success Criteria

`grep -c "WRITE ALL\|AUTO-EXECUTE" .agents/skills/idea/SKILL.md .agents/skills/project-idea/SKILL.md`
prints `0` for both, and `mk idea --help` lists no flag that does nothing.

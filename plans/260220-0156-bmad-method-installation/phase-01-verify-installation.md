# Phase 01 — Verify Installation & `/bmad-help`

## Context Links
- Parent plan: [plan.md](plan.md)
- Config: `_bmad/bmm/config.yaml`
- Commands dir: `.claude/commands/bmad-*.md`
- Research: `research/researcher-01-bmad-method-overview.md`

## Overview
- **Priority:** P1
- **Status:** Mostly done (installation verified, `/bmad-help` to test)
- **Effort:** 15min
- **Description:** Confirm BMad v6.0.0-Beta.7 is fully operational; test `/bmad-help` for context-aware guidance.

## Key Insights
- Installation already done: `_bmad/bmm/`, `_bmad/bmb/`, `_bmad/core/`, 55 commands
- Config file sets `project_name: mekong-cli`, `user_skill_level: intermediate`
- `/bmad-help` is context-aware — responds differently depending on current project state
- Brainstorming + PRD already generated in `_bmad-output/`

## Implementation Steps

1. **Confirm file structure** — verify 3 module dirs and command count:
   ```bash
   ls _bmad/          # should show: bmm/ bmb/ core/
   ls .claude/commands/ | grep bmad | wc -l  # should show: 55
   ```

2. **Review config** — open `_bmad/bmm/config.yaml`, confirm:
   - `project_name: mekong-cli`
   - `user_skill_level: intermediate`
   - Output paths point to `_bmad-output/`

3. **Test `/bmad-help`** — run the command in a new Claude session:
   ```
   /bmad-help
   ```
   Expected: BMad master agent activates, asks what phase you're in or what you need help with, provides context-aware guidance based on current project state (PRD exists, brainstorming done).

4. **Review existing outputs** — confirm previous sessions produced artifacts:
   ```bash
   ls _bmad-output/brainstorming/   # brainstorming-session-2026-02-19.md
   ls _bmad-output/planning-artifacts/  # prd.md
   ```

5. **Check BMB module** — verify builder commands present:
   ```bash
   ls .claude/commands/ | grep bmad-bmb  # should list bmb-* commands
   ```

## Todo
- [x] BMad v6.0.0-Beta.7 installed
- [x] BMM module verified (`_bmad/bmm/`)
- [x] BMB module verified (`_bmad/bmb/`)
- [x] 55 commands in `.claude/commands/`
- [ ] Test `/bmad-help` in live session — verify context-aware response
- [x] Brainstorming output exists
- [x] PRD output exists

## Success Criteria
- `/bmad-help` returns intelligent, context-aware guidance (not generic help text)
- Config confirmed correct for mekong-cli project
- All 55 commands accessible

## Risk Assessment
- **Low risk** — installation already complete, this is verification only
- If `/bmad-help` gives generic output: check that Claude reads `.claude/commands/bmad-help.md` correctly

## Next Phase
→ [phase-02-test-planning-phases.md](phase-02-test-planning-phases.md)

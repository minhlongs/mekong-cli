---
title: "Make mk idea write its blueprint to disk"
description: "idea_commands.py prints a hardcoded template and writes zero files, while both skills order the agent to emit 25 blueprints inline every run. Move writing onto code and make the skills thin CLI wrappers."
status: pending
priority: P1
effort: "6h"
tags: [mk-idea, context-economy, cli, skills]
created: 2026-10-22
---

# Make mk idea write its blueprint to disk

## Overview

`mk idea` is context-negative. `src/cli/idea_commands.py` calls `output_dir.mkdir()`
and then writes nothing — there is no `write_text` or `company.json` write in the
file. Meanwhile `.agents/skills/idea/SKILL.md` and `.agents/skills/project-idea/SKILL.md`
instruct the agent to "AUTO-EXECUTE ... WRITE ALL 25 FILES NOW". A genuinely budgeted
autonomous loop (`mekong/autopilot/`, 800k-token `SafetyBudget`, compacting
`ContextManager`, `audit.jsonl`) exists but **nothing in `src/` imports `IdeaLoop`**.

Because the CLI will not write and the skills forbid waiting, the only way an agent can
satisfy the skill is to invent all 25 blueprints inline as tool calls: ~26.8 KB of skill
text plus the full generated prose, every run, none persisted. That is the context burn.

## Goals

| # | Goal | Priority |
|---|------|----------|
| 1 | `mk idea run` writes a real artifact set to disk | P1 |
| 2 | Default path is deterministic Python, zero LLM tokens | P1 |
| 3 | `--deep` hands generation to the existing IdeaLoop under SafetyBudget | P1 |
| 4 | Both SKILL.md become thin wrappers with no inline-emission mandate | P1 |
| 5 | Dead code and inert flags stop implying features that do not exist | P2 |

## Phases

| # | Phase | Status |
|---|-------|--------|
| 1 | [Phase 1: CLI writes artifacts + deep reaches IdeaLoop](./phase-01-start.md) | Complete |
| 2 | [Phase 2: Thin the skills, remove dead code](./phase-02-skills-and-dead-code.md) | Complete |
| 3 | [Phase 3: Tests and gates](./phase-03-tests-and-gates.md) | Complete |

## Success Criteria

- [ ] `mk idea "demo" -o plans/co` leaves `company.json` + blueprint files on disk (`find plans/co -type f` > 1)
- [ ] `grep -c "WRITE ALL\|AUTO-EXECUTE" .agents/skills/idea/SKILL.md .agents/skills/project-idea/SKILL.md` = 0
- [ ] A test asserts `--deep --dry-run` reaches IdeaLoop and emits `.mekong/idea/<run>/audit.jsonl`
- [ ] `_is_ultracode_mode` no longer exists; `--auto`/`--parallel` either work or are removed from help
- [ ] `pytest tests/test_idea_deep_opencore_brainstorm.py tests/test_opencore_saas_25_step_suite.py` stays 12 passed

## Non-goals

Making generated content idea-specific beyond the live audit; changing the readiness
engine or its verdict logic; the open-core monetization defects; git history; resolving
which 25-file spec is authoritative (both skills and IDEA_AUTOPILOT.md disagree —
a founder decision).

## Constraints

KISS/DRY. Reuse `src/core/company_init.py:write_config_files`,
`OpenCoreDeepBrainstormEngine`, and `mekong/autopilot/IdeaLoop` rather than rebuilding
them. Keep the `run`/`brainstorm` subcommands and existing flags working for existing
callers. No secrets or real keys in outputs or tests. Do not revert the 34 uncommitted
entries already in the working tree.

## Red-team findings (recorded before implementation)

1. **LOC guard scope corrected (twice).** `tests/test_loc_invariants_for_deep_brainstorm_modules.py`
   polices **only `src/core/opencore`** at 185 LOC, deliberately not `src/` globally (its
   docstring says a global limit "would redden the suite on 500+ unrelated pre-existing
   files"). A *second* guard inside `tests/test_idea_deep_opencore_brainstorm.py` polices a
   named list — including `src/cli/idea_commands.py` **and that test file itself** — at 165 LOC,
   plus every `src/cli/*.py` at 180. My first read missed the second guard entirely and the
   suite went red at 278 LOC; the fix was to extract `blueprint_files`, `write_blueprint`,
   `run_deep_engine` and the four `stage_*` builders into the new `src/cli/idea_blueprint_writer.py`,
   and to move the six new CLI-writing tests into `tests/test_idea_run_blueprint_writing.py`
   so the self-policed file stayed at 162.
2. **`base_dir` semantics decided.** Blueprint files are keyed relative to `--output-dir`, so
   `company.json` lands at `<output_dir>/company.json`, **not** the repository root's
   `.mekong/`. Writing to the repo root would be an unwanted side effect on the caller's tree.
3. **`--dry-run` did not exist** on `idea_run`; Phase 1 added it, so "keep existing flags
   working" is satisfied trivially. `--auto` and `--parallel` were removed outright (inert).
4. **Duplicate test file collapsed.** Two parallel subagents wrote the same six tests into
   separate files; kept the better of the two (`test_idea_run_blueprint_writing.py`, which
   factors out `_isolate_autopilot`) and deleted the other.

## Verified-reusable contracts

- `write_config_files(files: dict[str, str], base_dir: str | Path) -> list[str]` — creates parents, returns written relative paths.
- `RunOptions(idea=..., dry_run=..., worktree=...)` — the safety-budget surface for `--deep`.

<!-- slug: 261022-mk-idea-write-artifacts -->
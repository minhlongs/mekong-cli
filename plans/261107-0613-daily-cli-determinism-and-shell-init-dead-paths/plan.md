---
title: "Fix Daily CLI Test Determinism & Remove Remaining Dead Paths in shell-init.sh"
description: "Isolate TestCliDailyCommand and TestMcpDailyToolsParity against temp_daily_repo so they never fail when the live branch has no commits in the 7-day window, and remove the 4 remaining dead script references in scripts/shell-init.sh with a path-existence regression test."
status: completed
priority: P1
effort: "S"
tags: ["bugfix", "tests", "shell-init", "daily-briefing"]
created: 2026-11-07
---

# Fix Daily CLI Test Determinism & Remove Remaining Dead Paths in shell-init.sh

## Overview

Two concrete defects surfaced during repository verification:

1. **`tests/test_antigravity_daily.py` (`TestCliDailyCommand` & `TestMcpDailyToolsParity`) depends on live git commit timestamps**:
   - `TestCliDailyCommand.test_cli_daily_console_mode` invokes `mekong daily --since "7 days ago"` against the live repository singleton (`get_daily_briefing_engine()`), whereas `src/cli/commands/daily_command.py:108-109` only renders the `"Recent Git Activity"` table when `report.recent_commits` is non-empty. Whenever the checked-out branch has zero commits within the last 7 days (reproduced on commit `a789f0dee` during the Nov 6 full test run), `test_cli_daily_console_mode` fails with `AssertionError: assert "Recent Git Activity" in result.output`.
   - Furthermore, running `TestCliDailyCommand` and `TestMcpDailyToolsParity` against the live repository walks the entire working tree for `TODO`/`FIXME` markers on every test invocation instead of using the existing `temp_daily_repo` fixture (`tests/test_antigravity_daily.py:37`).
2. **`scripts/shell-init.sh` retains 4 dead script paths after commit `d9cac9d3e`**:
   - `alias mekong-raas='bash $MEKONG_ROOT/scripts/raas-bridge.sh'` (`scripts/raas-bridge.sh` deleted in `d9cac9d3e`)
   - `alias mekong-health='bash $MEKONG_ROOT/scripts/cto-health-check.sh'` (`scripts/cto-health-check.sh` deleted in `d9cac9d3e`)
   - `source $MEKONG_ROOT/mekong/adapters/registry.sh` (`mekong/adapters/registry.sh` deleted in `d9cac9d3e`)
   - `source "$MEKONG_ROOT/scripts/bootstrap-init.sh"` (`scripts/bootstrap-init.sh` does not exist)

## Goals

| # | Goal | Priority |
|---|------|----------|
| 1 | Isolate `TestCliDailyCommand` and `TestMcpDailyToolsParity` in `tests/test_antigravity_daily.py` to use `temp_daily_repo` so tests are 100% deterministic regardless of live repo history or wall-clock time, plus add an explicit regression test for zero-commit windows. | P1 |
| 2 | Remove the 4 dead script references (`raas-bridge.sh`, `cto-health-check.sh`, `mekong/adapters/registry.sh`, `bootstrap-init.sh`) from `scripts/shell-init.sh` and add `tests/test_shell_init_script.py` to enforce that every `$MEKONG_ROOT/...` file/directory referenced in `scripts/shell-init.sh` exists on disk. | P1 |

## Phases

| # | Phase | Status |
|---|-------|--------|
| 1 | [Phase 1: TDD Isolation & Dead-Path Cleanup](./phase-01-start.md) | Completed |

## Validation & Red-Team Gate Summary

- **Validation Gate (`PASS`)**: Verified `ak plan validate` passes with exit code 0; all target paths (`tests/test_antigravity_daily.py`, `scripts/shell-init.sh`, `tests/test_shell_init_script.py`) and symbols (`get_daily_briefing_engine`, `DailyBriefingEngine`, `temp_daily_repo`) exist on `HEAD` (`f95e34270`).
- **Red-Team Gate (`PASS`)**:
  1. *Function-local vs module-level import trap*: `src/cli/commands/daily_command.py:23-27` imports `get_daily_briefing_engine` at module level, whereas `scripts/mcp_server.py:1511` and `src/core/mcp_server.py:16466` import `get_daily_briefing_engine` function-locally from `src.core.daily_briefing`. Therefore, the test fixture in `tests/test_antigravity_daily.py` must patch **both** `src.core.daily_briefing.get_daily_briefing_engine` and `src.cli.commands.daily_command.get_daily_briefing_engine` (or reset `src.core.daily_briefing._daily_briefing_instance` to `DailyBriefingEngine(repo_dir=temp_daily_repo)`).
  2. *Untracked plan directory hygiene*: Do not commit untracked `plans/` directories to the public repo if not required by repo tests; keep the git tree clean and scoped to the 3 target files (`scripts/shell-init.sh`, `tests/test_antigravity_daily.py`, `tests/test_shell_init_script.py`).

## Success Criteria

- [x] `TestCliDailyCommand` and `TestMcpDailyToolsParity` in `tests/test_antigravity_daily.py` run against `temp_daily_repo` and pass deterministically even when the live repository has zero recent commits.
- [x] `scripts/shell-init.sh` contains zero references to nonexistent `$MEKONG_ROOT/...` files (`raas-bridge.sh`, `cto-health-check.sh`, `mekong/adapters/registry.sh`, `bootstrap-init.sh`).
- [x] `tests/test_shell_init_script.py` verifies `bash -n scripts/shell-init.sh`, sources `scripts/shell-init.sh` cleanly, and asserts every `$MEKONG_ROOT/<path>` target in `scripts/shell-init.sh` exists on disk.
- [x] `python3 -m pytest tests/test_antigravity_daily.py tests/test_shell_init_script.py -v` and Open-Core boundary suites pass 100%, and `.mekong/company.json` remains byte-for-byte untouched.

<!-- slug: daily-cli-determinism-and-shell-init-dead-paths -->

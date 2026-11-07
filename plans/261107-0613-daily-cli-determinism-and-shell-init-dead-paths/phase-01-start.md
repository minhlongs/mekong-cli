---
title: "Phase 1: TDD Isolation & Dead-Path Cleanup"
status: completed
---

# Phase 1: TDD Isolation & Dead-Path Cleanup

## Overview

Isolate `TestCliDailyCommand` and `TestMcpDailyToolsParity` in `tests/test_antigravity_daily.py` onto `temp_daily_repo` so `mekong daily` tests never depend on the live git history or wall-clock time, remove the 4 remaining dead script references in `scripts/shell-init.sh`, and add `tests/test_shell_init_script.py` to guard `scripts/shell-init.sh` against dead paths.

## Requirements

- [x] Patch `get_daily_briefing_engine` in `tests/test_antigravity_daily.py` (`src.core.daily_briefing.get_daily_briefing_engine` and `src.cli.commands.daily_command.get_daily_briefing_engine`) via an `autouse` fixture on `TestCliDailyCommand` and `TestMcpDailyToolsParity` backed by `temp_daily_repo`.
- [x] Add a regression test in `TestCliDailyCommand` verifying console mode behavior both with commits (`Recent Git Activity` rendered from `temp_daily_repo`) and when an empty time window yields zero commits (`DAILY REPORT` and `Today's Strategic Focus` rendered with exit code 0).
- [x] Remove the 4 dead script references (`scripts/raas-bridge.sh`, `scripts/cto-health-check.sh`, `mekong/adapters/registry.sh`, `scripts/bootstrap-init.sh`) from `scripts/shell-init.sh`.
- [x] Create `tests/test_shell_init_script.py` asserting syntax validity (`bash -n`), clean sourcing, and on-disk existence of every `$MEKONG_ROOT/<path>` target in `scripts/shell-init.sh`.

## Implementation Steps

1. Write `tests/test_shell_init_script.py` first (TDD Red) and run pytest to confirm it catches the 4 missing paths in `scripts/shell-init.sh`.
2. Update `scripts/shell-init.sh` to remove the 4 dead references and re-run `tests/test_shell_init_script.py` (TDD Green).
3. Update `tests/test_antigravity_daily.py` so `TestCliDailyCommand` and `TestMcpDailyToolsParity` use `temp_daily_repo` via monkeypatch, plus add `test_cli_daily_console_mode_empty_window` to cover the 0-commit window branch.
4. Run `pytest` and `ruff` across all touched files and Open-Core boundary gates.

## Todo

- [x] Add `tests/test_shell_init_script.py`
- [x] Clean up 4 dead script paths in `scripts/shell-init.sh`
- [x] Isolate `TestCliDailyCommand` and `TestMcpDailyToolsParity` in `tests/test_antigravity_daily.py`
- [x] Verify pytest + ruff + `.mekong/company.json` byte-identity

## Success Criteria

All tests in `tests/test_antigravity_daily.py` and `tests/test_shell_init_script.py` pass deterministically with 0 lint errors.

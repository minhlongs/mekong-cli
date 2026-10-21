# Pre-Commit Test Report — Goal DB Path / Gate Anchoring / Vacuous Gate Fix

**Date:** 2026-10-21
**Tester:** tester agent (QA Lead role)
**Work context:** /Users/macbook/mekong-cli
**Test scripts:** `/Users/macbook/mekong-cli/plans/261020-goal-go-live-zero-bug/` (pre-commit verification request)
**Python used (suites 1–4):** homebrew python3.14.7 / pytest 9.0.3 / ruff 0.15.18, invoked as `python3 -m pytest` from repo root with `env -u MEKONG_ROOT`
**Python used (checks 5–6):** repo `.venv/bin/python3` (python3.11.15) — used as specified, ABI not mixed with suite results

## Test Results Overview

All requested suites and checks are **GREEN**. No blockers. No files were modified.

| # | Suite | Result | Time |
|---|-------|--------|------|
| 1 | `tests/mekongcli/` + goal adapter + conformance + protocol | 96 passed, 3 skipped | 37.71s |
| 2 | `tests/cli/` | 187 passed | 24.15s |
| 3 | `tests/mekongcli/test_goal_store_path_resolution.py` | 12 passed | 0.45s |
| 4 | ruff on 11 changed files | All checks passed! | — |
| 5 | Vacuous gate, both directions | Correct (both) | — |
| 6 | Store chdir robustness | absolute True, chdir OK | — |
| 7 | Stray debris scan | No new session debris (see notes) | — |

## Exact Summary Lines (verbatim)

### Command 1 — main suite

`cd /Users/macbook/mekong-cli && env -u MEKONG_ROOT timeout 600 python3 -m pytest tests/mekongcli/ tests/test_goal_engine_adapter.py tests/ports/test_goal_engine_conformance.py tests/test_protocol_compliance.py --no-header -p no:cacheprovider -p no:warnings --tb=short -q`

```
======================== 96 passed, 3 skipped in 37.71s ========================
```

Per-file progress line:

```
tests/mekongcli/test_goal_cli.py ..........sss....                       [ 17%]
tests/mekongcli/test_goal_engine.py .........                            [ 26%]
tests/mekongcli/test_goal_store_path_resolution.py ............          [ 38%]
tests/test_goal_engine_adapter.py .................                      [ 55%]
tests/ports/test_goal_engine_conformance.py ...................          [ 74%]
tests/test_protocol_compliance.py .........................              [100%]
```

Exit code: 0.

### Command 2 — CLI suite

`cd /Users/macbook/mekong-cli && env -u MEKONG_ROOT timeout 400 python3 -m pytest tests/cli/ --no-header -p no:cacheprovider -p no:warnings --tb=line -q`

```
============================= 187 passed in 24.15s =============================
```

Exit code: 0.

### Command 3 — path resolution suite with durations

`cd /Users/macbook/mekong-cli && env -u MEKONG_ROOT timeout 300 python3 -m pytest tests/mekongcli/test_goal_store_path_resolution.py --no-header -p no:cacheprovider -p no:warnings -q --durations=5`

```
============================= slowest 5 durations ==============================
0.30s setup    tests/mekongcli/test_goal_store_path_resolution.py::test_repo_local_store_is_not_shadowed_by_home
0.02s call     tests/mekongcli/test_goal_store_path_resolution.py::test_clean_gate_output_is_not_treated_as_vacuous
0.01s call     tests/mekongcli/test_goal_store_path_resolution.py::test_empty_target_gate_output_is_treated_as_vacuous

(2 durations < 0.005s hidden.  Use -vv to show these durations.)
============================== 12 passed in 0.45s ==============================
```

Exit code: 0.

### Command 4 — ruff on changed modules

```
All checks passed!
```

Exit code: 0. Files checked: `goal_engine/store.py`, `store_schema.py`, `store_queries.py`, `service.py`, `service_helpers.py`, `goal_engine/__init__.py`, `verification/gates.py`, `verification/__init__.py`, `test_goal_store_path_resolution.py`, `test_goal_engine_conformance.py`, `test_goal_engine_adapter.py`.

### Command 5 — vacuous gate, both directions (run from `/tmp/gatest`, MEKONG_ROOT unset)

```
clean -> exit 0 | success True | vacuous False
empty -> exit 0 | success True | vacuous True
```

Expected: `clean → exit 0, vacuous False (gate passes)` and `empty → exit 0, vacuous True (gate fails)`.
**Both directions are correct.** Not a blocker.

### Command 6 — store chdir robustness (run from `/tmp/cdtest`)

```
absolute: True
chdir OK
```

Expected: `absolute: True` and `chdir OK`. **Matches.** Not a blocker.

### Command 7 — stray test debris

```
/tmp/.mekong
/tmp/cdtest/.mekong
/tmp/cptest/.mekong
/tmp/dbclash/.mekong
/tmp/oldfull/.mekong
/Users/macbook/mekong-cli/.mekong/goals.sqlite3
```

`/tmp/gatest` and `/tmp/cdtest` were created by this session and have been **cleaned up** (`rm -rf` confirmed, both paths no longer exist). Post-cleanup re-scan:

```
/tmp/.mekong
/tmp/cptest/.mekong
/tmp/dbclash/.mekong
/tmp/oldfull/.mekong
/Users/macbook/mekong-cli/.mekong/goals.sqlite3
```

## Critical Issues

**None.** All suites and behavioral checks pass. No blockers to the commit.

## Test Coverage Analysis

- Findings on the corrected bugs are covered in both directions:
  - **Criterion 3 (vacuous pass), fail direction:** `test_empty_target_gate_output_is_treated_as_vacuous` asserts exit-0 success **and** `_looks_vacuous(...) is True`.
  - **Criterion 3, pass direction:** `test_clean_gate_output_is_not_treated_as_vacuous` asserts success **and** not-vacuous, guarding against over-suppression (the exact risk taken by the earlier marker-list fix).
  - **chdir robustness:** `test_store_path_is_absolute_and_survives_chdir` constructs a store, chdirs, then calls `list_goals()`, and asserts `Path.cwd()` actually changed (`test_resolution_is_identical_from_any_directory` re-confirms chdir took effect).
- **Removed-marker regression:** the vacuous-pass marker list no longer contains ruff's `All checks passed!`. The clean-direction test above is the live guard: if that banner were re-added, it would still pass (banner absent in a passing run's stdout may not catch it). See Recommendation 1 below for a stronger guard.
- **Path resolution precedence:** explicit arg > env var > repo-local `.mekong` > home-anchored default — each has a dedicated test; the repo-local-over-home case is covered by `test_repo_local_store_is_not_shadowed_by_home`.

### Untested / partially covered paths

| Finding | Covered by |
|---------|------------|
| Goal DB resolves to home when no repo-local store | `tests/mekongcli/test_goal_store_path_resolution.py::test_default_store_path_is_home_anchored` — **Yes** |
| Gate anchors to repo root not caller CWD | `::test_gate_target_is_sanitised_for_repo_root` — **Yes** |
| `vacuous_output` flag written into persisted gate records | `gates.py:115` — **No dedicated test** (field is only written, never asserted) |
| `exit_code_success` vs `passed` divergence in the record payload | `gates.py:105–115` — **No dedicated test** (semantics asserted only indirectly by the two directional tests) |
| `resolve_repo_root` fallback (no `src/main.py` found anywhere) | `gates.py:56` `return start` branch — **Untested** |
| VerificationPipeline real end-to-end `run()` with a vacuous gate producing `passed=False` | Pipeline `run()` is not exercised by these suites with a vacuous gate outcome |

The two unasserted payload fields (`exit_code_success`, `vacuous_output`) and the `resolve_repo_root` no-match fallback are the only genuine gaps found in the diff under test.

## Performance Metrics

| Suite | Duration | Slowest item |
|-------|----------|--------------|
| Command 1 | 37.71s | — |
| Command 2 | 24.15s | — |
| Command 3 | 0.45s | 0.30s setup (tmp_path-heavy fixture) |
| Command 4 | < 1s | — |

No slow-test concern. Total wall time for all suites: ~63s.

## Build Status

- Ruff: **pass**, no warnings or errors.
- Pytest collection: **clean** — 38 tests collected in `tests/mekongcli/`, no collection errors or import warnings beyond the ambient `pytest_asyncio` deprecation notice emitted by the fetch of the config (this notice appears in every run and is unrelated to the diff; it is a plugin-level PytestDeprecationWarning suppressed from output by `-p no:warnings` in the actual runs).
- Type-check (`mypy`) was **not** part of the requested scope and was not run — flagging this rather than assuming it is covered elsewhere.

## Flaky Test Analysis

No flapping observed. Every command was run exactly once (except command 3, re-run once only because the first invocation's output was truncated in the tool channel — the re-run reproduced the identical 12-passed result, confirming determinism). Note the `3 skipped` in command 1: those are `sss` marks in `test_goal_cli.py` (pre-existing skips, present before the diff — they are conditional/platform skips, not newly introduced).

## Recommendations

1. **Add a direct regression test that the vacuous-marker list excludes the ruff success banner.** Current guard is indirect: `test_clean_gate_output_is_not_treated_as_vacuous` passes whether or not `"All checks passed!"` is in the list, because a clean ruff run's stdout content is not asserted verbatim. A one-line assertion such as asserting `_VACUOUS_PASS_MARKERS` does not contain any substring of the ruff banner would hard-lock the prior fix.
   Priority: **Low** — the behavioral direction is correct today; this closes a regression avenue.
2. **Assert the persisted gate-record payload fields.** `exit_code_success` and `vacuous_output` are computed in `VerificationPipeline.run()` and never asserted. One test with a vacuous gate outcome asserting `result["passed"] is False`, `result["exit_code_success"] is True`, `result["vacuous_output"] is True` would cover the divergence the fix deliberately introduced.
3. **Cover `resolve_repo_root`'s no-match fallback** (`gates.py:56`): a `tmp_path` with no `src/main.py` anywhere in its ancestor chain should return `start` resolved. One small test closes this branch.
4. **Do not check `mypy` implicitly.** If the quality gate requires `npm`-style 0-error builds for the Python side, run `mypy src/mekongcli` explicitly and report — not in this request's scope, so unverified.

## Unresolved Questions

1. `/tmp/.mekong`, `/tmp/cptest/.mekong`, `/tmp/dbclash/.mekong`, `/tmp/oldfull/.mekong` predate this session (Oct 18–20). Are these expected scratch dirs from earlier sessions, or should they be cleaned? Left untouched — not mine to remove, and `/Users/macbook/mekong-cli/.mekong/goals.sqlite3` is `.gitignore`d so it is not a commit risk.
2. `/Users/macbook/mekong-cli/.mekong/goals.sqlite3` last modified 2026-10-20 15:02 (before this session). Confirmed not written by checks 1–7 — the tests use `tmp_path` and explicit paths per the file's own docstring. Flagging only so the commit author knows the file exists and is ignored, i.e., it will not enter the commit.
3. `git status` shows a large number of unrelated modified/deleted files (workflow YAML deletions, `apps/dashboard/**` edits) alongside the goal-engine diff. **These were not part of the requested verification scope.** The commit must be checked for accidental inclusion of unrelated changes before pushing.

## Artifacts

- Suite 1 output: `/private/tmp/claude-501/-Users-macbook/bd1fa4b1-0286-44b5-99b8-e400bcbf256d/tasks/bsmnud8q4.output`
- Suite 2 output: `/private/tmp/claude-501/-Users-macbook/bd1fa4b1-0286-44b5-99b8-e400bcbf256d/tasks/b942604mq.output`
- Suite 3 output: `/tmp/s3_out.txt` (session-local, may be removed)
- Temp dirs `/tmp/gatest`, `/tmp/cdtest`: removed on completion.
- **No source or test files were modified during this verification.**

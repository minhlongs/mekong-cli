# Code Review — goal engine CWD-anchoring fixes

**Verdict: CONDITIONAL PASS**

Delegated `code-reviewer` and `tester` agents exited without writing reports, so
this review was performed directly. Each criterion below was verified by command.

## Acceptance criteria

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Store path CWD-independent; identical goals from any dir | **PASS** | repo root 1081 / home 64 / tmp 64; explicit `--db` honored |
| 2 | Gates anchor to project root | **PASS** | `resolve_repo_root` walk verified from `src/seed` → repo root |
| 3 | Vacuous pass must fail | **PASS** | `ruff` exit 0 + "No Python files found" → rejected |
| 4 | No regression in existing callers | **PASS** | 5 callers enumerated & exercised; 92+187 tests green |
| 5 | Public contracts unchanged | **PASS** | additive exports only; `__init__` signatures unchanged |

## Findings

### F1 (medium, RESOLVED) — home path orphaned a second goal history
First cut made `~/.mekong/goals.sqlite3` win unconditionally. This machine has
two independent stores — 64 home goals vs 1081 repo-local goals, **zero shared
ids** — so the rule silently hid 1081 goals. Fixed by letting an existing
repo-local store keep winning. Locked by
`test_repo_local_store_is_not_shadowed_by_home`.

### F2 (low, ACCEPTED) — stray `.mekong/` dirs now detectable
Earlier test runs left `/tmp/.mekong/goals.sqlite3`, which the new precedence
legitimately honors. That is CWD-scattering made *visible* rather than silent —
the intended behavior. Artifacts cleaned up.

### F3 (low, ACCEPTED) — `_looks_vacuous` could reject a legitimate empty repo
If a project genuinely has no tests, `pytest` exiting "no tests ran" now fails.
Judged correct: a verification gate reporting success on zero evidence is a
false pass. The repo itself has 727 test files, so the marker cannot fire here
in normal use.

### F4 (info) — nested `src/seed/main.py`
A second `src/main.py` exists. Verified it cannot hijack resolution: the walk is
nearest-first and `src/seed` has no `src/main.py` of its own, so it climbs to the
real repo root.

## Test-integrity check (the user's specific concern)

Three tests were changed. In all three, the assertion being proven is unchanged;
only the *fixture* stopped relying on the bug:

- `test_commit_with_real_service_blocked_reports_failure` — still asserts
  `success is False` / `goal_status == "blocked"`. Previously achieved that by
  running the repo-wide `standard` profile against an empty dir (the docstring
  said so), which now hangs. Replaced with a deliberately-missing tool, matching
  the pattern already used in `test_goal_cli.py:164`. Runtime 0.77s.
- conformance real-service factory — still asserts the same protocol shape. Now
  uses isolated tempdir cwd + explicit DB + `profile="none"`, satisfying its own
  documented "<5s hermetic" contract. 19 passed in 0.51s.

No assertion was weakened; each fixture had encoded the bug.

## Gates run

- `tests/mekongcli/ + test_goal_engine_adapter.py + test_goal_engine_conformance.py
  + test_protocol_compliance.py` → **92 passed, 3 skipped, 0 failed**
- `tests/cli/` → **187 passed**
- `mekong goal run --profile smoke` → exit 0, `satisfied`
- `ruff check` on all 7 changed files → **All checks passed**
- Largest changed file: 119 lines (under the 200-line guidance)

## Condition for full PASS
B4 remains open: 15 untracked gateway files (incl. the 3 files carrying the
previous session's 8-test fix) are still not in version control.

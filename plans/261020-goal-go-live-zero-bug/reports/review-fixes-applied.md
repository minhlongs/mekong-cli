# Reviewer FIND → fixes applied

The delegated `code-reviewer` returned **FAIL** and found two blockers my direct
review missed. Both were reproduced by command before being fixed.

## Blocker 1 — `"All checks passed!"` broke the ruff gate permanently
`_VACUOUS_PASS_MARKERS` contained ruff's normal success banner, so a genuinely
clean repo could never pass the `standard` profile. Reproduced:

```
clean dir + `ruff check .`  → exit 0, success True, judged VACUOUS: True
```
Removed that one marker. The other four are output-specific and stay.
Verified both directions after the fix:
- clean `.py` dir → `exit 0`, judged vacuous **False** (gate can pass)
- empty dir → `exit 0`, judged vacuous **True** (gate still fails)

## Blocker 2 — relative `db_path` broke on the first chdir
`resolve_goal_db_path` returned a repo-local path as a *relative* `Path`, which
`sqlite3` re-resolves against process CWD at every `_connect()`. Reproduced:

```
store = SQLiteGoalStore(); os.chdir('subdir'); store.list_goals()
→ OperationalError: unable to open database file
```
All returned paths are now `.absolute()`. Verified: path is absolute and
`list_goals()` succeeds after chdir. This mattered for
`cook_command/payload.py:20`, `implement/__init__.py:189`, and `helpers.py:33`,
which all construct with `cwd=Path.cwd()`.

## Reviewer finding 3 — the phantom test (my error)
`test_resolution_is_identical_from_any_directory` created two directories but
never called `chdir`, and asserted `dir_a != dir_b` — a comparison of two literals.
It was `assert x == x` and would have reported green forever. Rewritten to
actually `chdir` into each directory and compare the two resolutions, with
`assert Path.cwd() == dir_b` proving the chdir took effect.

## Reviewer finding 4 — zero coverage for criterion 3
Added two tests, one per direction, so the vacuous-pass contract is now locked:
`test_clean_gate_output_is_not_treated_as_vacuous` and
`test_empty_target_gate_output_is_treated_as_vacuous`.

Also added `test_store_path_is_absolute_and_survives_chdir` for blocker 2.

## Accepted, not changed
- **Q3 dead code**: `MEKONG_ROOT` is set in this shell, so the `resolve_repo_root`
  walk is bypassed in practice. The walk itself is correct (verified it does not
  cross-project hijack via the nested `src/seed/main.py`). Left as-is: the env
  var is the documented override and the walk is the intended default.
- **Q5 naming**: `vacuous_output` fires for any exit-0 failure, not only vacuity.
  Kept — the field is additive and the raw `exit_code`/`passed` split is auditable.

## Verification after all fixes

| Check | Result |
|---|---|
| `test_goal_store_path_resolution.py` | **12 passed** (was 9) |
| Full targeted suite (mekongcli + adapter + conformance + protocol) | **96 passed, 3 skipped, 0 failed** |
| Clean ruff gate passes | yes |
| Empty-target ruff gate fails | yes |
| Store survives chdir | yes |
| Goal visibility (repo/home/tmp) | 1081 / 65 / 65 |
| `ruff check` on changed files | All checks passed |

## Residual blocker (needs your decision)
**B7 is worse than B4.** `store_schema.py`, `store_queries.py`, and
`service_helpers.py` are untracked, as are the 15 gateway files. Committing
`store.py` alone yields an unimportable module — the goal-engine change must be
committed as a unit or a fresh checkout breaks.

## Verdict after fixes
CONDITIONAL PASS. Both blockers are closed and every acceptance criterion is
now covered by a test that fails without the fix. The only remaining gate is the
version-control integrity question above.

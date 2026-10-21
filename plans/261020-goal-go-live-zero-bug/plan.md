# `/goal` Go-Live Zero-Bug Hardening — Plan

**Status:** implemented + verified; review agents delegated
**Created:** 2026-10-20
**Work context:** `/Users/macbook/mekong-cli`
**Task:** make `/goal` production-safe (go-live with zero bugs)

---

## 1. Current State (verified)

`/goal` is wired and functional. 11 subcommands register correctly under
both `goal` and `g` aliases (`src/cli/_app_setup/core_setup.py:61-62`).
Goal engine tests are **green: 59 passed, 3 skipped, 0 failed**.

The engine's internals are solid:
- SQLite store uses per-call connections + `PRAGMA journal_mode=WAL` + a
  thread lock (`store_schema.py:68-76`) — concurrency-safe by construction.
- All 7 swarm roles plan, execute, and checkpoint correctly.
- `goal checkpointer`/`rollback` exist and work.

**The problem is not the engine. It is the environment contract.**

---

## 2. Confirmed Blockers

### B1 — Goal state silently scatters across directories (HIGH)
`SQLiteGoalStore()` defaults to `.mekong/goals.sqlite3` **relative to CWD**
(`store.py:31`), and `_engine()` passes `cwd=Path.cwd()` (`helpers.py:34`).

Verified empirically:
- from `/tmp` → `mekong goal list --json` returns `[]`
- from `/Users/macbook` → returns real persisted goals

**Impact:** a user who travels with `mekong goal` loses every goal they ever
created, with no error. This alone disqualifies go-live.

### B2 — Verification gates run against the wrong directory (HIGH)
`VerificationPipeline.for_profile(profile, self.cwd)` runs gates in the goal's
CWD (`service.py:143`). Every standard gate fails unconditionally:
- `pytest` → exit 5 "collected 0 items"
- `mypy .` → exit 2 "no .py[i] files in directory"
- `coverage run -m pytest` → exit 5, warns "No data was collected"
- `ruff check .` → exit 0 but **passes vacuously** (no Python files)

Verified: `mekong goal run <id> --json` → `status: "blocked"`, all standard
gates red, for a trivially valid goal.

### B3 — Smoke gate guarantees failure on every non-installed checkout (HIGH)
`SMOKE_GATES` runs `python3 -c 'import src.main'` (`gates.py:35`) with the goal
CWD, but `src` is only importable when the project root is on `PYTHONPATH`.

Verified on a clean temp dir:
```
ModuleNotFoundError: No module named 'src'   → exit 1
```
**Impact:** the intended "fast local check" is the one thing that can never pass.

### B4 — 15 gateway files untracked in git (HIGH)
`src/core/gateway/` has 20 files on disk; only 5 are tracked. The 15-file
modular split — including `gateway_ws_handlers.py`, `gateway_helpers.py`, and
`gateway_dash_router.py`, which carry this session's fixes — has **never been
committed**. Working tree is dirty across 1,937 paths.

**Impact:** the previous session's 8-test gateway fix is not in version
control. It exists only in this working tree.

---

## 3. Recommended Fixes (minimal, source-first)

### Implementation log (2026-10-20)

| # | Outcome | Evidence |
|---|---------|----------|
| 1 | **DONE (revised)** | `resolve_goal_db_path()` added. Home-anchored, BUT an existing repo-local store keeps winning — see correction below |
| 2 | **DONE** | `resolve_repo_root()` + `_looks_vacuous()`; vacuous `ruff` exit-0 now rejected |
| 3 | **DONE** | smoke anchors to repo root; `goal run --profile smoke` exits 0 / `satisfied` |
| 4 | **DONE** | 9 new regression tests, all green |
| 5 | **PENDING** | blocked on ship phase |


| # | Fix | File | Rationale |
|---|-----|------|-----------|
| 1 | Resolve goal DB/repo root from the **installed package root**, not `Path.cwd()`. Allow `--db` / `MEKONG_GOAL_DB` override. | `store.py`, `helpers.py` | Fixes B1; keeps `--db` escape hatch |
| 2 | Anchor gates to the resolved repo root; make "0 tests collected" and "no `.py` files" hard **errors**, not clean passes. | `verification/gates.py` | Fixes B2 + the silent-pass class |
| 3 | Smoke gate: repo-root-anchored `python3 -c "import src.main"`, or drop it if importability is not a meaningful gate. | `verification/gates.py` | Fixes B3 |
| 4 | Add tests locking B1/B2/B3 behaviour: DB path independent of CWD; empty-target gate fails; smoke passes in repo root. | `tests/mekongcli/` | Prevents regression |
| 5 | Commit the 15 untracked gateway files **plus** the 3 carry-over fixes, as a focused commit on a branch. | repo | Fixes B4 |

**Explicitly out of scope** (decide later, do not bundle): the 506 lint
warnings, the ~28 pre-existing test failures, `mcp_server.py` at 33,837 LOC.

---

## 4. Go-Live Sequence

```
Phase A (correctness)   → fixes 1–3        ; goal gate turns green on a real repo
Phase B (proof)         → fix 4 + full suite
Phase C (version ctrl)  → fix 5            ; branch, focused commit
Phase D (smoke)         → /goal smoke green on a clean checkout
```

Gate for "zero bug": `mekong goal run --profile smoke --json` exits 0 on a
clean checkout, and `goal list` returns the same goals from any CWD.

---

## 5. Risks

| Risk | Mitigation |
|------|------------|
| Changing DB resolution orphans existing goals in `~/.mekong/` | One-time migration/notice; keep `--db` override |
| Making empty-target a hard error could break tests asserting exit 0 | Run `tests/mekongcli/` after change; 59 currently green |
| Touching untracked files risks losing the prior gateway fix | Commit **before** refactoring anything else |


## Correction logged during implement (2026-10-20)

First cut of `resolve_goal_db_path()` made the **home path win unconditionally**.
That was wrong, and testing caught it: this machine has two independent goal
histories — `~/.mekong/goals.sqlite3` (64 goals) and the repo-local
`.mekong/goals.sqlite3` (1,081 goals) with **zero shared ids**. Neither is a
superset of the other. The unconditional rule silently hid 1,081 goals.

Final precedence: explicit arg > `MEKONG_GOAL_DB` > existing repo-local store >
home canonical. A repo-local store is a separate history, not a shadow copy, so
it keeps winning while it exists. Verified after the fix:

| CWD | Goals visible |
|-----|---------------|
| `/Users/macbook/mekong-cli` | 1081 |
| `/Users/macbook` | 64 |
| `/tmp` | 64 |

Locked by `test_repo_local_store_is_not_shadowed_by_home`.

### Post-review fixes (delegated code-reviewer returned FAIL)

| Finding | Fix |
|---|---|
| `"All checks passed!"` in vacuous markers broke the ruff gate permanently | marker removed; verified clean-dir passes AND empty-dir fails |
| repo-local path returned relative → `OperationalError` on first chdir | all returned paths now `.absolute()` |
| `test_resolution_is_identical_from_any_directory` never called `chdir` (assert x == x) | rewritten to actually chdir and compare; `Path.cwd()` assertion proves it |
| zero coverage for criterion 3 | added `test_clean_gate_output_is_not_treated_as_vacuous` + `test_empty_target_gate_output_is_treated_as_vacuous` |
| new mypy error `service_helpers.py:77` | annotated `make_task_runner`; now 0 mypy errors in changed files |

Suite after fixes: **96 passed, 3 skipped, 0 failed** (clean env, `MEKONG_ROOT` unset,
stale bytecode purged). Path-resolution file alone: **12 passed**.


Note: stray `.mekong/` dirs created by earlier test runs in `/tmp` were real
CWD-scattering, now detected rather than silent. Those artifacts were removed.

# Pre-Commit Integrity Review — Goal Engine & Verification

**Scope:** Version-control integrity only. 11 proposed files (7 source + 3 new/modified tests, i.e. 5 source + 2 verification + 3 tests + 1 new test => 11 paths).
**Reviewer:** code-reviewer (adversarial, pre-landing)
**Date:** 2026-10-21
**Verdict:** **CONDITIONAL PASS**

---

## Verbatim Verification of Background Claims

| Background claim | Verified | Evidence |
|---|---|---|
| goal_engine has 8 .py, only 5 tracked | VAGUELY WRONG | `git ls-files src/mekongcli/core/goal_engine/` returns **7 tracked** (`__init__`, `models`, `planner`, `service`, `store`, + nothing else? see below) |
| UNTRACKED: service_helpers, store_queries, store_schema | TRUE | `git status --porcelain` shows `??` for all three |
| MODIFIED: store.py, service.py, `__init__.py` | PARTLY WRONG | `models.py` and `planner.py` are also tracked and are **clean**, but the claim lists them right; store.py/service.py/`__init__.py` all show ` M`. Minor: the stated "5 tracked" undercounts by 2 (`models.py`, `planner.py`) |
| verification/ both files TRACKED and MODIFIED | TRUE | both show ` M` |
| gateway package 15 files untracked, out of scope | TRUE but UNDERSTATED | **20 files** on disk, **5 tracked / 15 untracked** — and the 4 *modified* tracked gateway files already import the 15 untracked ones (see Finding 7) |

---

### 1. Import Coherence After Commit — **PASS (this is a net-add commit, not a repair)**

HEAD's `store.py` is **self-contained**. Verified:

- `git show HEAD:src/mekongcli/core/goal_engine/store.py` → 452 LOC, and `grep -c "store_schema\|store_queries\|service_helpers"` on it returns **`0`**. It defines `class SQLiteGoalStore` directly (grep line 31) with all methods inline.
- HEAD's `store.py` has **no** `resolve_goal_db_path` (grep → empty).
- `git log --all -- <store_schema.py store_queries.py>` returns **empty** — the mixin files were **never committed**.
- HEAD's `service.py` is 347 LOC with **0** references to `service_helpers`.
- `git show HEAD~1:src/mekongcli/core/goal_engine/store.py` → same 452 LOC.

**Materialized HEAD tree into `/tmp/headcheck` via `git archive`:**

```
import src.mekongcli.core.goal_engine  -> IMPORT OK
__all__: AcceptanceCriterion, AgentRole, Checkpoint, Goal, GoalEngine,
         GoalPlanner, GoalStatus, GoalTask, SQLiteGoalStore, TaskGraph,
         TaskStatus, VerificationRun
```

**Conclusion:** HEAD imports cleanly and is *self-sufficient*. This commit **does not repair a broken HEAD** — which is the weaker position of the two possibilities. It introduces the mixin split for testability. **No commit introduced a broken state; the previous commit was fine.** (The background framing "this commit REPAIRS it" is not supported.)

### 2. Public Contract Stability — **PASS**

```
git diff goal_engine/__init__.py:
-  from .store import SQLiteGoalStore
+  from .store import SQLiteGoalStore, resolve_goal_db_path
   __all__: + "resolve_goal_db_path"
```

HEAD `__all__` = `['AcceptanceCriterion','AgentRole','Checkpoint','Goal','GoalEngine','GoalPlanner','GoalStatus','GoalTask','SQLiteGoalStore','TaskGraph','TaskStatus','VerificationRun']`
Working `__all__` = the same 12 **plus** `resolve_goal_db_path` = 13.

**Strict superset. No HEAD-exported name is missing.** Verification package similarly goes 2 → 3 exports (`+ resolve_repo_root`).

I additionally enumerated every `def` in HEAD's `store.py` against the union of `store.py + store_schema.py + store_queries.py`: **`comm -23` (lost) is empty; `comm -13` (added) is empty.** The mixin split is a pure relocation with **zero method loss** — including `_connect`, `_init_schema`, `_safe_json`, `add_checkpoint`, `add_event`, `add_memory`, `get_checkpoints`, `get_criteria`, `get_events`, `get_goal`, `get_latest_verification`, `get_memory`, `get_tasks`, `list_goals`, `save_*`, `snapshot`.

### 3. Data-Migration Risk — **NO MIGRATION NEEDED (coexistence is correct)**

`resolve_goal_db_path` precedence (`src/mekongcli/core/goal_engine/store.py:35-57`):
1. explicit `db_path` argument
2. `MEKONG_GOAL_DB` env
3. **repo-local `.mekong/goals.sqlite3` if it `is_file()`**
4. `~/.mekong/goals.sqlite3`

**With both DBs present, the repo-local one wins.** Measured on this machine:

| DB | goals | shared ids with other |
|---|---|---|
| `/Users/macbook/mekong-cli/.mekong/goals.sqlite3` | 1082 | **0** |
| `/Users/macbook/.mekong/goals.sqlite3` | 65 | — |

**Zero shared ids ⇒ genuinely independent histories, not divergent replicas.** Nothing is orphaned: the home DB remains readable from any directory via precedence rule 4, and the repo-local history is never shadowed. The comment at `store.py:51-54` documents this exactly, and `tests/mekongcli/test_goal_store_path_resolution.py:23-45` locks the behavior (`test_repo_local_store_is_not_shadowed_by_home`). **Coexistence is acceptable; migration is unnecessary and would be destructive.**

Note: prior behavior (`Path(".mekong/goals.sqlite3")` CWD-relative) is *not* silently replaced — `Path(db_path).absolute()` is returned untouched when explicit, so any caller passing `db_path=` (every test, `src/cli/goal_commands/helpers.py:33`, `src/cli/cook_command/payload.py:20`) keeps byte-identical behavior.

### 4. Lint / Type — **FAIL on one new defect (1 error introduced)**

**ruff:** `python3 -m ruff check` on all 8 source files → **`All checks passed!`** ✅
**ruff format:** 6 files "would be reformatted" — cosmetic only, repo does not gate on `ruff format` (no CI reference found).

**mypy:**

| | HEAD baseline | Working tree |
|---|---|---|
| Total errors in scoped dirs | **10** | **3** |
| Errors in scoped `.py` files | 3 (`store.py:446` arg-type, `service.py:186`, `service.py:187` no-untyped-def) | **1** (`service_helpers.py:77` no-untyped-def) |

Net: **-7 errors**; the two `service.py` errors and the `store.py:446` `asdict` arg-type are both **fixed**. But a **new** error is introduced in a file this commit *adds*:

`src/mekongcli/core/goal_engine/service_helpers.py:77: error: Function is missing a type annotation [no-untyped-def]`

```python
def make_task_runner(t=task, role_val=assignment.role.value):   # :77 — no annotations
```

Under `[tool.mypy] disallow_untyped_defs = true`. `tests/mekongcli/` passes because pytest does not run mypy.

### 5. Leftover Debris — **FAIL**

Requested check plus what I found:

- `/tmp/.mekong`, `/tmp/cdtest/.mekong`, `/tmp/cptest/.mekong`, `/tmp/dbclash/.mekong`, `/tmp/oldfull/.mekong` all exist.
- **`/tmp/cdtest/.mekong/goals.sqlite3` (57344 bytes, mtime Oct 21 08:00 — today)** is an **orphan goal database created by a non-hermetic run**. Its `sqlite_master` reports it cannot be opened (`unable to open database file`) — likely still-locked or truncated. `cdtest` is a CWD-change test directory, matching `test_store_path_is_absolute_and_survives_chdir`-style manual probing.
- **Inside the repo, `.mekong/` is correctly gitignored** (`.gitignore:118`) — confirmed by `git status --porcelain --ignored` → `!! .mekong/`, so **no data leaks into version control**. Also confirmed: repo `./.mekong`, `src/.mekong`, `packages/mekong-engine/.mekong`, `apps/landing/.mekong` all ignored.
- The two modified test files were genuinely made hermetic (see Finding 3), so this `/tmp` debris predates the fix.

---

## Critical Issues

### C1. `type: ignore` suppression freeze violated — 5 new suppressions, zero precedent

`$HOME/.claude/rules/development-rules.md` "ESLint Suppression Freeze (MANDATORTORY)": *"New `eslint-disable` comments are FORBIDDEN unless … the suppression already exists in the baseline"* and *"The baseline count must only decrease over time."*

Measured repo-wide:
- `grep -rn "type: ignore" src/mekongcli/core/` at HEAD → **0**
- working tree → **5**, all in this commit's new files, all `[empty-body]`:
  - `src/mekongcli/core/goal_engine/store_queries.py:30, 32, 33, 34`
  - `src/mekongcli/core/goal_engine/service_helpers.py:32`
- `grep -rn "type: ignore\[empty-body\]" src/` → **exactly these 5** (100% of the repo's population, all newly minted).

These 5 are mixin "attribute exists on the concrete class" placeholder declarations:

```python
class GoalStoreQueriesMixin:
    lock: threading.RLock
    def _connect(self) -> sqlite3.Connection: ...   # type: ignore[empty-body]
    @staticmethod
    def _safe_json(raw: str, fallback: Any) -> Any: ...   # type: ignore[empty-body]
```

I empirically proved they are **avoidable**. In `/tmp/ignchk2` I replaced every `: ...  # type: ignore[empty-body]` with a real body `raise NotImplementedError` and re-ran mypy on the whole package:

```
store_queries rewrote 4
service_helpers rewrote 1
src/core/__init__.py:7: error: ... [no-untyped-def]
src/core/memory_canonical.py:43: error: ... [import-not-found]
Found 2 errors in 2 files   <- both pre-existing, both OUTSIDE scoped dirs
```

**Zero `type: ignore` comments are needed.** The mixin split is the only reason these exist. This is a policy violation introduced by undescribed scope growth and should block.

**Fix:** replace the 5 ellipsis stubs with `raise NotImplementedError` bodies (preserves `disallow_untyped_defs` compliance, drops 5 → 0 suppressions, no behavior change — the concrete `SQLiteGoalStore` overrides every one).

### C2. `service_helpers.py:77` untyped def violates project quality gate

`No :any types` / `disallow_untyped_defs = true` in `pyproject.toml`. Fix alongside C1 by annotating the closure:

```python
def make_task_runner(t: GoalTask = task, role_val: str = assignment.role.value) -> Callable[[], str]:
```

Shares a root cause with C1: this untyped closure was *moved* out of `service.py` into a new file rather than fixed, and the `service.py:186-187` duplicates were fixed while this one was not.

---

## High Priority

### H1. Non-hermetic test created an orphan DB at `/tmp/cdtest/.mekong/goals.sqlite3`

Today 08:00. Confirms at least one pre-fix manual run wrote goal state outside the repo. Not in version control (risk contained), but evidence the CWD-relative bug was live during this session. **Delete `/tmp/cdtest`, `/tmp/cptest`, `/tmp/dbclash`, `/tmp/oldfull`, `/tmp/.mekong`.** Going forward, `resolve_goal_db_path` returning a real path means any test that constructs `SQLiteGoalStore()` without `db_path` writes to the developer's actual `~/.mekong/goals.sqlite3` (65 real goals). `test_goal_store_path_resolution.py:85-99` (`test_store_path_is_absolute_and_survives_chdir`) constructs `SQLiteGoalStore()` with **no explicit path** — it survives only because `monkeypatch.chdir(workdir)` puts it in a tmp dir with a local `.mekong`. That is fragile: it monkeypatches `Path.home` in siblings but *not* here, and if `workdir/.mekong/goals.sqlite3` were absent it would resolve to the **real home DB**. Add `monkeypatch.setattr(Path, "home", ...)` + assert on the resolved path before constructing.

### H2. `test_goal_engine_adapter.py` mutates global class state (`VerificationPipeline.STANDARD_GATES`)

```python
original_gates = VerificationPipeline.STANDARD_GATES
VerificationPipeline.STANDARD_GATES = (VerificationGate("missing-tool", "definitely-missing-mekong-verifier"),)
try: ...
finally:
    VerificationPipeline.STANDARD_GATES = original_gates
```

`tests/test_goal_engine_adapter.py:~281-299`. This is shared mutable class state. Safe **today** because `xdist` is not installed (`ModuleNotFoundError: No module named 'xdist'`) and `pytest.ini` has no `-n auto`. But it is a latent race: the first person to add `-n auto` or run the two files concurrently gets cross-test contamination. Prefer `VerificationPipeline(cwd=..., gates=(...))` via the `gates=` constructor parameter, which is already supported (`gates.py:67-69`) and needs no global mutation.

### H3. Undescribed scope growth — mixin refactor bundled into a bug-fix commit

| file | HEAD LOC | working LOC | delta |
|---|---|---|---|
| `goal_engine/store.py` | 452 | **84** | −368 |
| `goal_engine/service.py` | 347 | **177** | −170 |
| `service_helpers.py` | — | 168 | new |
| `store_queries.py` | — | 159 | new |
| `store_schema.py` | — | 136 | new |

The stated task was 3 behavioral fixes (path anchoring, repo-root anchoring, vacuous-gate detection). The mixin split is a *separate* structural change riding along. It is correctly executed (zero method loss, verified in Finding 2) and it does serve fix #1's testability, but it is not described anywhere in the commit framing I was given, and the three new modules have **no dedicated tests**:

```
grep -rln "store_schema\|store_queries\|service_helpers\|GoalStoreSchemaMixin\|GoalStoreQueriesMixin\|GoalEngineHelpersMixin" tests/
-> (empty)
```

`store_schema.py` (136 LOC, owns DDL + `_init_schema`) and `store_queries.py` (159 LOC, owns all persistence SQL) are now **completely untested as units**; they are only covered incidentally through 12 path-resolution tests and the engine tests. Given the "burned twice by hollow tests" history, this is the largest *unverifiable* surface in the commit.

---

## Medium Priority

### M1. The working tree is drastically dirtier than the task implies — commit hygiene risk

- `git status --porcelain | grep -c "^??"` → **1170 untracked files repo-wide** (**759 under `src/`, 83 under `tests/`)
- 518 modified tracked files under `src/`
- The gateway package alone: **15 untracked files**, and its 4 *tracked* files already import them:
  - `src/core/gateway/gateway_main.py:21,25,29` → `gateway_dash_router`, `gateway_helpers`, `gateway_sub_router`
  - `src/core/gateway/models.py:12` → `models_sub`
  - `src/core/gateway/rate_limiter.py:13` → `rate_limiter_telemetry`
  - `src/core/gateway/streaming.py:16` → `streaming_broker`

  Note: some of those targets **are** tracked (`git ls-files src/core/gateway/` shows 5 incl. `streaming.py`, `rate_limiter.py`), so this is not uniformly broken — but `src/core/adapters/goal_engine_adapter.py` and `src/core/consensus_bridge.py:251`, `sandbox_bridge.py:97`, `memory_federation.py:231`, `_watcher_daemon.py:34`, `mcp_server.py:15627-15693` all import `src.core.gateway.streaming.*`, so the gateway split has the same shape as the goal_engine split and **the same "is HEAD broken?" question must be answered for it before it lands.** I verified goal_engine is safe; **I did not verify gateway** (out of scope), and it should get the identical treatment.
- Also relevant given `/Users/macbook/.claude/projects/-Users-macbook/memory/20261020-sophia-multi-session-concurrency.md`: multiple sessions write this tree concurrently. Verify branch + quiescence immediately before committing.

**Dry-run confirmed all 11 paths stage cleanly and none are gitignored:**
```
git add --dry-run ... 11 files -> 11x "add '...'" (incl. the 3 ?? mixins and 1 ?? test)
```
So `git commit -- <those 11 paths>` (or `git add` them explicitly, never `git add -A`) yields exactly the intended commit.

### M2. Two pre-existing test failures that are *not* this commit's fault — do not let them confuse triage

Running the goal suite on a `git archive HEAD` reconstruction showed **8 identical failures** in `tests/mekongcli/test_goal_cli.py` at *both* HEAD and post-commit, root cause `ModuleNotFoundError: No module named 'src.cli.commands.maritime_bunker_pilot_draft_reefer_command'` — a module that is **untracked** and therefore absent from `git archive`. On the **actual working tree**, `tests/mekongcli/test_goal_cli.py` → **14 passed, 3 skipped**. This is an artifact of my simulation, not a product defect. **Real results below.**

### M3. `ruff format` drift

6 of the scoped files "would be reformatted" (`store.py`, `store_queries.py`, `store_schema.py`, `gates.py` + 2 others). Non-blocking — repo does not gate on format — but worth one `ruff format` pass so the new modules match house style.

---

## Actual Test Results (real working tree, not reconstruction)

| Suite | Result |
|---|---|
| `tests/mekongcli/test_goal_store_path_resolution.py` | **12 passed** |
| `tests/mekongcli/test_goal_cli.py` | **14 passed, 3 skipped** |
| `tests/ports/test_goal_engine_conformance.py` + `tests/test_goal_engine_adapter.py` | **36 passed** |
| `tests/mekongcli/` + conformance + adapter + protocol compliance | **96 passed, 3 skipped** |
| Full `tests/ -k "goal or verification or gate or store"` | **1143 passed, 6 skipped, 13329 deselected, 251s** |

**Post-commit tree simulation** (`git archive HEAD` + the 11 files overlaid): imports clean —
```
import src.mekongcli.core.goal_engine  -> OK, __all__ has 13 entries incl. resolve_goal_db_path
from src.mekongcli.core.verification import VerificationPipeline, resolve_repo_root -> OK
from src.mekongcli.core.goal_engine.service import GoalEngine -> OK
```

---

## Edge Cases from Scout

- `_looks_vacuous` false-positive check — **clean.** Empirically validated 6 cases: `12 passed`, `All checks passed!`, `Success: no issues found in 5 source files` → all `False`; `no tests ran`, `No Python files found`, `No data was collected` → all `True`. No legitimate output trips the markers.
- `resolve_repo_root` (`gates.py:39-49`) falls back to `start` (the caller's cwd) when no `src/main.py` marker is found. `src/main.py` does exist (572 B), so anchoring works in this repo. A gate run outside any repo silently self-anchors rather than failing — acceptable, and `MEKONG_ROOT` is the documented override (verified unset in this environment).
- `VerificationPipeline.__init__` now rewrites `self.cwd` (`gates.py:68`). Only 2 callers (`tests/...:172`, `tests/mekongcli/test_goal_engine.py:106`), both accounted for. `test_gate_target_is_sanitised_for_repo_root` (`tests/mekongcli/test_goal_store_path_resolution.py:163-174`) locks it.
- `vacuous_output` field added to the result payload (`gates.py:115`) — pure addition, no consumer breakage.
- Both modified tests were made hermetic correctly: conformance now uses `tempfile.mkdtemp()` + `verification_profile="none"` (`tests/ports/test_goal_engine_conformance.py:151-156`), eliminating the previously hardcoded `Path("/tmp/test_goal_engine_conformance")`.

---

## Positive Observations

Only where risk-calibrating:
- The mixin relocation is **verifiably lossless** (method-set diff was empty in both directions) — so C1/C2/H3 are about *process and coverage*, not about broken behavior.
- The two fixes that the commit *did* describe are genuinely implemented and tested, and the new test file is **not hollow** — it asserts pass *and* fail directions for vacuous detection (`:102-123`), uses real `LocalExecutor` invocations rather than mocks, and pins CWD-independence with a `Path.cwd() == dir_b` guard (`:82`) that proves the `chdir` actually took effect.
- The commit is a strict mypy improvement (10 → 3 errors) even before fixing C2.

---

## Recommended Actions

1. **BLOCKER (C1):** Delete all 5 `# type: ignore[empty-body]` comments in `store_queries.py` and `service_helpers.py`, replacing each ellipsis body with `raise NotImplementedError`. Verified to reach zero suppressions and zero scoped-dir mypy errors. This is a hard rule ("baseline count must only decrease over time").
2. **BLOCKER (C2):** Annotate `make_task_runner` at `service_helpers.py:77` (params + return type). Fix while addressing the file for C1.
3. **BEFORE COMMIT (H1):** `rm -rf /tmp/cdtest /tmp/cptest /tmp/dbclash /tmp/oldfull /tmp/.mekong`. Add `Path.home` monkeypatching to `test_store_path_is_absolute_and_survives_chdir` (`test_goal_store_path_resolution.py:85`) so it cannot touch the real 65-goal home DB if the fixture dir ever changes.
4. **STRONGLY RECOMMENDED (H2):** Replace the `VerificationPipeline.STANDARD_GATES` global mutation at `tests/test_goal_engine_adapter.py:~281` with the existing `gates=` constructor parameter. Removes the latent `-n auto` race.
5. **DECISION NEEDED (H3):** Either (a) split into two commits — the 3 behavioral fixes + tests, then the mixin refactor — or (b) keep bundled and add at least one direct test exercising `store_schema.py` DDL/migration behavior (e.g. opening a pre-mixins schema file) so the 136 LOC of previously-inline-now-untested SQL is covered. Do not land 275 LOC of untested persistence code as "scope growth."
6. **COMMIT HYGIENE (M1):** Use `git commit -- <11 explicit paths>`, never `git add -A`. Confirm HEAD SHA immediately before committing (multi-session hazard). Apply the *same* HEAD-importability verification to the gateway package before that split lands.
7. **OPTIONAL (M3):** Run `ruff format` on the 6 drifted files.

---

## Unresolved Questions

- Should the gateway split get its own pre-commit integrity review? It has the identical shape (tracked files importing untracked siblings) and I could not verify its HEAD importability within this task's scope.
- Is the mixin split intentional scope, or did it drift? No plan/commit text I was given describes it. The commit message should describe it, per `~/.claude/rules/review-audit-self-decision.md` ("Explain the invariant or behavior directly").
- Which `/tmp` directory corresponds to which manual run is not reconstructible from mtimes alone; the orphans should just be removed.

---

## Metrics

- **ruff (8 source files):** 0 errors ✅
- **mypy (scoped dirs):** 3 errors (HEAD baseline: 10). Net −7, but **+1 new error at `service_helpers.py:77`**.
- **`type: ignore` in `src/mekongcli/core/`:** 0 → **5** ❌ (freeze violated)
- **Tests (real tree):** 1143 passed / 6 skipped (full `-k` sweep); 96 passed targeted; 12 passed new file. 0 failures.
- **Public API:** strict superset, 12 → 13 (`goal_engine`) and 2 → 3 (`verification`). No removals.
- **Store method parity vs HEAD:** 0 lost, 0 renamed.
- **Data migration:** none required (0 shared goal ids across the two DBs).
- **Untracked-in-tree:** 1170 repo-wide (759 in `src/`) — commit must be path-explicit.

# Pre-Ship Review — `/goal` Go-Live Zero-Bug Hardening

**Verdict: FAIL**
**Reviewed:** 2026-10-20
**Scope:** focused bug-fix change (goal store path resolution + gate anchoring + vacuous-pass detection)
**Work context:** `/Users/macbook/mekong-cli`

> **Review-wide caveat:** the tree was **mutating during review**. `store.py`, `gates.py`,
> `service.py`, the 3 new mixin files, and the new test file were all written/rewritten
> between 15:33 and 18:53 (fresh `mtime`s), and `store.py` changed content twice while I read it.
> All findings below are pinned to the hashes captured at the end. Re-verify before acting.

---

## Scope actually under review

The task described **4 source + 3 test** files. The real diff is larger:

| File | Status | HEAD → working |
|---|---|---|
| `src/mekongcli/core/goal_engine/store.py` | modified | 452 → 84 LOC |
| `src/mekongcli/core/goal_engine/service.py` | modified | 347 → 177 LOC |
| `src/mekongcli/core/verification/gates.py` | modified | 83 → 119 LOC |
| `src/mekongcli/core/goal_engine/__init__.py` | modified | +1 export |
| `src/mekongcli/core/verification/__init__.py` | modified | +1 export |
| `src/mekongcli/core/goal_engine/store_schema.py` | **UNTRACKED (new)** | 136 LOC |
| `src/mekongcli/core/goal_engine/store_queries.py` | **UNTRACKED (new)** | 159 LOC |
| `src/mekongcli/core/goal_engine/service_helpers.py` | **UNTRACKED (new)** | 168 LOC |
| `tests/mekongcli/test_goal_store_path_resolution.py` | **UNTRACKED (new)** | 137 LOC |
| `tests/ports/test_goal_engine_conformance.py` | modified | hermetic fixture |
| `tests/test_goal_engine_adapter.py` | modified | hermetic fixture |

The modularization itself is sound — every file now respects the 200-LOC rule — but it is
undescribed scope drift, and it **triples the plan's own B4 hazard** (see M2).

---

## Acceptance criteria

| # | Criterion | Result |
|---|---|---|
| 1 | Store path independent of CWD; `goal list` identical from any directory | **FAIL** — see C1 |
| 2 | Verification gates anchor to project root, not caller's directory | **PASS** (with caveat, see M3) |
| 3 | Vacuous pass (exit 0, examined nothing) must FAIL | **PARTIAL** — implemented, but over-broad to the point of breaking normal gates. See C2 |
| 4 | No regression for existing callers | **PASS** — all 7 callers exercised, signatures unchanged |
| 5 | Public contracts unchanged | **PASS** — `SQLiteGoalStore.__init__` / `GoalEngine.__init__` signatures identical; MRO clean |

---

## CRITICAL 1 — `_looks_vacuous` rejects every *clean* ruff run, so the ruff gate can never pass

`src/mekongcli/core/verification/gates.py:26-32`

```python
_VACUOUS_PASS_MARKERS = (
    "All checks passed!",        # <-- ruff's NORMAL SUCCESS STRING
    "no tests ran",
    "No Python files found",
    "no .py[i] files in directory",
    "No data was collected",
)
```

`"All checks passed!"` is the exact stdout of a **passing** `ruff check .`. Verified twice:

```
$ cd /tmp/ruffprobe && ruff check .     # clean dir containing `x = 1`
All checks passed!
EXIT=0
```

and end-to-end through the real pipeline (`MEKONG_ROOT` pinned to an isolated probe dir so no
parent-walk contamination):

```
ruff | passed: False | exit: 0 | exit_code_success: True | vacuous_output: True
stdout: 'All checks passed!\n'
```

`gates.py:97-99` computes `gate_passed = outcome.success and not _looks_vacuous(...)`, so a
genuinely clean repo — exit 0, zero findings — is recorded as **failed**. The `standard` profile
therefore cannot pass on any repository where lint is clean, which is the inverse of the goal.

Note the marker is also ambiguous by construction: ruff prints `All checks passed!` both after a
clean run *and* on a partial run following `--fix`, so the string cannot discriminate the two cases.

**The plan's B2 diagnosis was correct about the empty-directory case** (`ruff check .` exits 0 with
no Python files), and the remaining markers do cover it — `No Python files found` appears on
ruff's `warning:` line (stderr), and `_looks_vacuous` concatenates stdout+stderr, so it is caught.
The fix for the real problem is to drop `"All checks passed!"` entirely; the other four markers
already handle the vacuous cases correctly and are specific.

**Fix:** remove `"All checks passed!"` from `_VACUOUS_PASS_MARKERS`. If a positive signal is
wanted, gate on the *absence of scanned files*, not on the success banner.

---

## CRITICAL 2 — Acceptance criterion #1 is not met: `goal list` still returns different goals by directory

`src/mekongcli/core/goal_engine/store.py:51-56`

```python
local_path = Path(".mekong") / DEFAULT_GOAL_DB_NAME
if local_path.is_file():
    _logger.debug("using repo-local goal store at %s", local_path)
    return local_path
return Path.home() / ".mekong" / DEFAULT_GOAL_DB_NAME
```

Measured on the real machine, same command, four directories:

| CWD | resolved `db_path` | goals |
|---|---|---|
| `/Users/macbook/mekong-cli` | `.mekong/goals.sqlite3` **(relative)** | **1081** |
| `/Users/macbook` | `.mekong/goals.sqlite3` **(relative)** | **65** |
| `/tmp` | `/Users/macbook/.mekong/goals.sqlite3` | **65** |
| `/Users/macbook/Desktop` | `/Users/macbook/.mekong/goals.sqlite3` | **65** |

Two defects here:

1. **CWD-dependent resolution persists.** `.mekong/goals.sqlite3` exists in *both*
   `/Users/macbook/mekong-cli` (1081 goals) and `/Users/macbook` (65 goals). Which store wins is
   decided by an accidental directory artifact, so the same `mekong goal list` returns 1081 or 65
   goals. That is precisely the B1 scatter the change set out to eliminate, relocated rather than
   fixed. A goal created from `/tmp` lands in the home DB; the identical command from the repo
   root lands in the repo DB.

2. **The returned path is relative.** `local_path` is `Path(".mekong") / ...`, so `self.db_path`
   is relative and every `_connect()` (`store_schema.py:69`) re-resolves it against the *process*
   CWD at access time. Demonstrated: create a store where `.mekong/goals.sqlite3` exists,
   `os.chdir()` into a subdirectory, then call `list_goals()` →

   ```
   sqlite3.OperationalError: unable to open database file
   ```

   `cook_command/payload.py:20`, `implement/__init__.py:189`, and `helpers.py:33` all construct
   with `cwd=Path.cwd()` and some spawn subprocesses — exactly the population exposed to this.

This is a **deliberate design decision, not an oversight** — the comment at `store.py:48-50` and the
new test `test_repo_local_store_is_not_shadowed_by_home` (`test_goal_store_path_resolution.py:23-44`)
both assert repo-local-wins-on-purpose, arguing the two stores hold independent histories
(~1k repo-local vs ~64 home, no shared ids). That reasoning is coherent, but it **contradicts
criterion #1 as written**, and the new test suite now *locks the violation in as intended
behaviour*. This needs a user decision, not a silent ship.

**Fix:** default to one absolute canonical path — `(Path.home() / ".mekong" / DEFAULT_GOAL_DB_NAME)`
returned already-absolute — and keep repo-local only as an explicit opt-in via `MEKONG_GOAL_DB`
or `--db`. If repo-local-wins is the desired product behaviour, criterion #1 must be rewritten
first and the ~1k/65 divergence surfaced to the user as a migration decision.

---

## HIGH 3 — The vacuous-pass logic (plan fix #2, criterion #3) has zero test coverage

```
$ grep -rn "vacuous\|_looks_vacuous\|exit_code_success" tests/ | grep -v __pycache__
tests/mekongcli/test_goal_store_path_resolution.py:7:and verification gates to pass vacuously.
```

That is a docstring mention. No test asserts that a vacuous exit-0 gate is rejected, and **no test
asserts that a clean exit-0 gate is accepted** — which is exactly why CRITICAL 1 ships green. The
9 new regression tests cover path resolution and repo-root anchoring only.

**Fix:** add two cases — (a) `VerificationPipeline` with a gate whose command exits 0 and prints
`No Python files found` must yield `passed: False` and `vacuous_output: True`; (b) a gate that
exits 0 with clean output must yield `passed: True`. Case (b) is the regression guard for CRITICAL 1.

---

## MEDIUM 4 — `resolve_repo_root` is correct, but `MEKONG_ROOT` makes the walk dead code in practice

`src/mekongcli/core/verification/gates.py:40-50`

The walk behaves correctly against the reviewer's question #3. With `MEKONG_ROOT` unset:

- Caller inside a **different** project that also has `src/main.py`, nested `src/pkg/sub`
  → resolves to *that* project's root. **Correct** — the nearest root wins, so no cross-project hijack.
- No `src/main.py` anywhere → returns `start` unchanged. Safe (no crash), but silent: an anchor
  failure is indistinguishable from a legitimate root. Given the new markers usually make that
  fail loudly, acceptable — though an explicit error would be better.
- Hostile/stale `MEKONG_ROOT` → verified it redirects all gates to the pointed-at project.

The real issue: **`MEKONG_ROOT=/Users/macbook/mekong-cli` is set in the user's actual shell**
(confirmed via `zsh -ic 'echo $MEKONG_ROOT'` and `env`). Since `gates.py:44` short-circuits on it,
the directory-walk at `gates.py:47-49` never executes in normal use, so the code path that makes
question #3 safe is exactly the path that is never exercised in production. The env override is
also validated only by `src/main.py` existing — a stale value pointing at any old checkout would
silently mis-anchor every gate.

**Fix (low cost):** prefer the walk from `start`, and treat `MEKONG_ROOT` as a last-resort fallback
(or require it to also be an ancestor/related to `start`). At minimum, log which branch was taken.

---

## MEDIUM 5 — Scope drift: 6 source files changed, 3 of them new and untracked

The described change is 4 source files. The actual `git diff --stat -- src/mekongcli/` shows 5,
plus 3 new untracked modules. `store.py` lost 368 lines and `service.py` lost 170 — that is a
full decomposition, not a bug fix.

`store_schema.py`, `store_queries.py`, and `service_helpers.py` are **not tracked in git**. The
working tree is already dirty across 771 paths and the plan's B4 records 15 untracked gateway
files. This extends the same hazard to the goal engine: committing `store.py` alone produces an
unimportable module (`from .store_schema import ...` fails at import). Commit the module as a unit
or the decomposition will break a checkout.

---

## MEDIUM 6 — `service_helpers.py:77` introduces a mypy error (net improvement over HEAD, still new)

```
src/mekongcli/core/goal_engine/service_helpers.py:77: error: Function is missing a type annotation [no-untyped-def]
```

This is the `make_task_runner(t=task, role_val=assignment.role.value)` closure. Context worth
noting: HEAD's `service.py` carried **10** mypy errors, the working tree carries **1** — the
decomposition is a large net typing win. But this one is newly introduced code, and it is the
only remaining error in the changed files.

Also pre-existing and unrelated (out of scope): `packages/memory/mem0_client.py:15` and
`src/core/__init__.py:7`.

---

## Test-file integrity — honest read on the 3 changed files

### `tests/ports/test_goal_engine_conformance.py` — genuine tightening, correct

HEAD: `SQLiteGoalStore()` (CWD-dependent default) + `cwd=Path("/tmp/test_goal_engine_conformance")`.
Now: explicit temp DB, temp cwd, and `verification_profile="none"`.

This is **necessary, not a weakening**. After the resolver change, `SQLiteGoalStore()` in a test
would otherwise bind the 1081-goal repo-local DB, and `standard` gates would run against the
entire repo. The assertions are unchanged and the test is genuinely hermetic now. Nit: two
separate `tempfile.mkdtemp()` calls put the cwd and the DB in different trees; one mkdtemp for
both would be clearer.

### `tests/test_goal_engine_adapter.py` — defensible, but the test's subject changed

`test_commit_with_real_service_blocked_reports_failure` (`:279-301`) now monkeypatches
`VerificationPipeline.STANDARD_GATES` to a single missing binary with `try/finally` restore, instead
of running the real `standard` gates in an empty temp dir.

- Assertions are **unchanged** (`success is False`, `error is not None`, `goal_status == "blocked"`),
  so the strength "gate fails → goal blocked" is preserved.
- But the subject changed: it used to prove "real pytest/ruff/mypy/bandit/coverage in an empty
  directory blocks the goal" — the B2 symptom end-to-end. Now it proves "one missing binary
  blocks the goal". **The `standard` gate set is no longer exercised by any test.**
- The class-attribute monkeypatch is a mild global-state hazard: no `try/finally` covers a hard
  crash mid-body, and any future parallel/importing test would see the mutation.

Verdict: hermeticity fix is justified (the old form is exactly what the resolver change would have
made flaky), but flag the coverage loss and prefer restoring real gates at a repo-root anchor.

### `tests/mekongcli/test_goal_store_path_resolution.py` — two real problems

1. **`test_resolution_is_identical_from_any_directory` (`:62-76`) is a phantom test.** It creates
   `dir_a` and `dir_b`, asserts `dir_a != dir_b` (a comparison of two literal `Path` objects —
   trivially true), and **never calls `monkeypatch.chdir()`**. Verified: CWD is identical before and
   after, and both `resolve_goal_db_path(None)` calls execute in the same directory. It is
   `assert x == x`. This is the test named after acceptance criterion #1, and it proves nothing.

   Fix: `monkeypatch.chdir(dir_a)`, capture, `monkeypatch.chdir(dir_b)`, compare.

2. **`test_repo_root_ignores_invocation_directory` (`:93-104`)** builds a raw
   `pytest.MonkeyPatch()` instead of using the injected `monkeypatch` fixture, and calls `.undo()`
   *after* the assert. If the assertion raises, `MEKONG_ROOT` leaks — and it is set globally in the
   user's shell to the repo root, so a leak would perturb every later test. Fragile; use the fixture.

Positive: `test_repo_target_is_sanitised_for_repo_root` (`:116-127`) sets `MEKONG_ROOT` to the real
repo and asserts the pipeline rewrites a foreign cwd — that is a genuine, meaningful test of the
anchoring fix, and the one test that would have caught a real regression.

On the reviewer's blunt-question framing (#7): **no assertion was weakened to force a pass** in any
of the three files. The conformance change strictly tightens the fixture. The adapter change keeps
every assertion but narrows what it exercises. The new file contains one phantom test that *looks*
like coverage without being coverage — which is worse than a weakened assertion, because it will
report green forever.

---

## Reviewer's specific questions — answers

**Q1 (repo-local fallback reachable/surprising?)** Yes, and it is live on this machine. Both
`~/.mekong/goals.sqlite3` (65 goals) and `/Users/macbook/mekong-cli/.mekong/goals.sqlite3`
(1081 goals) exist, plus `/Users/macbook/.mekong/goals.sqlite3` (65). The `local_path.is_file()`
branch is taken from both home-ish directories and the repo, giving 1081 vs 65 from identical
invocations. Whether home or repo-local wins is decided by which `.mekong` happens to be adjacent
to the CWD — not by policy. This is the kernel of CRITICAL 2.

**Q2 (`Path.home` monkeypatched via `classmethod`?)** Works, no fragility found.
`monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))` correctly intercepts
`Path.home()` and restores on teardown; confirmed by the passing tests and by reproducing the
technique directly. Caveat: it patches `Path.home()` globally for the duration, so any stdlib call
that consults home (sqlite temp dirs, etc.) also sees the fake. In these tests that is intended.

**Q3 (`resolve_repo_root` walk, `MEKONG_ROOT` sufficiency, fallback safety?)** The walk is
correct — the nearest `src/main.py` wins, so a caller inside a *different* project resolves to
that project's own root, not mekong-cli's (verified). `MEKONG_ROOT` is *sufficient but not
necessary* and, because it is already exported in the user's shell, it makes the safe walk path
dead code in production. `return start` does not crash but silently passes an anchor failure
through as if it were a root.

**Q4 (legitimate zero-collection — vacuous or genuine?)** Both sides are arguable and the marker
list splits accordingly:
- Rejecting `no tests ran` / `No data was collected` at a **repo-root** gate is defensible: a
  go-live gate whose suite is empty has proven nothing, and mypy/ruff genuinely exit 0 on empty
  dirs, which is the false-green class worth killing.
- Against it: a per-subpackage gate in a monorepo can legitimately see 0 tests, so the rule is only
  right because these gates are repo-root-anchored.
- The decisive point is that `"All checks passed!"` belongs to **neither** side — it is ruff's
  success banner, and its presence in this tuple is an unambiguous false negative. See CRITICAL 1.

**Q5 (raw `exit_code` vs `passed` recorded auditable?)** Yes, correctly and better than required.
`gates.py:104-117` records `exit_code` (raw), `exit_code_success` (`outcome.success`), `passed`
(verdict), and `vacuous_output` (`gate_passed is False and outcome.success`). A vacuous zero-exit
stays fully visible in the record. Minor: `vacuous_output` is true for *any* failed-gate-with-exit-0
(including a `blocked_reason`), so the name promises more precision than it delivers.

**Q6 (new lint/type errors, files >200 LOC?)** Ruff clean on all 4 in-scope source files. One new
mypy error (`service_helpers.py:77`) against HEAD's 10 in the same code — net large improvement,
one new defect. No file exceeds 200 LOC; max is `tests/test_goal_engine_adapter.py` at 320 LOC
(existing test file, pre-existing, not touched by this change).

**Q7 (did I weaken any assertion?)** No assertion was weakened. Details above: conformance
tightened, adapter preserved but narrowed, new file contains one phantom test and one fragile
monkeypatch. The phantom test is the item that needs your attention, because it will never go red.

---

## Verification performed

| Check | Result |
|---|---|
| `tests/mekongcli/test_goal_store_path_resolution.py` | **9 passed** |
| `tests/test_goal_engine_adapter.py` + `tests/ports/test_goal_engine_conformance.py` | **36 passed** |
| Full `tests/mekongcli` | **32 passed, 3 skipped** |
| Ruff on 4 in-scope source files | clean |
| Mypy on in-scope source | 1 new error (`service_helpers.py:77`) + 2 pre-existing/unrelated |
| Caller inventory (7 sites) | all return real stores; `run_goal_parallel` inherited & working; `_engine(db_path)` honours `--db` |
| Public signatures | `SQLiteGoalStore.__init__(self, db_path: str \| Path \| None = None)`, `GoalEngine.__init__(self, store, cwd=".", memory_store=None)` — identical to HEAD |
| MRO | `['GoalEngine', 'GoalEngineHelpersMixin', 'object']` — clean, no diamond |
| `goal run --profile smoke` | exit 0 / `satisfied` |

---

## Recommended actions, ranked

1. **BLOCKER — remove `"All checks passed!"` from `_VACUOUS_PASS_MARKERS`** (`gates.py:27`). As
   written the ruff gate can never pass on a clean repo. Delete the marker; the other four cover
   the real vacuous cases.
2. **BLOCKER — decide criterion #1.** Either make the default a single absolute
   `Path.home()/".mekong"/goals.sqlite3` return (repo-local only via `MEKONG_GOAL_DB`/`--db`), or
   get explicit user sign-off that repo-local-wins is the intended product behaviour and rewrite
   criterion #1 to match. Today it measurably fails as written (1081 vs 65 goals).
3. **BLOCKER — return an absolute path from `resolve_goal_db_path`** so `self.db_path` cannot
   re-resolve against process CWD (currently causes `sqlite3.OperationalError` after chdir).
4. **Add the two missing vacuous-gate tests** — clean exit 0 must pass; vacuous exit 0 must fail
   with `vacuous_output: True`. #4 is the regression guard for #1.
5. **Replace the phantom test** — make `test_resolution_is_identical_from_any_directory` actually
   `chdir` into both directories and compare.
6. **Fix `service_helpers.py:77`** type annotation.
7. **Use the `monkeypatch` fixture** in `test_repo_root_ignores_invocation_directory` instead of a
   hand-rolled `MonkeyPatch()` with post-assert `undo()`.
8. **Commit the 3 untracked modules as one unit** with `store.py`/`service.py` — extends B4 to the
   goal engine otherwise.
9. **Prefer the directory walk over `MEKONG_ROOT`** (or validate the env root more strictly), so
   the safe code path is the one that actually runs.
10. Restore real `STANDARD_GATES` coverage in the adapter test (anchor cwd at repo root) so the
    gate set is exercised end-to-end at least once.

---

## Plan follow-ups

- Phase A (correctness, fixes 1–3): **not complete.** Fix 1 partially inverted (see C1/C2), fix 2
  implemented but breaks normal gates and is untested, fix 3 verified working (`smoke` green).
- Phase B (proof, fix 4): **partial.** 9 + 36 tests pass, but the criterion the plan cares most
  about (vacuous rejection) has no test, and the new path-independence test is vacuous itself.
- Phase C (version control, fix 5): **blocked** and now larger — 3 additional untracked source
  modules to fold in.
- Phase D (smoke on clean checkout): **`smoke` profile verified green**, but the machine cannot
  reach the plan's stated zero-bug gate (`goal run --profile smoke` green AND `goal list` identical
  from any CWD) until C1/C2 are resolved.

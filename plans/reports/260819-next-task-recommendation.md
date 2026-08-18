# Next Task Recommendation — 2026-08-19

## TL;DR

**Fix the 22 marketplace_router test failures by mocking filesystem scans.** This is the single highest-impact task because it resolves 45% of all non-public test failures, tests a core RaaS product feature, and has a clear, low-risk fix path. The actual failure count is 49 (not 313 as previously estimated), spread across 6 test files.

---

## Failure Inventory (49 total, verified 2026-08-19)

| Test File | Failures | Root Cause | Fix Effort |
|---|---|---|---|
| `tests/raas/test_marketplace_router.py` | 22 | `_scan_skills()` / `_scan_commands()` scan `.claude/skills/` and `.claude/commands/` which do not exist at repo root. All 22 tests depend on these returning data. | Medium |
| `tests/integration/test_ask_routing.py` | 13 | `ask` command dispatches via subprocess: `python -m src.main <routed_command> <question>`. Routed commands like `deploy` are Typer groups that don't accept the question as first arg. | Heavy |
| `tests/e2e/antigravity_e2e/test_f5_inference.py` | 6 | Tests reference `scripts/launch-fable-5` which does not exist. Future-feature tests for fable-5 inference. | Quick (skip/delete) |
| `tests/e2e/test_1m_sop_flow.py` | 5 | Billing refactor changed CreditStore paths. Test mocks patch `src.raas.credits.CreditStore` but the deduct endpoint now uses a different auth/billing flow (returns 402). | Medium |
| `tests/raas/test_polar_webhook_e2e.py` | 2 | Stale assertions: expects 50 credits for `starter_monthly`, code now provisions 300. | Quick |
| `tests/raas/test_final_phase_validator.py` | 1 | `usage_meter_loaded` is False because the usage meter module was renamed/moved. | Quick |

**Additional findings:**
- 17 tests skipped (benchmarks, purchase flow) — these are fine, they gate on external deps
- 306 tests pass in the non-public suites
- No ruff errors in non-public test directories
- 4 missing `__init__.py` files in non-public test dirs (not causing failures but should be added)

---

## Recommended Task: Fix marketplace_router Tests (22 failures)

### What to fix

`tests/raas/test_marketplace_router.py` has two test classes that fail:

1. **TestCatalogScanning** (4 failures): Directly calls `_scan_skills()` and `_scan_commands()` which scan real filesystem paths `.claude/skills/` and `.claude/commands/`. These directories do not exist at the repo root — the actual skills live in `.claude/_integration/skills/` (and globally in `~/.claude/skills/`).

2. **TestMarketplaceAPI** (18 failures): Creates a FastAPI TestClient and calls `/marketplace/browse`, `/marketplace/skills`, `/marketplace/commands`, `/marketplace/install` endpoints. All depend on the catalog scan returning items, which returns empty because the directories don't exist.

### How to fix

**Option A (recommended): Mock the filesystem scan in tests**

Add fixtures that patch `_scan_skills` and `_scan_commands` to return sample `MarketplaceItem` objects. This makes the tests self-contained and independent of the developer's local filesystem layout. The tests already have a `tmp_db` fixture for database isolation — extend this pattern to the catalog scan.

Concrete changes:
- Add a `@pytest.fixture(autouse=True)` in `TestCatalogScanning` and `TestMarketplaceAPI` that patches `src.raas.marketplace_router._scan_skills` and `src.raas.marketplace_router._scan_commands` to return 5-10 sample items each
- Update `TestCatalogScanning` assertions to check the mocked items (not count > 0 from filesystem)
- Update `TestMarketplaceAPI.test_browse_with_auth` assertion from `data["total"] > 100` to match the mocked count

**Option B (alternative): Create sample `.claude/skills/` and `.claude/commands/` directories**

Create minimal sample files in these paths. Problem: this couples the tests to the repo's directory structure and would break for contributors who have different skill sets installed. Not recommended.

**Option C (alternative): Update scan paths to `.claude/_integration/skills/`**

Change `marketplace_router.py` line 42-43 to scan the correct paths. Problem: this changes production code to match the current repo layout, but the marketplace feature is designed for end-users who install skills into `.claude/skills/`. Not recommended.

### Expected impact

- 22 test failures resolved (45% of all 49 non-public failures)
- RaaS marketplace feature becomes properly testable
- Tests become self-contained (no filesystem dependency)
- Demonstrates active test maintenance for open-source contributors

### Estimated effort

Medium (1-2 hours). The mock fixtures follow existing patterns in the test file. No production code changes needed.

---

## Why This Over Alternatives

### Alternative 1: Mark future-feature tests as skip (19 failures: ask_routing + f5_inference)

**Why not first:** These 19 failures fall into two categories:
- `f5_inference` (6): Clearly future-feature tests for unimplemented fable-5 integration. Quick to skip/delete.
- `ask_routing` (13): The `ask` command exists and partially works — the routing logic (`route_ask`) functions correctly for keyword matching. The bug is in the dispatch mechanism (subprocess call passes question as first arg to Typer group commands). This is a real bug in a real feature, not a future placeholder.

Skipping these would reduce the count but hide real issues. The marketplace fix is higher-impact because it tests a fully-implemented feature that just has a test-design flaw.

**If you want quick wins after the marketplace fix:** Mark the 6 `f5_inference` tests as `@pytest.mark.skip(reason="scripts/launch-fable-5 not implemented")` and fix the 2 `polar_webhook` stale assertions (change expected 50 to 300). That's 8 failures in ~20 minutes.

### Alternative 2: Fix ask_routing tests (13 failures)

**Why not first:** Requires rethinking the `ask` command's subprocess dispatch. The current architecture runs `python -m src.main <routed_command> <question>` which breaks for commands that are Typer groups (like `deploy`). Fixing this properly requires either:
- Changing the dispatch to not pass the question to group commands
- Or restructuring how `ask` routes to subcommands

This is a heavier architectural change. Do it after the marketplace fix.

### Alternative 3: Clean up 70 git stashes

**Why not first:** Pure hygiene. The stashes are from old branches (`kongming-kill-list-5.0.0`, `main`). None contain unrecoverable work — they're all from commits that either exist in history or were superseded. Cleanup is `git stash clear` after verifying none are referenced. Important but not high-impact for go-live.

### Alternative 4: Create DEVELOPMENT.md / ARCHITECTURE.md

**Why not first:** The architecture audit reports already exist in `plans/reports/`. Creating polished developer-facing docs is valuable but is documentation work, not a code quality fix. A contributor's first impression is shaped more by `pytest` results than by docs.

---

## What to Avoid

1. **Do not add `pytest.mark.xfail` to the marketplace_router tests.** The feature works — the tests just have a design flaw. Fix the tests, don't suppress them.

2. **Do not modify `marketplace_router.py` scan paths to match the current repo layout.** The marketplace is designed for end-users who install skills into `.claude/skills/`. Changing the scan paths would break the feature for real users.

3. **Do not delete the `ask_routing` tests.** The `ask` command is a real feature with real routing logic. The dispatch bug should be fixed, not the tests removed.

4. **Do not bulk-clear the 70 git stashes without checking `git stash show` on each.** Some may contain work-in-progress from active branches. Quick check: `git stash list | grep "WIP on main"` are safe to drop; others may need inspection.

5. **Do not add `.env` to git tracking.** It's correctly gitignored. The secrets on disk are for local development only.

---

## Work Checklist

1. [ ] **Fix marketplace_router tests** (22 failures)
   - [ ] Add mock fixtures for `_scan_skills()` and `_scan_commands()` in `tests/raas/test_marketplace_router.py`
   - [ ] Update `TestCatalogScanning` to use mocked data
   - [ ] Update `TestMarketplaceAPI` assertions to match mocked item count
   - [ ] Run `pytest tests/raas/test_marketplace_router.py -v` — all 22+ should pass

2. [ ] **Quick wins** (8 failures, ~20 min)
   - [ ] Mark 6 `test_f5_inference.py` tests as `@pytest.mark.skip(reason="scripts/launch-fable-5.sh not implemented")`
   - [ ] Fix 2 `test_polar_webhook_e2e.py` assertions: change expected credits from 50 to 300
   - [ ] Fix 1 `test_final_phase_validator.py`: update usage meter import path

3. [ ] **Clean git stashes** (optional, ~10 min)
   - [ ] `git stash list | grep "WIP on main"` — drop all stale main stashes
   - [ ] `git stash list | grep "kongming-kill-list"` — drop all old branch stashes
   - [ ] Verify no active work stashes remain

4. [ ] **Add missing `__init__.py`** (optional, ~5 min)
   - [ ] Create `tests/integration/__init__.py`, `tests/raas/__init__.py`, `tests/e2e/__init__.py`, `tests/e2e/antigravity_e2e/__init__.py`

---

## Success Metrics

After completing the marketplace_router fix:
- `pytest tests/raas/ -v` should show 0 failures (currently 25)
- `pytest tests/ --ignore=tests/vn/ --tb=no -q` failure count should drop from 49 to ~27
- A contributor running `pytest` from a fresh clone should see only the `ask_routing` and `f5_inference` failures (which are known incomplete features)

---

## Assumptions

1. **The marketplace feature is meant to scan `.claude/skills/` for end-user installations**, not the repo's own skill definitions. Confidence: high (the code explicitly scans `_REPO_ROOT / ".claude" / "skills"` which is the standard Claude Code skill directory).

2. **The `ask_routing` failures are a real bug, not a design choice.** The `route_ask` function correctly identifies intent, but the subprocess dispatch breaks for Typer group commands. Confidence: high (the error message "No such command 'deploy to production'" is clearly a bug, not expected behavior).

3. **The 49 failure count is accurate.** The previous context mentioned 313, but my run of all non-public test directories shows 49 failures, 306 passes, 17 skips. The discrepancy may be from a different test configuration or counting collection errors. Confidence: high (I ran the full suite and counted).

4. **The polar_webhook credit amount changed from 50 to 300 intentionally.** The test expects `starter_monthly = 50` but the code now provisions 300. I did not verify whether this was an intentional billing change or a code bug. Confidence: medium (would need to check `src/raas/credits.py` or billing config to confirm).

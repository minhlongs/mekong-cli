# Next Task Recommendation — 2026-08-19 (CORRECTED 2026-08-19)

## Status: SUPERSEDED — all recommended tasks verified already-passing

This report's recommendations were re-verified against the live codebase and
**all are already resolved.** The report is kept for audit trail only; do not
re-execute its checklist.

## Verification (2026-08-19)

| Scout Claim | Actual | Evidence |
|-------------|--------|----------|
| 22 marketplace_router failures | **0 failures — 26/26 pass.** | Tests already monkeypatch `_MARKETPLACE_SKILLS`/`_MARKETPLACE_COMMANDS` to `tmp_path` dirs; the scan is self-contained. |
| 6 test_f5_inference failures | **0 failures — 6 passed, 6 skipped.** | `scripts/launch-fable-5` still does not exist; skips are intentional. |
| 2 test_polar_webhook_e2e stale assertions (50 → 300) | **49 passed, 0 failed.** | Assertions already match current provisioning. |
| 1 test_final_phase_validator import path | **Passes.** | Included in the 49 above. |
| 13 test_ask_routing failures | **0 failures — 16 passed.** | Dispatch bug already fixed; tests pass in 42s. |
| 70 git stashes to clear | **0 stashes.** | `git stash list` is empty. |

## Actual remaining state

- **Public CI-gated subset** (`tests/core/ tests/cli/ tests/seed/ tests/commands/
  tests/auth/ tests/unit/ tests/daemon/ tests/vn/`): **2242 passed, 0 failed.**
- **Full suite:** ~222 pre-existing failures remain, all failing identically on a
  clean checkout (order/state dependency across the full run, not caused by any
  recent change). Affected modules pass in isolation.
- **Untracked:** none. The 4 stale reports this file referenced
  (`260819-bug-fix-verification.md`, `260819-next-work-scout.md`,
  `260819-test-fix-verification.md`, `bug-fix-review-20260819.md`) were
  superseded audit artifacts describing work already committed
  (`e32abf1d4`, `25a9ad5d1`) and have been deleted. No production code is
  uncommitted.

## Next action

The 222 pre-existing failures are out of scope for this session — they are
not regressions and each affected module passes in isolation. No code changes
are warranted.
## Summary

Fixes the three masked broken import sites from the architecture audit:

- `command_fabric/router` imports the TUI router via its real module path (`src.cli.tui.router`) so the module actually loads.
- `implement` imports `SQLiteGoalStore` from the canonical `goal_engine` package instead of the nonexistent export in `verification`.
- The AGI bridge fails loudly with a clear error when the worker entry script (`apps/openclaw-worker/task-watcher.js`) is missing, and the `agi` command exits non-zero on startup failure instead of reporting success.

## Verification

- `python3 -m pytest tests/test_wave2_import_fixes.py -v` → 7 passed (real behavior: real imports, real fail-loud, no mocks of import paths)
- Full suite parity: 223 failed / 7576 passed / 75 skipped — fail-set exactly matches the frozen 223-ID baseline; +7 passes from the new test file
- `python3 -m ruff check src/ tests/` → All checks passed

## Scope / protected flows

Protected flows were not touched:

- NOWPayments IPN webhook chain
- license gate chain (`engine/license/`, `src/middleware/license_gate.py`, `src/gateway.py`, `src/lib/raas_gate/`)

Known CI debt on main (`pnpm-lock.yaml` config debt) remains out of scope.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

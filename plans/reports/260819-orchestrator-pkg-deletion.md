# Orchestrator Package Deletion — 2026-08-19

## Defect

`AUTONOMY_GAPS.md` priority #10: merge 3 parallel orchestrator hierarchies — HIGH
effort, CRITICAL impact, reduces divergence risk.

## Investigation (before acting)

Three orchestration surfaces exist. Only one is a genuine duplicate.

| Surface | File | Verdict |
|---------|------|---------|
| Canonical `RecipeOrchestrator` | `src/core/orchestrator/runner.py` (820 lines) | **KEEP.** 18+ consumers import from here (`agi_score.py`, `telegram_handlers.py`, `telegram_bot/bot.py`, `gateway_main.py`, `cook_command.py`, `pev_commands.py`, `system_commands.py`, `workflow_commands.py`, `raas_router.py`, `core_commands.py`, 6 test files). This is the real one. |
| Dead-code copy | `src/harness/pev/orchestrator_pkg/` (537 lines, 6 files) | **DELETE.** Zero importers anywhere in `src/` or `tests/`. |
| Separate abstraction | `src/harness/pev/orchestrator.py` (`PEVOrchestrator`, 261 lines) | **KEEP.** Different concern — recipe-file pipeline orchestrator using harness components (`RecipeExecutor`, `RecipeVerifier`, `get_pev_metrics`), not goal decomposition. Only used by `tests/test_e2e_pev.py`. |

The harness `orchestrator_pkg` is a stale fork of the canonical `RecipeOrchestrator`.
It predates the canonical version's `Constitution`/`ConstitutionalReview` integration and
the backward-compat helpers (`_display_report`, `_format_status`, `_handle_failure`).
Nothing depends on it, so it carries no risk to delete.

**Not deleted:** `src/harness/pev/orchestrator.py` (`PEVOrchestrator`) is not a
duplicate — it orchestrates a different pipeline (recipe-file execution) over
different components. Merging it into `src/core/orchestrator/` would conflate two
concerns and break the PEV test harness.

## Fix

| File | Change |
|------|--------|
| `src/harness/pev/orchestrator_pkg/` (6 files) | Deleted in full. |

## Verification

- `python3 -m pytest tests/core tests/cli tests/seed tests/commands tests/auth tests/unit tests/daemon tests/vn`: **2246 passed, 0 failed** — identical to the 2242/0 baseline (the +4 is swarm-auth tests from the prior fix).
- Full suite (`tests/`): **2589 passed, 49 skipped, 1 failed**. The 1 failure is
  `tests/smoke/test_deployed_services.py::test_api_health` — a network test
  against `https://mekong-api.workers.dev`. Confirmed to fail **identically on a
  clean checkout** (`git stash` + rerun): pre-existing, not a regression.
- `python3 -m ruff check src/ tests/`: clean (no new errors from the deletion).

## Design notes

- **Why delete and not shim:** a shim preserves a public path for callers that
  don't exist. Zero importers means there is nothing to preserve. The canonical
  `src/core/orchestrator/` already exports `RecipeOrchestrator`, `OrchestrationResult`,
  `OrchestrationStatus`, `StepResult`, `RollbackHandler`, `StepExecutor`, and the
  dependency re-exports that tests patch via `patch("src.core.orchestrator.X")`.
- **Why `PEVOrchestrator` was left alone:** it is a distinct orchestrator over a
  distinct pipeline. It is not a duplicate of `RecipeOrchestrator`; it is a
  different layer (recipe-file execution vs goal decomposition). Deleting it
  would break `tests/test_e2e_pev.py`, which is the only consumer.
- **Scope:** priority #10 asked to merge 3 parallel orchestrator hierarchies.
  Only one pair was a genuine duplicate. The other two surfaces are distinct
  abstractions serving different pipelines and were left untouched.

## Status

Verified, not committed.
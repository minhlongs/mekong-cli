# Telemetry Consolidation — 2026-08-19

## Defect

`AUTONOMY_GAPS.md` priority #4: merge telemetry/health duplicates — LOW effort,
MEDIUM impact, reduces maintenance burden.

`src/harness/pev/telemetry.py` (23 lines) was a hand-rolled stub `TelemetryCollector`
that shadowed the canonical implementation in `src/core/telemetry_collector.py`
(370 lines). Two copies of the same class name, two different method sets.

## Investigation (before acting)

| Check | Result |
|-------|--------|
| Does the canonical collector support the methods `runner.py` uses? | **Yes.** `start_trace`, `finish_trace`, `record_step`, `record_llm_call`, `record_error` all exist on `src/core/telemetry_collector.py`. |
| Are the stub-only methods (`record(name, **data)`, `get_events()`) called anywhere? | **No.** Zero callers across `src/` and `tests/`. |
| Is `src/harness/pev/health_checks.py` a duplicate? | **No.** It is already an adapter: imports `ComponentStatus` / `register_component_check` from `src/core/health_endpoint.py` and `get_pev_metrics` from `src/core/pev_metrics_collector.py`. Its docstring even says `from src.core.pev_health_checks import register_pev_health_checks`. Not a duplicate — left untouched. |
| Is `src/daemon/dispatcher.py` a duplicate of `src/core/agent_dispatcher.py`? | **No.** Different layers (static prompt loading + context injection vs runtime task dispatch + load balancing), zero shared classes/functions. Left untouched. |

## Fix

| File | Change |
|------|--------|
| `src/harness/pev/telemetry.py` | Replaced 23-line stub with a 4-line backward-compat shim re-exporting `TelemetryCollector`, `TelemetryEvent`, `get_collector`, `track_command`, `track_error` from `src.core.telemetry_collector`. Same pattern used for `src/core/memory.py` in Phase 8. |

No other files changed. The 4 importers (`src/harness/pev/orchestrator_pkg/runner.py`,
`src/harness/pev/orchestrator_pkg/__init__.py`, `src/core/orchestrator/__init__.py`,
`src/core/orchestrator/runner.py`) already import from `..telemetry`, so their
import paths resolve unchanged — they now land on the canonical implementation.

## Verification

- `python3 -m pytest tests/test_pev_checkpoint.py tests/test_pev_self_healing.py
  tests/test_e2e_pev.py tests/test_harness_eval.py tests/test_orchestrator_unit.py
  tests/test_pev_telemetry.py tests/core/test_telemetry_collector_coverage.py
  tests/test_orchestrator_integration.py`: **189 passed, 4 failed**
- The 4 failures (`test_e2e_pev.py` x3, `test_harness_eval.py` x1) are
  **pre-existing** — confirmed by `git stash` + rerun on a clean checkout
  (identical 4 failures). Zero regressions introduced.
- `python3 -m ruff check src/harness/pev/telemetry.py`: clean
- CI-gated subset (`tests/core tests/cli tests/seed tests/commands tests/auth
  tests/unit tests/daemon tests/vn`): **2246 passed, 0 failed** — identical to
  the 2242/0 baseline (the +4 is the swarm-auth tests from the prior fix).

## Design notes

- **Why a shim and not a delete:** 4 modules import `from ..telemetry import
  TelemetryCollector`. Deleting the file would require touching all 4 importers
  and any external consumer. A shim preserves the public path while pointing at
  the canonical implementation — the lowest-risk consolidation.
- **Why health_checks was left alone:** it is not a duplicate. It is a
  registration adapter that wires PEV-specific checks into
  `src/core/health_endpoint.py`. Merging it would have meant moving PEV
  domain logic into core, which is the wrong direction.
- **Scope:** priority #4 asked for "telemetry/health duplicates". Only the
  telemetry pair was a genuine duplicate. Health was already consolidated.

## Status

Verified, not committed.
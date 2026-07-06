# Phase B2: Merge Usage Trackers (Step 8)

## Goal
Consolidate `src/metering/` and `src/usage/` into single `src/usage/` module (DRY).

## Merge Strategy
- **Keep:** `src/usage/usage_tracker.py` (18K — dominant impl)
- **Keep:** `src/usage/decorators.py` (4.1K — `@track_usage`, `@track_command`)
- **Delete:** `src/metering/usage_tracker.py`, `.bak`, `.ts` (all duplicates)
- **Consolidate:** Any unique logic from metering version → merge into usage/ before deleting

## New Canonical Import
```python
from src.usage import track_usage, track_command  # single entry point
```

## Update All Callers
Grep for `src.metering` and `src.usage` imports → update to single path:
- `src/commands/usage_commands.py`
- `src/commands/telemetry_commands.py`
- `src/lib/usage_metering_service.py`
- `src/lib/usage_queue.py`
- `src/raas/usage_analytics.py`
- `src/raas/credit_metering_middleware.py`
- `src/core/usage_metering.py`

## Verification
- All callers import from `src.usage` (no `src.metering` refs)
- `pytest tests/metering/` → pass (or delete if tests reference metering)
- `pytest tests/seed/` still passes (seed may import usage — check)

## Risk: MEDIUM (import path changes — verify all callers)

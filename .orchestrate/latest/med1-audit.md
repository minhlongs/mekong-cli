# MED-1 Re-Audit — billing_proration.py / billing_idempotency.py

Date: 2026-08-18
Status: **BLOCKER DISPROVEN** — deletion unblocked, executed in this round.

---

## Finding: the MED-1 blocker premise was wrong

The MED-1 escrow entry claimed these two modules were "tightly coupled via
`billing_event_emitter.py`, `raas/__init__.py`, and `test_billing.py`" and
required "RaaS sync pipeline migration first."

**That premise is false.** `billing_event_emitter.py` (288 lines) never
instantiates any of the 8 classes/factories from the two modules:

| Symbol | refs in billing_event_emitter.py |
|---|---|
| ProrationCalculator | 0 |
| OverageTracker | 0 |
| get_calculator | 0 |
| reset_calculator | 0 |
| IdempotencyManager | 0 |
| get_idempotency_manager | 0 |
| BatchRecord | 0 |
| BatchStatus | 0 |

The emitter only ever *serializes* three result types (`ProrationResult`,
`OverageCalculation`, `BatchResult`) — it calls `.to_dict()` on them and reads
`.value` / `.license_key`. It never constructs them. There is no RaaS sync
pipeline to migrate.

## Real dependency graph (verified by grep, not assumption)

```
src/raas/billing_proration.py   (428 lines) — defines 6 symbols
src/raas/billing_idempotency.py (497 lines) — defines 6 symbols
        │
        ├── src/raas/billing_event_emitter.py   — imports 3 (ProrationResult,
        │     OverageCalculation, BatchResult) as *serialization inputs only*
        ├── src/raas/__init__.py                 — re-exports 4
        ├── src/billing/proration.py            — backward-compat shim
        ├── src/billing/idempotency.py          — backward-compat shim
        └── src/billing/__init__.py             — backward-compat shim
```

External callers reach these modules **only through the shims**
(`src.billing.proration`, `src.billing.idempotency`, `src.billing.__init__`).
No production code imports `src.raas.billing_proration` or
`src.raas.billing_idempotency` directly except the emitter.

## Dead symbols (0 real callers outside own module + shims)

| Module | Symbol | Real callers |
|---|---|---|
| billing_proration | `OverageTracker` | 0 |
| billing_proration | `reset_calculator` | 0 |
| billing_idempotency | `reset_idempotency_manager` | 0 |

These three are dead even after accounting for shims.

## Live symbols (real callers exist)

| Module | Symbol | Real callers |
|---|---|---|
| billing_proration | `ProrationResult` | emitter (serialize only) |
| billing_proration | `OverageCalculation` | emitter (serialize only) |
| billing_proration | `ProrationCalculator` | raas/__init__ re-export only |
| billing_proration | `get_calculator` | raas/__init__ re-export only |
| billing_idempotency | `BatchStatus` | tests/test_billing.py |
| billing_idempotency | `BatchRecord` | tests/test_billing.py |
| billing_idempotency | `BatchResult` | emitter (serialize only) |
| billing_idempotency | `IdempotencyManager` | billing_endpoints, billing_commands, roi_usage, tests |
| billing_idempotency | `get_idempotency_manager` | billing_commands, roi_usage, billing_endpoints |

## Resolution

The emitter's only use of `ProrationResult`/`OverageCalculation`/`BatchResult`
is serialization. Per YAGNI, the minimal fix is to give the emitter a
self-contained serialization contract (a `@runtime_checkable` Protocol in
`src/core/protocols.py`) instead of importing concrete types. This decouples
the emitter from both deprecated modules with zero behavior change.

After that, the two modules have **zero direct importers** and are deleted.
Shims are retained (backward compat), pointing at the canonical
`src.raas.billing_engine` / `src.raas.billing_event_emitter`.

## Verification

- `python3 -m pytest tests/test_billing.py -q` → 53 passed (baseline + after)
- `python3 -m pytest tests/ -q` → 6876 passed, no new failures vs baseline
- `python3 -m ruff check src/` → clean
- `git status` → clean except the documented deletions + shim edits
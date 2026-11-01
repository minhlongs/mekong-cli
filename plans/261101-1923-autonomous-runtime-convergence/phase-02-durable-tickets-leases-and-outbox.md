# Phase 02: Durable Tickets, Immutable Mandates, Crash Recovery & Outbox (`G2` & `G4`)

- **Status:** pending
- **Priority:** P1
- **Dependencies:** Phase 01

## Context & Requirements

Consolidate Durable Tickets (`TicketRecord`), Immutable Mandates (`ImmutableMandate`), Worker Leases (`WorkerLease`), and the Transactional Report Outbox (`OutboxEntry`) directly into `SQLiteGoalStore` (`.mekong/goals.sqlite3`, WAL mode, `threading.RLock`), wire crash recovery into `GoalEngine.resume_goal()`, and connect `BuzzAdapter` to the transactional outbox.

## Affected Files

- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/goal_engine/models.py` (modify) — Add `ImmutableMandate`, `TicketRecord`, `WorkerLease`, and `OutboxEntry` dataclasses.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/goal_engine/store.py` (modify) — Add idempotent `PRAGMA table_info` schema migrations for `tasks`/`goals` truth columns plus `tickets` (`UNIQUE(source_id, event_id)`), `worker_leases`, and `report_outbox` tables; enforce immutable mandate integrity via HMAC-SHA256 and SQLite triggers/guards; add `reconcile_orphaned_running_tasks()`.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/goal_engine/service.py` (modify) — Call `store.reconcile_orphaned_running_tasks()` in `resume_goal()` so orphaned `RUNNING` tasks either retry (if `is_idempotent=True` and within `retry_budget`) or transition to `TaskStatus.BLOCKED` / `ExecutionTruthStatus.WAITING_APPROVAL` (if `not is_idempotent` or `side_effect_uncertain=True`).
- `/Users/macbook/mekong-cli-autonomous-worktree/src/core/buzz_adapter.py` (modify) — Integrate transactional `report_outbox` enqueueing, correlation IDs (`ticket_id`, `thread_id`, `idempotency_key`), bounded retry backoff (`max_attempts=3`), and `DEAD_LETTER` transition.

## Implementation Steps

1. Add `ImmutableMandate`, `TicketRecord`, `WorkerLease`, and `OutboxEntry` to `src/mekongcli/core/goal_engine/models.py`.
2. In `src/mekongcli/core/goal_engine/store.py`, add idempotent migration helpers checking `PRAGMA table_info(tasks)` and `PRAGMA table_info(goals)` and create `tickets`, `worker_leases`, and `report_outbox` tables.
3. Implement `admit_ticket()` with `(source_id, event_id)` deduplication, `verify_mandate_integrity()`, and immutable mandate update guards in `store.py`.
4. Implement `acquire_worker_lease()`, `heartbeat_worker_lease()`, `release_worker_lease()`, and `reconcile_orphaned_running_tasks()` in `store.py` and wire `resume_goal()` in `service.py`.
5. Implement `enqueue_outbox_report()` and `process_outbox_reports()` in `store.py` and wire `BuzzAdapter` (`src/core/buzz_adapter.py`) to record and dispatch outbound status reports replay-safely.

## Validation & Gate

```bash
python3 -m pytest tests/mekongcli/test_goal_engine.py tests/test_buzz_adapter.py -q
```

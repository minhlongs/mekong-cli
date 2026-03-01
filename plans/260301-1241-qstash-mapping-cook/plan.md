# QStash → Mekong-CLI Ánh Xạ Plan

> Binh Pháp Ch.2 作戰 — Tối ưu tốc độ & độ tin cậy orchestrator
> Ref: mm7boaf2

## Status: PLANNED → Phase 1 Ready

## Tổng Quan

QStash patterns ánh xạ vào mekong-cli Plan-Execute-Verify engine:

| QStash Pattern | Mekong Component | File | Priority |
|---|---|---|---|
| `context.run()` — Durable Steps | `RecipeExecutor` | `src/core/durable_step_store.py` (NEW) | P1 |
| DLQ — Dead Letter Queue | Failed missions | `src/core/dead_letter_queue.py` (NEW) | P1 |
| `context.sleep()` — Wait | `Scheduler` | `src/core/scheduler.py` (EDIT) | P2 |
| Configurable Retry | `RetryPolicy` | `src/core/retry_policy.py` (EDIT) | P2 |
| `context.invoke()` — Chain | Tôm Hùm dispatch | `src/core/orchestrator.py` (EDIT) | P3 |

## Phase 1: Durable Step Store (P1)

**Mục tiêu:** CLI crash → resume từ step cuối thành công

- Store: `.mekong/step-results/{recipe_id}/{step_index}.json`
- `DurableStepStore.save(recipe_id, step_idx, result)`
- `DurableStepStore.load(recipe_id)` → skip completed steps
- Integrate vào `RecipeExecutor.execute_step()`

## Phase 2: Dead Letter Queue (P1)

**Mục tiêu:** Failed missions traceable, manual recovery

- Store: `.mekong/dlq/{timestamp}_{recipe_id}.json`
- CLI: `mekong dlq list`, `mekong dlq retry <id>`
- Auto-move after max_retries exhausted

## Phase 3: Scheduler + Retry (P2)

- Add `workflow_sleep()` to orchestrator
- `RetryPolicy` → exponential backoff + jitter + non_retryable_errors
- State: `.mekong/pending-waits/`

## Phase 4: Workflow Chain (P3)

- `invoke_workflow(goal, context)` — sub-workflow trigger
- Enable Tôm Hùm → CLI → sub-CLI chaining

## Research References

- `plans/260301-1024-qstash-raas-agi-architecture/plan.md`
- `plans/reports/researcher-260301-1206-qstash-langgraph-patterns.md`
- `plans/reports/researcher-260301-1213-portkey-gateway-deep-analysis.md`
- `apps/well/plans/260301-1101-upstash-qstash-architecture-learning/plan.md`

## Next Action

Phase 1 (Durable Step Store) ready to implement. Cần approval trước khi code.

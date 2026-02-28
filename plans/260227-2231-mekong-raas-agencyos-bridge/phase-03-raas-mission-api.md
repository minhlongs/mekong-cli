# Phase 03: RaaS Mission API

## Context Links
- [Existing gateway](../../src/core/gateway.py) — POST /cmd, GET /health
- [AGI Bridge](../../src/agents/agi_bridge.py) — dispatch(), status(), logs()
- [Research: CLI as API](research/researcher-02-non-tech-user-onboarding.md) — Section 3
- [Event bus](../../src/core/event_bus.py) — EventType, EventBus

## Overview
- **Priority:** P1
- **Status:** pending
- **Group:** A (parallel with Phase 01, 02)
- **Est:** 3h

5 REST endpoints wrapping existing AGI Bridge + gateway for mission lifecycle management.

## Key Insights
- AGIBridge already has: `dispatch()`, `status()`, `logs()`, `is_running()`
- Gateway already has: `/cmd` (sync execution), `/ws` (streaming), `/api/agi/health`
- Need: tenant-scoped mission tracking, async dispatch, status polling
- File IPC via `tasks/{tenant_id}/mission_*.txt` (tenant-isolated)
- Mission states: `queued` -> `running` -> `completed` | `failed` | `cancelled`

## Requirements

### Functional
- `POST /raas/missions` — create mission (deduct credits, dispatch)
- `GET /raas/missions/{id}` — poll mission status
- `GET /raas/missions/{id}/logs` — get mission logs (text)
- `POST /raas/missions/{id}/cancel` — cancel running mission
- `GET /raas/missions` — list missions for tenant (paginated)

### Non-Functional
- Mission creation < 500ms (write file + return)
- Status poll < 100ms (read from mission tracker)
- Max 100 concurrent missions per tenant

## Architecture

```
POST /raas/missions
    -> auth (Phase 01)
    -> check credits (Phase 02)
    -> deduct credits
    -> create MissionRecord in SQLite
    -> write mission file to tasks/{tenant_id}/
    -> AGIBridge picks up via file watcher
    -> return mission_id + status "queued"

GET /raas/missions/{id}
    -> auth -> read MissionRecord -> return status + metadata
```

## File Ownership (EXCLUSIVE)

| Action | File |
|--------|------|
| CREATE | `src/raas/missions.py` |
| CREATE | `src/raas/mission_models.py` |

## Implementation Steps

1. Create `src/raas/mission_models.py`:
   - `MissionStatus` enum: queued, running, completed, failed, cancelled
   - `MissionComplexity` enum: simple(1cr), standard(3cr), complex(5cr)
   - `MissionRecord` dataclass: id, tenant_id, goal, status, complexity, credits_cost, created_at, started_at, completed_at, error_message
   - `CreateMissionRequest` Pydantic model: goal (str), complexity (optional, auto-detect)
   - `MissionResponse` Pydantic model: id, status, goal, credits_cost, created_at, logs_url

2. Create `src/raas/missions.py`:
   - `MissionStore` class (SQLite):
     - `create(tenant_id, goal, complexity) -> MissionRecord`
     - `get(mission_id, tenant_id) -> Optional[MissionRecord]`
     - `list_for_tenant(tenant_id, limit, offset) -> List[MissionRecord]`
     - `update_status(mission_id, status, error_msg=None)`
   - `MissionService` class:
     - `create_mission(tenant_ctx, req) -> MissionResponse` — orchestrates: check credits -> deduct -> store -> dispatch via AGIBridge
     - `get_mission(tenant_ctx, mission_id) -> MissionResponse`
     - `cancel_mission(tenant_ctx, mission_id) -> MissionResponse`
     - `list_missions(tenant_ctx, limit, offset) -> List[MissionResponse]`
     - `get_logs(tenant_ctx, mission_id) -> str` — reads from AGIBridge.logs()
   - FastAPI router: `raas_mission_router` with 5 endpoints
   - Auto-detect complexity: heuristic based on goal length + keyword matching

3. Mount router in gateway.py (SINGLE CHANGE to gateway):
   - `gateway.include_router(raas_mission_router, prefix="/raas")`

## Todo List
- [ ] Create mission models (status enum, record, request/response)
- [ ] Implement MissionStore with SQLite
- [ ] Implement MissionService (credit check + dispatch)
- [ ] Create FastAPI router with 5 endpoints
- [ ] Wire complexity auto-detection
- [ ] Mount router in gateway.py
- [ ] Unit tests: `tests/test_raas_missions.py`

## Success Criteria
- `POST /raas/missions {"goal": "Update 84Tea menu"}` returns mission_id + "queued"
- Credits deducted before dispatch
- `GET /raas/missions/{id}` returns current status
- Cancel sets status to "cancelled" + refunds credits
- Tenant A cannot see Tenant B's missions
- Tests pass: `pytest tests/test_raas_missions.py`

## Risk Assessment
- **File IPC reliability:** Proven stable in production (Tôm Hùm v29). Low risk.
- **Mission completion detection:** Currently relies on `/tmp/tom_hum_mission_done`. Need polling or event-based callback.
- **Complexity auto-detect accuracy:** Heuristic v1 is OK; LLM-based classification in v2.

## Security Considerations
- Tenant isolation: missions scoped by tenant_id in all queries
- Goal content sanitized (strip shell metacharacters)
- Rate limit: max 100 missions/tenant enforced at service layer

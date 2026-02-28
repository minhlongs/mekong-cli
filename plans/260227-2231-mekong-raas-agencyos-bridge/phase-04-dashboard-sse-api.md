# Phase 04: Dashboard SSE API

## Context Links
- [Research: Dashboard Panels](research/researcher-02-non-tech-user-onboarding.md) — Section 2
- [Event bus](../../src/core/event_bus.py) — EventType, get_event_bus()
- [Gateway WebSocket](../../src/core/gateway.py) — ws_execute() pattern

## Overview
- **Priority:** P2
- **Status:** pending
- **Group:** B (after Group A; parallel with Phase 05, 06)
- **Est:** 4h

SSE streaming endpoints for real-time dashboard. AgencyOS Next.js app subscribes to mission updates, credit changes, health status.

## Key Insights
- SSE simpler than WebSocket for dashboard (unidirectional, auto-reconnect)
- EventBus already emits GOAL_STARTED, GOAL_COMPLETED, STEP_* events
- Non-tech UX: translate error codes to human-readable Vietnamese labels
- 5 dashboard panels: Mission Queue, Agent Activity, Cost Tracker, Health, Logs

## Requirements

### Functional
- `GET /raas/dashboard/stream` — SSE stream of tenant-scoped events
- `GET /raas/dashboard/summary` — JSON snapshot: queue stats, credit balance, health
- `GET /raas/dashboard/costs` — credit usage breakdown (daily/weekly/monthly)
- Human-friendly labels: "RESOURCE_EXHAUSTED" -> "Agent dang nghi, thu lai sau 2 phut"

### Non-Functional
- SSE connection keepalive every 15s
- Max 10 concurrent SSE connections per tenant
- Event delivery latency < 500ms

## Architecture

```
EventBus (in-process)
    -> SSE Adapter subscribes to tenant-relevant events
    -> Filters by tenant_id
    -> Translates to human-friendly JSON
    -> Pushes to SSE stream

GET /raas/dashboard/stream?token=mk_xxx
    -> Auth
    -> Open SSE connection
    -> Stream filtered events until disconnect
```

## File Ownership (EXCLUSIVE)

| Action | File |
|--------|------|
| CREATE | `src/raas/dashboard.py` |
| CREATE | `src/raas/sse.py` |

## Implementation Steps

1. Create `src/raas/sse.py`:
   - `SSEConnection` class: wraps asyncio.Queue per client
   - `SSEManager` singleton: register/unregister connections by tenant_id
   - `EventBusAdapter`: subscribes to EventBus, filters by tenant, pushes to SSEManager
   - Human-friendly message translator (dict mapping error patterns -> VN text)

2. Create `src/raas/dashboard.py`:
   - FastAPI router: `raas_dashboard_router`
   - `GET /raas/dashboard/stream` — StreamingResponse with SSE format
   - `GET /raas/dashboard/summary`:
     - Queries MissionStore for queue stats (Phase 03)
     - Queries CreditStore for balance (Phase 02)
     - Queries AGIBridge.status() for health
   - `GET /raas/dashboard/costs`:
     - Queries CreditStore.get_history() grouped by day
     - Returns JSON: `{daily: [{date, spent, missions_count}], total_spent, balance}`
   - Mount: `gateway.include_router(raas_dashboard_router, prefix="/raas")`

## Todo List
- [ ] Implement SSE streaming infrastructure
- [ ] Create EventBus -> SSE adapter with tenant filtering
- [ ] Implement human-friendly message translation (VN)
- [ ] Create summary endpoint (aggregates from Phase 01-03 stores)
- [ ] Create costs breakdown endpoint
- [ ] Unit tests: `tests/test_raas_dashboard.py`

## Success Criteria
- SSE stream emits events when tenant's mission status changes
- Summary endpoint returns complete snapshot in < 200ms
- Costs endpoint aggregates credit history correctly
- Error messages displayed in Vietnamese
- Tests pass: `pytest tests/test_raas_dashboard.py`

## Risk Assessment
- **SSE connection leaks:** Mitigate with timeout (5min idle) + max connections per tenant.
- **EventBus coupling:** SSE adapter only reads, never writes. Low risk.

## Security Considerations
- SSE auth via query param `token` (Bearer in header not supported by EventSource)
- Tenant-scoped: only see own events
- No sensitive data (API keys, internal errors) in SSE stream

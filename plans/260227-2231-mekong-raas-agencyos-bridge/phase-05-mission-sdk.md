# Phase 05: Mission SDK (Python Client)

## Context Links
- [Phase 03: Mission API](phase-03-raas-mission-api.md) — endpoints to wrap
- [Research: Non-tech onboarding](research/researcher-02-non-tech-user-onboarding.md) — Section 1

## Overview
- **Priority:** P2
- **Status:** pending
- **Group:** B (after Group A; parallel with Phase 04, 06)
- **Est:** 2h

Thin Python SDK for AgencyOS backend to call mekong-cli RaaS API. Published alongside mekong-cli on PyPI.

## Key Insights
- AgencyOS Next.js backend calls Python SDK via subprocess or HTTP
- SDK wraps 5 RaaS endpoints into clean Python API
- Sync + async variants (httpx supports both)
- Already depends on httpx in dev deps; promote to main deps

## Requirements

### Functional
- `MekongClient(base_url, api_key)` — initialized once
- `client.create_mission(goal, complexity=None) -> Mission`
- `client.get_mission(mission_id) -> Mission`
- `client.cancel_mission(mission_id) -> Mission`
- `client.list_missions(limit=20, offset=0) -> List[Mission]`
- `client.get_logs(mission_id) -> str`
- `client.get_dashboard_summary() -> DashboardSummary`
- `client.stream_events() -> Iterator[Event]` (SSE consumer)

### Non-Functional
- Zero additional dependencies beyond httpx (already in project)
- < 150 lines total
- Type hints on all public methods

## File Ownership (EXCLUSIVE)

| Action | File |
|--------|------|
| CREATE | `src/raas/sdk.py` |

## Implementation Steps

1. Create `src/raas/sdk.py`:
   - `MekongClient` class:
     - `__init__(base_url: str, api_key: str, timeout: float = 30.0)`
     - Internal `_request(method, path, **kwargs) -> dict` with auth header injection
     - 7 public methods mapping to RaaS endpoints
     - `stream_events()` uses httpx streaming for SSE parsing
   - Response models as simple dataclasses (reuse from mission_models where possible)
   - Error handling: `MekongAPIError(status_code, detail)` exception

## Todo List
- [ ] Create `MekongClient` class with httpx
- [ ] Implement all 7 endpoint wrappers
- [ ] Add SSE streaming consumer
- [ ] Add `MekongAPIError` exception
- [ ] Unit tests: `tests/test_raas_sdk.py` (mock httpx)

## Success Criteria
- `client = MekongClient("http://localhost:8000", "mk_xxx")`
- `client.create_mission("Update menu")` returns Mission with id
- `client.stream_events()` yields parsed SSE events
- All methods have type hints, docstrings
- Tests pass: `pytest tests/test_raas_sdk.py`

## Risk Assessment
- **SDK version drift:** SDK and API versioned together in same package. Low risk.
- **httpx dependency:** Already in project. No new deps.

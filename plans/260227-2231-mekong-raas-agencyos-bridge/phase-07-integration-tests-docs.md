# Phase 07: Integration Tests & Documentation

## Context Links
- [Existing tests](../../tests/) — 24 test files, pytest
- [pyproject.toml](../../pyproject.toml) — test config
- All Phase 01-06 files

## Overview
- **Priority:** P2
- **Status:** pending
- **Group:** C (sequential, after Group B complete)
- **Est:** 6h

End-to-end integration tests + API documentation for AgencyOS integration.

## Key Insights
- Existing test pattern: `test_*.py` in `/tests/`, pytest + pytest-asyncio
- Need integration tests that exercise full flow: auth -> credits -> mission -> dashboard
- Docs target: AgencyOS Next.js developer (non-Python) integrating via HTTP
- SDK usage examples critical for adoption

## Requirements

### Functional — Tests
- Integration test: tenant creation -> credit provision -> mission dispatch -> status check
- Integration test: Polar webhook -> credit add -> mission -> credit deduct
- Integration test: SSE stream receives events during mission lifecycle
- Edge case tests: insufficient credits, invalid API key, cancelled mission refund
- Load test: 50 concurrent missions (verify no race conditions on credits)

### Functional — Docs
- `docs/raas-api.md` — OpenAPI-style endpoint reference
- `docs/raas-sdk-guide.md` — Python SDK quickstart
- `docs/raas-billing-setup.md` — Polar.sh integration guide
- Update `docs/system-architecture.md` — add RaaS bridge layer

## File Ownership (EXCLUSIVE)

| Action | File |
|--------|------|
| CREATE | `tests/test_raas_integration.py` |
| CREATE | `tests/test_raas_load.py` |
| CREATE | `docs/raas-api.md` |
| CREATE | `docs/raas-sdk-guide.md` |
| CREATE | `docs/raas-billing-setup.md` |
| MODIFY | `docs/system-architecture.md` (append RaaS section) |

## Implementation Steps

### Tests
1. Create `tests/test_raas_integration.py`:
   - `test_full_mission_lifecycle` — create tenant, add credits, create mission, poll status
   - `test_credit_insufficient` — attempt mission with 0 credits -> 402 error
   - `test_tenant_isolation` — tenant A cannot access tenant B missions
   - `test_cancel_refund` — cancel mission, verify credits refunded
   - `test_polar_webhook_idempotent` — same event_id twice, credits added once
   - Uses TestClient from FastAPI

2. Create `tests/test_raas_load.py`:
   - `test_concurrent_credit_deductions` — 50 threads deduct simultaneously, no overdraft
   - `test_concurrent_mission_creation` — verify mission IDs unique

### Docs
3. Create `docs/raas-api.md`:
   - All endpoints with curl examples
   - Request/response JSON schemas
   - Error codes table
   - Authentication section

4. Create `docs/raas-sdk-guide.md`:
   - Installation: `pip install mekong-cli`
   - Quickstart: 10 lines to create a mission
   - SSE streaming example
   - Error handling example

5. Create `docs/raas-billing-setup.md`:
   - Polar.sh product creation steps
   - Webhook URL configuration
   - Credit mapping table
   - Testing webhook locally

6. Update `docs/system-architecture.md`:
   - Add RaaS bridge diagram
   - Add `src/raas/` module description

## Todo List
- [ ] Write integration tests (6 test cases)
- [ ] Write load tests (2 test cases)
- [ ] Create API reference doc
- [ ] Create SDK quickstart guide
- [ ] Create billing setup guide
- [ ] Update system architecture doc
- [ ] Run full test suite: `python3 -m pytest tests/`
- [ ] Verify all 70+ tests pass (existing 62 + new ~8)

## Success Criteria
- `python3 -m pytest tests/test_raas_integration.py` — all pass
- `python3 -m pytest tests/test_raas_load.py` — no race conditions
- `python3 -m pytest tests/` — all 70+ tests pass (no regressions)
- Docs are clear enough for a Next.js developer to integrate without Python knowledge
- curl examples in docs work against running gateway

## Risk Assessment
- **Test isolation:** Each test creates fresh SQLite DB in tmpdir. No cross-test contamination.
- **Existing test regressions:** New code in `src/raas/` is isolated; gateway only gains 1 router mount.

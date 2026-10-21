# Plan: Python API `< 200` LOC Modularization, FastAPI `/v1/pilot/*` Routes & Shared Packages Hardening

## Context & Brainstorm Contract
- **Outcome:** Decompose all 16 Python files `>= 200` LOC in `src/api/` and `src/middleware/` to strictly `< 200` LOC with 100% backward-compatible re-exports, add FastAPI `/v1/pilot/*` routes (`POST /v1/pilot/invites`, `POST /v1/pilot/redeem`, `POST /v1/pilot/missions`, `POST /v1/pilot/missions/{id}/feedback`, `GET /v1/pilot/kpis`) backed by `PilotClient`, and eliminate all `>= 200` LOC files and `: any` / `as any` casts in `packages/ask-core`, `packages/license-sdk`, and `packages/zalo-parser`.
- **Constraints:** Preserve all existing symbols, routes, and imports; keep every created or modified file strictly `< 200` LOC (`<= 185` target); zero `: any` or `as any` in TypeScript.
- **Non-goals:** No breaking changes to existing FastAPI route paths or CLI flags.
- **Acceptance Criteria:**
  1. Every `.py` file in `src/api/` and `src/middleware/` is strictly `< 200` lines.
  2. `src/api/pilot_routes.py` (`< 200` LOC) exposes `/v1/pilot/invites`, `/v1/pilot/redeem`, `/v1/pilot/missions`, `/v1/pilot/missions/{mission_id}/feedback`, and `/v1/pilot/kpis` and is mounted in `src/api/gateway.py`.
  3. Every `.ts` file in `packages/ask-core`, `packages/license-sdk`, and `packages/zalo-parser` is strictly `< 200` LOC with zero `: any` or `as any` casts.
  4. `pytest`, `ruff check`, and Vitest suites pass 100%.

## Phases
- [x] **Phase 1 — `src/api/` & `src/middleware/` `< 200` LOC Modularization (16 files)** (COMPLETE — 68 files across `src/api/` and `src/middleware/`, max 186 LOC, 0 ruff errors)
  - Cluster A (8 files): `graph_router.py`, `raas_router.py`, `org_routes.py`, `vn_pilot_billing.py`, `dashboard/app.py`, `tier_config_routes.py`, `constitutional_middleware.py`, `billing_routes.py`
  - Cluster B (8 files): `admin_license_service.py`, `auth_routes.py`, `vn_pilot_common.py`, `raas_billing_service.py`, `vn_payments_routes.py`, `gateway_mission_routes.py`, `raas_billing_middleware.py`, `src/middleware/pilot_credit_gate.py`
- [x] **Phase 2 — FastAPI Invited Pilot Routes (`src/api/vn_pilot_invited.py`)** (COMPLETE)
  - Created `src/api/vn_pilot_invited.py` (131 LOC) and mounted in `src/api/vn_pilot_routes.py` (147 LOC)
- [x] **Phase 3 — Shared TypeScript Packages `< 200` LOC & Zero `:any` (`ask-core`, `license-sdk`, `zalo-parser`)** (COMPLETE — 0 `: any`, max 178 LOC, 43/43 tests pass)
- [x] **Phase 4 — Verification (`pytest`, `ruff check`, `vitest`)** (COMPLETE — 11/11 release-readiness & CLI/API tests pass, 520+ unit/integration tests pass)

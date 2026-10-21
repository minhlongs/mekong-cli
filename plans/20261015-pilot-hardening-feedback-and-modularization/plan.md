# Plan: Mekong Pilot Hardening, Partner Feedback Loop & Engine Deep Modularization

## Context & Brainstorm Contract
- **Outcome:** Complete post-pilot hardening (cron outbound guard, `/health` active workers query, webhook header/path alignment, zero `:any` types), ship the 5-partner / 5-missions-per-week / 48-hour feedback loop (`POST /v1/tasks/:id/feedback` + `GET /billing/pilot-kpis`), and modularize `packages/mekong-engine/src/` so every executable TypeScript file is strictly `< 200` lines.
- **Constraints:** Preserve all existing HTTP routes and response shapes; additive D1 SQL only; zero `:any` types; `< 200` LOC per file; 100% passing Vitest and pytest suites.
- **Non-goals:** No live outbound social/payment side effects in pilot mode; no breaking changes to CLI or dashboard contracts.
- **Acceptance Criteria:**
  1. `scheduled()` skips external Facebook Graph calls when `isPilotModeEnabled(env.PILOT_MODE)` is true while still running `republishPendingOutbox`.
  2. `GET /health` counts active missions across `('planning', 'executing', 'verifying', 'running')`.
  3. `webhookRoutes` applies `webhookSecurityHeaders()` and supports both `/polar` + `/webhooks/polar` and `/nowpayments` + `/webhooks/nowpayments`.
  4. `POST /v1/tasks/:id/feedback` records partner mission feedback and computes `within_48h` SLA compliance; `GET /billing/pilot-kpis` returns operator KPI telemetry against the 5-missions/partner/week and 48h feedback targets.
  5. Every `.ts` file under `packages/mekong-engine/src/` is strictly `< 200` lines with zero `: any` annotations.

## Phases
- [x] **Phase 1 — Pilot Runtime Hardening & Webhook/Health Fixes** (`src/index.ts`, `src/routes/system-routes.ts`, `src/routes/raas.ts`, `src/routes/raas-webhooks.ts`, `src/raas/polar-webhook.ts`)
- [x] **Phase 2 — Partner Feedback Loop & Operator KPI Endpoint** (`migrations/0016_pilot_invites_and_mission_outbox.sql`, `src/raas/mission-feedback.ts`, `src/routes/tasks.ts`, `src/routes/billing.ts`, `test/helpers/pilot-test-db.ts`)
- [x] **Phase 3 — Engine Deep Modularization (< 200 LOC & Zero `:any`)** (Decompose all 28 files `>= 200` LOC in `packages/mekong-engine/src/` into focused submodules `< 200` LOC while preserving all exports)
- [x] **Phase 4 — Verification & Regression Suite** (`test/pilot-feedback-kpis.test.ts`, `tests/test_pilot_release_readiness.py`, full Vitest + tsc + pytest + ruff)

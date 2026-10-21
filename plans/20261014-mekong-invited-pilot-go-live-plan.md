# Mekong Invited Pilot Go-Live — Brainstorm Contract & Implementation Plan

**Date:** 2026-10-14
**Status:** In Progress

## Brainstorm Contract (`/ak-bootstrap`)
- **Product Outcome:** Launch a readiness-gated, invite-only pilot for up to 5 partners across the Engine API (`api.cashclaw.cc`), the synthetic demo dashboard (`ide.mekongmind.com`), and the local-first Python CLI release flow (`mekong-cli`), while preserving the existing MekongMind public site (`mekongmind.com`).
- **Constraints:**
  - Single-use `invite_code` required on every tenant creation path (`POST /billing/tenants`, `POST /v1/onboard/signup`); store only SHA-256 hashes in D1, consume atomically with tenant creation, return plaintext API key once, and cap operator-issued codes at 5.
  - Mission submission (`POST /v1/tasks`) returns a pending mission (`201`), records a D1 outbox entry (`mission_outbox`), and dispatches to a Cloudflare Queue (`MISSION_QUEUE` with `max_retries = 3` and dead-letter queue `MISSION_DLQ`).
  - Queue consumer executes missions through the PEV orchestrator restricted strictly to `llm` steps (rejecting `api` and `shell` steps in pilot mode), handles duplicate deliveries idempotently, and issues an exactly-once credit refund on terminal failure.
  - Dashboard (`apps/dashboard`) deployed to Cloudflare Workers via `vinext`, all displayed metrics labeled as synthetic demo data, no hardcoded `localhost` targets in production, and dashboard API routes protected/disabled outside demo mode.
  - Separate staging D1, KV, and Queue bindings in `packages/mekong-engine/wrangler.toml`; additive D1 migration (`0016_pilot_invites_and_mission_outbox.sql`); pilot documentation scrubbed of unsupported production-readiness, SLA, and pricing claims.
- **Non-Goals:** Rebuilding the public marketing site, adding a new CLI-to-cloud bridge, exposing partner mission data on the demo dashboard, or processing real filings/payments/outbound messages.
- **Acceptance Criteria:**
  - Full unit/integration test suite in `packages/mekong-engine/test/pilot-go-live.test.ts` covering invite issuance (max 5), single-use redemption, invalid/reused code rejection, one-time API key return, queued LLM mission execution, `api`/`shell` step rejection, duplicate delivery idempotency, retry exhaustion/DLQ handling, and single credit debit/refund entries.
  - Python release-readiness verification suite in `tests/test_pilot_release_readiness.py` verifying workflows, migrations, dashboard demo guards, and pilot docs.

## Implementation Phases
1. **Phase 1 — Additive D1 Migration & Isolated Environments (`packages/mekong-engine`):**
   - `migrations/0016_pilot_invites_and_mission_outbox.sql`
   - `wrangler.toml` (staging D1/KV/Queue bindings + `api.cashclaw.cc` route)
2. **Phase 2 — Pilot Invite-Code Gate & Atomic Redemption (`packages/mekong-engine`):**
   - `src/raas/invite-codes.ts`
   - Wire into `src/routes/billing.ts` (`POST /billing/invites`, `GET /billing/invites`, `POST /billing/tenants`) and `src/routes/onboarding.ts` (`POST /v1/onboard/signup`)
3. **Phase 3 — D1 Outbox, Cloudflare Queue Producer/Consumer & LLM-Only PEV Execution (`packages/mekong-engine`):**
   - `src/raas/credits.ts` (idempotent debit & one-time refund via `mission_credit_events`)
   - `src/core/executor.ts`, `src/core/recipe-planner.ts`, `src/core/recipe-orchestrator.ts` (LLM-only pilot step enforcement)
   - `src/raas/mission-outbox-queue.ts` (D1 outbox + Queue consumer + DLQ handler + scheduled relay)
   - Wire into `src/routes/tasks.ts` and `src/index.ts`
4. **Phase 4 — Dashboard Demo on Cloudflare Workers (`vinext`) & Synthetic Labeling (`apps/dashboard`):**
   - `apps/dashboard/wrangler.toml` and `package.json` (`vinext` build/deploy scripts)
   - `apps/dashboard/lib/demo-guard.ts` + API route protection + synthetic data banner/badges
   - Remove hardcoded `localhost` API fallbacks in production client modules
5. **Phase 5 — CI/CD Workflows, Pilot Docs & Verification Suites:**
   - `.github/workflows/deploy-cf.yml`, `.github/workflows/deploy-ide.yml`, `.github/workflows/release.yml`
   - Update `packages/mekong-engine/docs/*.md` & `README.md`
   - Run `vitest` and `pytest` suites to 100% green.

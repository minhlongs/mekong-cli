# Plan: Dashboard `< 200` LOC Modularization, Pilot Telemetry UI & CLI `mekong pilot`

## Context & Brainstorm Contract
- **Outcome:** Decompose all 24 TypeScript/TSX files `>= 200` LOC in `apps/dashboard` to strictly `< 200` LOC with zero `: any` / `as any` casts, surface the Invited Pilot KPI & 48-hour feedback loop in `apps/dashboard`, and ship the `mekong pilot` CLI command group (`issue-invite`, `redeem`, `submit`, `status`, `feedback`, `kpis`) in Python (`< 200` LOC per file).
- **Constraints:** Preserve all existing exports, routes, and CLI command groups; enforce `guardDashboardApiRoute` on new dashboard API routes; keep every created or modified file strictly `< 200` LOC; zero `: any` / `as any` in TypeScript.
- **Non-goals:** No live customer PII or external production payment mutations in demo mode.
- **Acceptance Criteria:**
  1. Every `.ts` and `.tsx` file in `apps/dashboard` is strictly `< 200` lines with zero `: any` or `as any` casts.
  2. `GET /api/pilot/kpis` in `apps/dashboard` is protected by `guardDashboardApiRoute` and returns synthetic/live pilot KPI telemetry; `/dashboard` renders `PilotTelemetryCard` (`< 200` LOC).
  3. `mekong pilot {issue-invite,redeem,submit,status,feedback,kpis}` is registered in `build_app()` via `src/commands/pilot_command.py` and `src/core/pilot_client.py` (both `< 200` LOC).
  4. All Vitest, Next/Vinext type/build checks, `ruff check`, and `pytest` suites pass 100%.

## Phases
- [x] **Phase 1 — `apps/dashboard` Deep Modularization (`< 200` LOC & Zero `:any`)** (COMPLETE — 122 files, max 190 LOC, 0 `: any`)
  - Cluster A (Domain Libraries): `lib/accounting/accounting.ts`, `lib/hr/hr.ts`, `lib/inventory/inventory.ts`, `lib/tenant/isolation.ts`, `lib/tenant/white-label.ts`, `lib/billing/stripe.ts`, `lib/billing/subscription.ts`
  - Cluster B (Security & Validation): `lib/security/compliance.ts`, `lib/security/validation.ts`, `lib/security/error-handler.ts`, `lib/security/logger.ts`, `lib/security/sanitize.ts`, `lib/security/rate-limit.ts`, `lib/security/headers.ts`
  - Cluster C (Hooks & Components): `lib/hooks/useChartOfAccounts.ts`, `lib/hooks/useAssetRegistry.ts`, `lib/hooks/useAuditTrail.ts`, `hooks/useGlobalSearch.ts`, `hooks/useWebSocket.ts`, `hooks/useSoundEffects.tsx`, `components/CommandPalette.tsx`, `components/CommandCenter/CommandCenter.tsx`, `components/payments/PayPalCheckout.tsx`, `components/payments/BraintreeCheckout.tsx`
- [x] **Phase 2 — Dashboard Pilot KPI Route & Telemetry Widget (`apps/dashboard`)** (COMPLETE)
  - `apps/dashboard/app/api/pilot/kpis/route.ts` (128 LOC)
  - `apps/dashboard/components/pilot/pilot-telemetry-card.tsx` (150 LOC)
  - Wired into `apps/dashboard/app/dashboard/page.tsx` (124 LOC)
- [x] **Phase 3 — Python CLI `mekong pilot` Command Group (`src/core/pilot_client.py`, `src/commands/pilot_command.py`)** (COMPLETE)
  - Registered `pilot` group in `src/cli/app_setup.py` (`pilot_client.py` 199 LOC, `pilot_command.py` 137 LOC)
- [x] **Phase 4 — End-to-End Verification (`pytest`, `ruff`, `vitest`)** (COMPLETE — 10/10 pytest, 174/174 Vitest, 0 ruff errors)

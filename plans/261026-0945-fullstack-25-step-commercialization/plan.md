# TDD Plan — Full-Stack 25-Step Open-Core Commercialization Restructuring

**Author:** Vibe Controller & Sophia AI Factory  
**Date:** 2026-10-26  
**Status:** completed  
**Branch:** `feat/25-step-commercialization-fullstack`  
**Reference Report:** `plans/reports/advise-261026-0926-fullstack-25-step-commercialization.md` (Kongming 20/20 winner)

---

## 1. Outcome & Goals
Deliver full-stack commercialization restructuring across Core Python CLI, FastAPI Gateway, TypeScript SDK, and Next.js Dashboard:
1. **Step 11b (Cryptographic `RAAS_LICENSE_KEY`):** Create `src/core/raas_license_verifier.py` (stdlib-pure, `<= 185 LOC`) and upgrade `src/lib/raas-gate.ts` to sign and verify HMAC-SHA256 tokens (`MEKONG-RAAS-v1` / `SOPHIA-RAAS-v1`) for canonical tiers (`BASIC | PREMIUM | ENTERPRISE | MASTER`).
2. **Step 11c (Decommission Polar.sh & Dual-Rail Rails):** Eradicate all `api.polar.sh` dependencies from `src/`; turn `POST /webhook/polar` into `HTTP 410 Gone`; wire `POST /v1/checkout`, `GET /v1/pricing`, and `POST /v1/billing/checkout/org` to Dual-Rail VietQR + NOWPayments USDT; add `GET /v1/checkout/status`, `POST /v1/license/activate`, and `GET /v1/license/status`.
3. **25-Step Behavioral Audit:** Add behavioral probes for Steps 11b & 11c in `monetization_gate_probes.py` and `phase_560_opencore_saas_readiness_engine.py`; update `phase_559_opencore_25_step_catalog.py`, `tasks.md`, `plan.md`, and `.mekong/company.json` so `audit_repository(".")` yields `PUBLIC_GITHUB_SAAS_READY` (100.0%).
4. **Next.js Dashboard Integration:** Wire `agentops-api.ts` (0 `:any`), `checkout/demo/page.tsx` (Dual-Rail + 3s Auto-Provisioning), `settings/page.tsx` (Manual License Input + MCU quota + 25-Step Readiness Matrix), and `revenue/page.tsx` (real gateway transactions).
5. **Quality Invariants:** Every created/modified Python module `<= 185 LOC`, zero `api.polar.sh` in `src/`, 39 CLI groups intact, `ruff` 0 errors, `pytest` 100% pass.

---

## 2. Disjoint File Ownership (Parallel Waves)

### Wave 1: Core Cryptographic Licensing & Verification
- `src/core/raas_license_verifier.py` (New, <= 185 LOC)
- `tests/test_raas_license_verifier.py` (New, <= 185 LOC)
- `src/lib/raas-gate.ts` (Upgrade, <= 185 LOC)

### Wave 2: Payment Rails, Gateway Endpoints & Polar Decommission
- `src/raas/checkout_router.py` (Rewrite to Dual-Rail + license endpoints, <= 185 LOC)
- `src/raas/revenue_router.py` (Clean Polar, 410 Gone webhook, <= 185 LOC)
- `src/api/billing_routes.py` (Refactor to Dual-Rail / local, <= 185 LOC)
- `src/services/polar_client.py` (Clean api.polar.sh URL, shim, <= 185 LOC)
- `src/raas/webhook_bridge.py` (Remove polar api url references, <= 185 LOC)
- `src/api/raas_billing_middleware.py`, `src/raas/marketplace_router.py`, `src/raas/marketplace_router_install.py` (Clean polar.sh string messages)

### Wave 3: 25-Step Readiness Probes & Blueprint Synchronization
- `src/core/opencore/monetization_gate_probes.py` (Add 11b & 11c behavioral probes, <= 185 LOC)
- `src/core/opencore/phase_560_opencore_saas_readiness_engine.py` (Sync with 11b/11c and blueprint, <= 185 LOC)
- `src/core/opencore/phase_559_opencore_25_step_catalog.py` (Update Step 20 description, <= 185 LOC)
- `plans/company-blueprint/tasks.md` (Check 11b & 11c)
- `plans/company-blueprint/plan.md` (Update verified statuses)
- `.mekong/company.json` (Update open_core verified & decommission polar)

### Wave 4: Next.js Dashboard UI & Real Wiring
- `apps/dashboard/lib/agentops-api.ts` (Remove `:any`, add dual-rail & license functions)
- `apps/dashboard/app/checkout/demo/page.tsx` (Dual-rail + 3s Auto-Provisioning)
- `apps/dashboard/app/dashboard/settings/page.tsx` (Manual License Input + Matrix)
- `apps/dashboard/app/dashboard/revenue/page.tsx` (Real Gateway transactions)

### Wave 5: Integration Tests & Quality Gates
- `tests/test_dual_rail_checkout.py` (New, verify endpoints, <= 185 LOC)
- Run `pytest`, `ruff check src/ tests/`, `wc -l`, and boundary checks.

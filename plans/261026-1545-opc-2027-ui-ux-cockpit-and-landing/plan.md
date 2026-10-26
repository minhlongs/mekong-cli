---
id: 261026-1545-opc-2027-ui-ux-cockpit-and-landing
title: "OPC 2027 UI/UX Architecture: Agentic Cockpit, Cryptographic Approval Card, Honest Usage Ledger & Dual-Rail RaaS"
status: in_progress
branch: feat/opc-2027-ui-ux-cockpit-and-landing
created: 2026-10-26
route: feature
mode: official
---

# Plan — OPC 2027 UI/UX Restructuring (`mekongmind.com` + `apps/dashboard` + `packages/raas-landing`)

## 1. Context & Objective

Restructure 100% of the UI/UX across both `mekong-cli` (`apps/dashboard`, `packages/raas-landing`) and `/Users/macbook/mekongmind/mvp` (`mekongmind.com`) according to the confirmed **OPC 2027 Agentic Cockpit & Cryptographic Glass** design paradigm:
- **Root-cause fix on `mekongmind.com` (`/Users/macbook/mekongmind/mvp`):** Resolve the Flash of Unstyled Content (FOUC) by creating `src/app/globals.css` with Tailwind directives and Obsidian/Emerald 2027 tokens, creating the root `src/app/layout.tsx`, removing decommissioned Polar SDK/checkout files, and replacing the Hero/Pricing/Templates UI with the OPC 2027 Sovereign Operating System + Dual-Rail RaaS (`VietQR` + `NOWPayments`).
- **OPC 2027 Cockpit in `apps/dashboard/` (`mekong-cli`):**
  - Build `/dashboard/opc` interactive 4-step Bento Cockpit:
    1. **Client Intake Card** (multi-currency `USD` / `VND` / `EUR`, IANA timezone, bilingual `EN`/`VI`, service selector).
    2. **Proposal & Rate Preview** (live calculation matching `src/opc/engine.py`).
    3. **Cryptographic Approval Gate** (live canonical `SHA-256 Action Digest` computed in browser, single-use approve/reject/revoke controls, payload tamper simulation toggle).
    4. **Honest Usage & Economics Ledger** (4 stages: `Estimated`, `Reserved`, `Actual`, `Unknown` — preserving `has_unknown_costs` without coercing to zero).
  - Build `/dashboard/packs` Business Packs Registry (`opc-pack/v1` manifest viewer, schema validator badge, capabilities & approval requirements).
  - Upgrade `DashboardShell.tsx` and `/dashboard/page.tsx` to OPC 2027 branding (`Mekong OPC 2027`, Obsidian/Emerald glass, navigation to `/dashboard/opc` and `/dashboard/packs`).
- **Sync `packages/raas-landing/`:** Eliminate legacy `OpenClaw` / `Polar.sh` / `$49-$499` drift and align with OPC 2027 + Dual-Rail RaaS (`VietQR` + `NOWPayments`) and canonical tiers (`$199 / $399 / $799 / $4,999`).

## 2. Disjoint Parallel Waves

| Wave | Scope / Owned Files | Deliverables |
|---|---|---|
| **Wave A (`mekongmind/mvp`)** | `/Users/macbook/mekongmind/mvp/**` | Add `src/app/globals.css` & root `src/app/layout.tsx`; remove Polar (`polar-config.ts`, `polar-checkout.ts`, `@polar-sh/sdk`); upgrade `hero-section.tsx`, `pricing-section.tsx`, `navbar.tsx`, `footer.tsx`, `checkout/page.tsx` to OPC 2027 & Dual-Rail RaaS; verify `npm run build`. |
| **Wave B (`apps/dashboard` OPC Cockpit)** | `apps/dashboard/app/dashboard/opc/page.tsx`, `apps/dashboard/app/dashboard/packs/page.tsx`, `apps/dashboard/components/DashboardShell.tsx`, `apps/dashboard/app/dashboard/page.tsx`, `apps/dashboard/app/layout.tsx` | Full 4-Step OPC Cockpit with live SHA-256 digest & tamper simulation, Honest Usage Ledger, Business Packs explorer, and updated navigation. |
| **Wave C (`packages/raas-landing` & UI Contract Tests)** | `packages/raas-landing/src/pages/en/index.astro`, `packages/raas-landing/src/pages/index.astro`, `tests/test_opc_2027_ui_contract.py` | Replace OpenClaw/Polar references with OPC 2027 + Dual-Rail RaaS; add pytest contract suite verifying UI alignment, zero Polar SDK/checkout references, and `mekong ui audit` pass. |

## 3. Acceptance Criteria

- [ ] **AC1:** `/Users/macbook/mekongmind/mvp` has `src/app/globals.css` and `src/app/layout.tsx` importing it, zero `@polar-sh/sdk` references, OPC 2027 Hero & Dual-Rail RaaS pricing (`$199 / $399 / $799 / $4,999`), and `npm run build` exits 0.
- [ ] **AC2:** `apps/dashboard` includes `/dashboard/opc` (4-step Intake -> Proposal -> SHA-256 Approval Gate -> Honest Usage Ledger) and `/dashboard/packs` (`opc-pack/v1` registry), and `npm run build` + `npm run typecheck` exit 0 with zero `:any` types.
- [ ] **AC3:** `packages/raas-landing` is aligned with OPC 2027 and Dual-Rail RaaS (`VietQR` + `NOWPayments`) with zero `Polar.sh` references.
- [ ] **AC4:** `tests/test_opc_2027_ui_contract.py` passes 100% (`<= 185 LOC`) alongside all existing Open-Core and OPC test suites.

---
title: "Deep Open-Core Spine, UI/UX Pro Max & SaaS Boundary Refactor (Waves 1–8)"
description: "Bilingual VN/EN implementation and verification plan for Waves 1–8 Open-Core + UI/UX Pro Max + SaaS <=175 LOC modularization and contract parity."
status: completed
priority: P1
effort: 10h
branch: main
tags: [opencore, saas, ui-ux-pro-max, refactor, wave6, wave7, wave8, loc-gate, bilingual]
created: 2026-10-17
---

# Implementation Plan: Deep Open-Core Spine, UI/UX Pro Max & SaaS Boundary Refactor (Waves 1–8)

**Date:** 2026-10-18 | **Contract Source:** `plans/reports/brainstorm-261017-deep-opencore-refactor.md` & `plans/reports/journal-261017-opencore-25-step-saas-bootstrap.md`  
**Selected Approach:** Waves 1–7 Completed + **Wave 8 Option D (All 3 Scopes Combined: 72 Files Strictly $\le 175\text{ LOC}$ across UI/UX Pro Max + Core 368–419 LOC + CLI 306–339 LOC)**

---

## 1. Objectives & Acceptance Gate (Mục tiêu & Cổng nghiệm thu)

1. **[EN] DRY Consolidation & Public Contract Parity / [VN] Hợp nhất DRY & Bảo toàn Hợp đồng Công khai:**
   - Centralize `OpenCoreSaasReadinessEngine.audit_blueprint(repo_root)` across CLI (`src/cli/commands/opencore_saas_restructuring_command.py`) and FastAPI (`src/api/opencore_status_routes.py`).
   - Preserve 100% of public Python/CLI/API contracts, JSON output keys, `MCUBilling` / `mcu_gate` HTTP 402 semantics, and `license_gate` / `auth_session` / `entitlement_enforcer` auth semantics.
2. **[EN] Wave 8 Option D Scope (72 Files Strictly $\le 175\text{ LOC}$) / [VN] Phạm vi Wave 8 Phương án D (72 File $\le 175\text{ LOC}$):**
   - **Scope A (24 UI/UX TS/TSX/CSS + Design Intelligence files $\le 175\text{ LOC}$):**
     - `src/components/settings/open-core-readiness-card.tsx` (154), `src/components/billing-pricing-modal.tsx` (131), `src/components/billing-quota-banner.tsx` (116), `src/components/billing/UsageDashboard.tsx` (94), `src/components/billing/PlanBadge.tsx` (80), `src/components/billing/QuotaExceededModal.tsx` (88), `src/components/billing/UpgradeToast.tsx` (68), `src/lib/quota-error-handler.ts` (117), `apps/dashboard/src/styles/tokens.css` (152), `apps/dashboard/src/pages/LoginPage.tsx` (94), `apps/dashboard/src/pages/RegisterPage.tsx` (110), `apps/dashboard/src/pages/BillingPage.tsx` (128), `apps/dashboard/src/pages/UsagePage.tsx` (129), `apps/dashboard/src/pages/ApiKeysPage.tsx` (127), `apps/dashboard/src/pages/MissionsPage.tsx` (92), plus all 9 `src/design_intelligence/*.py` modules (`approval_gate.py` 128, `auditor.py` 139, `benchmark_compare.py` 151, `builder.py` 153, `design_md.py` 141, `pipeline_orchestrator.py` 149, `redesign_planner.py` 145, `registry.py` 158, `study_pipeline.py` 165).
   - **Scope B (20 Python `src/core/*.py` files in the 368–419 LOC band $\le 175\text{ LOC}$):**
     - `health_reporter.py` (157), `sandbox_bridge.py` (152), `dag_scheduler.py` (159), `telemetry_collector.py` (151), `vector_memory_store.py` (167), `gateway_dashboard.py` (143), `api_adapter.py` (156), `ship_tech_masterplan_engine.py` (165), `webhook_events.py` (169), `self_improve.py` (161), `reflection.py` (153), `anomaly_detector.py` (150), `daily_briefing.py` (169), `packaging_bridge.py` (161), `plugin_marketplace.py` (169), `binh_phap_dispatcher.py` (169), `copywriting_engine.py` (165), `autonomous.py` (157), `raas_audit_logger.py` (171), `thue_engine.py` (168).
   - **Scope C (28 Python `src/cli/commands/*.py` files in the 306–339 LOC band $\le 175\text{ LOC}$):**
     - `watch_command.py` (167), `agy_command.py` (149), `chemical_command.py` (164), `legalaid_command.py` (159), `contract_command.py` (165), `arbitration_command.py` (169), `medtech_command.py` (165), `tender_command.py` (173), `hitech_command.py` (166), `cyber_command.py` (167), `maritime_passenger_mortgage_bunker_pilot_command.py` (167), `notary_command.py` (167), `lawyer_command.py` (171), `copywriting_command.py` (156), `price_command.py` (167), `veterinary_command.py` (169), `worktree_command.py` (170), `ip_command.py` (173), `support_command.py` (165), `procuracy_command.py` (172), `press_command.py` (166), `maritime_admiralty_ga_collision_command.py` (157), `esg_command.py` (166), `content_command.py` (160), `cto_command.py` (168), `maritime_sar_aton_spill_dredging_command.py` (170), `advertising_command.py` (173), `particle_init.py` (173).

---

## 2. Implementation & Finishing Verification Checklist (Danh sách công việc hoàn tất Waves 1–8)

- [x] **Task 1–7 (Waves 1–7):** Completed Open-Core spine DRY refactor and Waves 1–7 subsystem compactions ($\le 180\text{ LOC}$).
- [x] **Task 8 (Wave 8 Option D — 72 Files Strictly $\le 175\text{ LOC}$):**
  - Refactored all 24 UI/UX Pro Max & Design Intelligence files (`src/components`, `src/lib`, `apps/dashboard`, `src/design_intelligence`), all 20 Core 368–419 LOC files, and all 28 CLI 306–339 LOC files to strictly $\le 175\text{ LOC}$.
- [x] **Task 9 (Persistent Test Gate Coverage in `tests/test_idea_deep_opencore_brainstorm.py`):**
  - Added `"src/design_intelligence"`, `"src/components"`, `"src/lib"`, and `"apps/dashboard/src"` to the automated LOC test gate along with all 48 Wave 8 Python modules while keeping `tests/test_idea_deep_opencore_brainstorm.py` strictly $\le 165\text{ LOC}$.
- [x] **Task 10 (Verification & Journal Sync):**
  - Verified Open-Core, Blueprint, 25-Step, Core Boundary, and Wave 8 test suites + `ruff check` with 0 errors.

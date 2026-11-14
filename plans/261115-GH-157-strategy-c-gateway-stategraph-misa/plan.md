# Plan: GH-157 — Strategy C StateGraph, Profile 4 Router, Pilot A HTTP/Card & Legal Fourth-Door Closure

- **Issue:** `https://github.com/minhlongs/mekong-cli/issues/157`
- **Branch:** `feat/strategy-c-gateway-stategraph-misa`
- **Baseline `main` SHA:** `fcc565289be38596609a49e340a1752de054ba26`
- **Status:** `IN_PROGRESS`

## Phases & Disjoint File Ownership

| Phase | Mode | Owned Files | Dependencies |
| :--- | :---: | :--- | :--- |
| **Phase 1: Legal Fourth-Door Closure & VN SME Pricing Alignment** | Parallel Wave 1 (Worktree A) | `src/api/vn_pricing_routes.py`, `factory/contracts/pricing.json`, `src/raas/checkout_router.py`, `src/raas/nowpayments_router.py`, `src/raas/nowpayments_webhook_handler.py`, `src/opc/quota.py`, `tests/test_strategy_e_billing_reconcile.py`, `tests/test_strategy_c_legal_pricing.py` | None |
| **Phase 2: Strategy C Core Runtime (`src/opc/` <= 185 LOC)** | Parallel Wave 1 (Worktree B) | `src/opc/state_graph.py`, `src/opc/selective_router.py`, `src/opc/recipe_loader.py`, `src/opc/misa_export.py`, `src/opc/tenant_provisioner.py`, `src/opc/pilot_a.py`, `src/opc/bench_layers_vn.py`, `src/cli/commands/opc_command.py`, `src/cli/commands/opc_strategy_c_cmd.py`, `.goose/recipes/pilot-a-zalo-lead-to-quote.yaml`, `config/litellm_proxy.yaml`, `config/mcp_manifest_allowlist.json`, `tests/test_strategy_c_runtime.py` | None |
| **Phase 3: Dashboard OPC Bilingual VN-First Cockpit** | Parallel Wave 1 (Worktree C) | `apps/dashboard/lib/opc-cockpit-data.ts`, `apps/dashboard/app/dashboard/opc/page.tsx`, `apps/dashboard/app/dashboard/opc/components/client-intake-card.tsx`, `apps/dashboard/app/dashboard/opc/components/proposal-draft-preview.tsx`, `apps/dashboard/app/dashboard/opc/components/cryptographic-approval-card.tsx`, `apps/dashboard/app/dashboard/opc/components/honest-usage-ledger.tsx` | None |
| **Phase 4: FastAPI Pilot A HTTP Routes, Mobile Card & Gateway Wiring** | Wave 2 (Integration Worktree) | `src/api/pilot_a_routes.py`, `src/api/pilot_a_card_view.py`, `src/gateway.py`, `.github/workflows/gates.yml`, `tests/test_opc_platform_contract.py`, `tests/test_strategy_c_http_gateway.py` | Phases 1, 2, 3 |
| **Phase 5: Full Verification, Isolated Adversarial Review, PR & Merge** | Wave 3 (Orchestrator + Isolated Reviewer) | `plans/reports/code-review-gh-157.md` | Phase 4 |

## Acceptance Criteria (Done Means)
1. `/v1/opc/pilot-a/*` HTTP endpoints + `<15KB` Vietnamese mobile HTML card + Zalo/LarkSuite card payload + `HANDOFF_ZALO_OA_MANAGER` (`<0.85` confidence / math mismatch) + signed VietQR reconciliation + `DRAFT_PENDING_TVAN` MISA/Sapo export (`CSV`/`JSON`/`XML`).
2. 5-stage `StateGraph` (`RUNTIME_ENGINE=legacy|langgraph`) with SQLite WAL checkpointer, `SelectiveRouter` Profile 4 (`1500ms` failover + `source_span` + `UNKNOWN_COST_EVENT` + `config/litellm_proxy.yaml`), `.goose/recipes/pilot-a-zalo-lead-to-quote.yaml` + SHA-256 MCP allowlist, and `mekong opc provision-tenant` / `validate-recipe` (`189` registered CLI groups preserved).
3. `GET /v1/pricing/vn` has `0` references to `Polar.sh`; `VN_SME_WORKFLOW_TIERS` aligns to Section 10.3 (`790k/300`, `990k/500`, `1.99M/1000`, `4.9M/3500` + 6-month commitment pricing); `POST /webhooks/nowpayments` rejects `VN` jurisdiction orgs fail-closed.
4. `apps/dashboard/app/dashboard/opc` supports VN/EN (VN default), renders `source_span`, VietQR, and `DRAFT_PENDING_TVAN`, connects to `/v1/opc/pilot-a/*` with offline fallback, passes `npm run typecheck` and `npm run build` with `0` errors and `0` `:any` types, and keeps `tests/test_dashboard_opencore_sync.py` green.
5. `100%` of `src/opc/**/*.py` and OPC contract test files `<= 185 LOC` with `0` forbidden AST imports; `phase_559_opencore_25_step_catalog.py` and `.mekong/company.json` byte-unchanged; `ruff check` = `0` errors; `MEKONG-BENCH` 15/15 layers and all CI gates green; isolated `code-reviewer` clean; PR merged to `main` and issue `#157` labelled `shipped`.

# Implementation Plan — Strategy E Forensic Audit, Fail-Closed Pilot A, VN SME Tiers & MEKONG-BENCH 15 Layers

- **Issue:** `#153` (`https://github.com/minhlongs/mekong-cli/issues/153`)
- **Branch:** `feat/strategy-e-forensic-pilot-a-bench15`
- **Baseline HEAD SHA:** `30cf3895d6ee409b592f66627c9aaad1b2790cbf`
- **Status:** Completed (All 6 Deliverables Verified + Isolated Round-2 Code Review Approved)

## Phases & File Ownership

1. **Phase 1 — Read-Only Forensic Audit (`V-01..V-08` & `G0..G13`)** (`DONE`)
   - Outputs: `plans/reports/forensic-audit-baseline-v01-v08.json`, `plans/reports/forensic-audit-baseline-v01-v08.md`
2. **Phase 2 — Fail-Closed HMAC Approval (`src/opc/approval.py`, `src/opc/engine.py`)**
   - `PayloadBoundApprovalEngine` raises `ApprovalSecurityError` when `MEKONG_APPROVAL_SECRET` is unset or `< 16` chars outside `pytest`.
   - `OPCEngine` accepts optional `approval_secret: str | bytes | None = None`.
3. **Phase 3 — Production-Grade Stdlib `ZaloOAConnector` & Pilot A Hardening (`<= 185 LOC` per file)**
   - `src/opc/connectors/zalo_http.py` + `src/opc/connectors/zalo_oa.py` (re-export; internal `src/opc/` imports `zalo_http` to satisfy AST boundary)
   - `src/opc/privacy_guard.py` (Decree `13/2023/NĐ-CP` consent + `<72h` DSAR erasure + VN PII tokenization + `<0.85` confidence / math verifier `HALT_FOR_HUMAN` + `{tenant_id}.db` path-traversal guard)
   - `src/opc/accounting_draft.py` (Signed VietQR webhook reconciliation + `DRAFT_PENDING_TVAN` MISA/Sapo export)
   - `src/opc/pilot_a.py`, `src/opc/packs/*/pack.json`, `src/cli/commands/opc_command.py`, `src/core/cli_domain_handlers.py`
4. **Phase 4 — Parallel `VN_SME_WORKFLOW_TIERS` & Atomic SQLite WAL Workflow Quota**
   - `src/raas/checkout_router.py` (`VN_SME_WORKFLOW_TIERS`: `starter` 790k/300, `pilot_a` 990k/500, `growth` 1.99M/1,500, `agency` 4.9M/5,000; `vietqr`-only; `COMMERCIAL_TIERS` untouched)
   - `src/raas/revenue_router.py` (`vn_sme_workflow_tiers` on `GET /v1/pricing`)
   - `src/opc/quota.py` + `src/opc/usage.py` (`BEGIN IMMEDIATE` workflow quota reservation)
5. **Phase 5 — `MEKONG-BENCH v1.0` (15/15 Deterministic Layers)**
   - `src/opc/mekong_bench.py` + `src/opc/bench_layers_vn.py` (`15/15` layers, `pass_rate == 1.0`)
   - `tests/test_mekong_bench.py`, `tests/test_opc_production_callers.py`, `tests/test_strategy_e_pilot_a.py`
6. **Phase 6 — Verification, Isolated Code Review, PR & Issue Lifecycle**
   - Full CI G1 gate suites, `ruff check src/ tests/`, `scripts/generate-sbom.py`, `<= 185 LOC` guard, isolated `code-reviewer` subagent, PR linked to `#153`, cleanup.

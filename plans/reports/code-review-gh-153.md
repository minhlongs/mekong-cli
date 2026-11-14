# Adversarial Code Review (Round 2) — GH-153 (`feat/strategy-e-forensic-pilot-a-bench15`)

- **Repository / Worktree:** `/Users/macbook/mekong-cli-atoz-strategy-e`
- **Branch:** `feat/strategy-e-forensic-pilot-a-bench15` (Baseline `HEAD`: `30cf3895d6ee409b592f66627c9aaad1b2790cbf`)
- **Issue:** `#153` — Strategy E Forensic Audit (`V-01..V-08`), Fail-Closed Pilot A, VN SME Tiers & `MEKONG-BENCH` 15 Layers
- **Round-2 Verdict:** **APPROVED FOR PR / MERGE (`DONE`)** — All Round-1 findings (`C1`, `C2`, `H1..H6`, `M1..M4`) verified resolved by source inspection and adversarial runtime probes. `0` Critical, `0` High, `0` Medium, `3` Low (non-blocking) observations remain.

---

## Code Review Summary

### Scope
- **Files inspected:** 26 changed/new files (`16` modified tracked files: `+402 / -407`; `10` new untracked files; `4,711` total physical LOC across inspected targets) plus surrounding runtime callers (`src/opc/state.py`, `src/core/vietqr_engine.py`, `src/core/privacy_engine.py`, `src/core/cli_domain_handlers.py`).
- **Focus:** Independent Round-2 verification of all remediated defects, adversarial edge-case probing, SQLite FK/WAL concurrency invariants, Decree 13 PDPD erasure safety, VietQR single-order binding, `MEKONG-BENCH` 15-layer runtime oracle integrity, and repository hard invariants.
- **Runnable checks executed in Round 2:**
  - `python3 -m ruff check src/ tests/`: **All checks passed (`0` errors)**
  - G1 Open-Core, RaaS, OPC, Strategy E & Promise gate (`26` suites, `249` tests): **249 passed (`100%`)**
  - Vietnamese & credit regression suites (`tests/vn/` + `tests/core/test_service_credits.py`, `375` tests): **375 passed (`100%`)**
  - `python3 scripts/generate-sbom.py`: **CycloneDX `1.5`, `1,246` components**
  - `src/core/opencore/phase_559_opencore_25_step_catalog.py` & `.mekong/company.json`: **clean / byte-unchanged**

### Overall Assessment
All 12 blocking and medium defects identified in Round 1 (`C1`, `C2`, `H1..H6`, `M1..M4`) have been cleanly remediated without scope creep or invariant regressions. Every `src/opc/**/*.py` module (`18` files, max `183 LOC`) and every OPC contract test file (`8` files, max `179 LOC`) strictly satisfies the `<= 185 LOC` ceiling, enforced automatically in `tests/test_opc_platform_contract.py::test_file_loc_ceiling`. Adversarial runtime probes against SQL `LIKE` wildcards, FK constraints, cross-order `bank_tx_id` replays, short UTF-8 secrets, unauthenticated Zalo webhooks, `NaN`/`inf`/negative quote math, and subprocess CLI execution outside `pytest` all failed closed as designed.

---

### Round-1 Remediation Verification Matrix

| Round-1 ID | Original Defect | Round-2 Verification Evidence | Status |
| :--- | :--- | :--- | :---: |
| **C1** | DSAR `<72h` SQL `LIKE` wildcard wipe & FK orphan rows | `src/opc/privacy_guard.py:106-140` rejects `<3` char or non-alphanumeric `subject_id`, escapes `\`, `%`, `_` with `ESCAPE '\'`, enables `PRAGMA foreign_keys = ON`, deletes `opc_approvals` + `opc_actions` before `opc_runs`, and cleans `{stem}_vietqr.db`. Probed with `subject_id="sub_%_wild"`: innocent rows untouched, `PRAGMA foreign_key_check == []`. | **RESOLVED** |
| **C2** | VietQR cross-order single-payment replay & `bool`/type coercion | `src/opc/accounting_draft.py:48-106` rejects `bool`/`None`/non-int `amount_vnd`, enforces single-run word-boundary binding in `_memo_binds_exclusively_to_run`, and rejects duplicate `bank_tx_id` when stored `matched_order_id != expected_run_id`. Draft status strictly `DRAFT_PENDING_TVAN`. | **RESOLVED** |
| **H1** | Explicit short `secret_key` bypassed 16-byte minimum | `src/opc/approval.py:24-40` enforces `_MIN_SECRET_BYTES = 16` UTF-8 bytes on both explicit `secret_key` (`str`/`bytes`) and `MEKONG_APPROVAL_SECRET` (falling back only when env is empty *and* `PYTEST_CURRENT_TEST` is set). | **RESOLVED** |
| **H2** | Test files `> 185 LOC` & `zalo_oa.py` forbidden module name | `src/opc/connectors/zalo_oa.py` removed (`zalo_http.py` used everywhere); tests split into `test_strategy_e_pilot_a.py` (`173 LOC`), `test_strategy_e_billing_reconcile.py` (`142 LOC`), and `test_opc_production_callers.py` (`135 LOC`); all 8 OPC test files enforced `<= 185 LOC` in `test_opc_platform_contract.py:146-165`. | **RESOLVED** |
| **H3** | `NaN`/`inf` confidence & negative quantity/amount bypass | `src/opc/verifier.py:26-49` checks `math.isfinite(conf)` and `0.85 <= conf <= 1.0`, plus `is_finite()` and `>= 0` on `actual_total`, `tax_rate`, `qty`, and `rate`. | **RESOLVED** |
| **H4** | `WorkflowQuotaGuard` & `resolve_tenant_db_path` lacked live callers | `src/opc/pilot_a.py:111-114, 145-154` wires `resolve_tenant_db_path` in `PilotAWorkflow.__init__` and `self.usage.reserve_workflow_quota` (with `release_workflow_slot` rollback on draft/verifier failure) in `PilotAWorkflow.handle_webhook`, exposed via `mekong opc pilot-a --tenant-id --sme-tier`. | **RESOLVED** |
| **H5** | Live `ZaloOAConnector` optional MAC & non-dict/`bool` JSON crash | `src/opc/pilot_a.py:116, 129-131` defaults `require_webhook_mac=True` whenever `isinstance(zalo_connector, ZaloOAConnector)`; `src/opc/connectors/zalo_http.py:160-173` guards `isinstance(parsed, dict)`, `type(err_code) is not int`, and `isinstance(data_obj, dict)`. | **RESOLVED** |
| **H6** | `MEKONG-BENCH` L14 inline list-slicing tautology | `src/opc/verifier.py:52-66` implements `compact_conversation_preserving_moim`, exercised by `src/opc/bench_layers_vn.py:166-174` (`>=35%` token reduction, pinned `[MOIM]` at index `0`, turn-58 price change retained). | **RESOLVED** |
| **M1** | VN PII regex ordering, separators, 10-digit MST & 9-digit CMND | `src/opc/privacy_guard.py:20-26` orders `PII_BANK_ACC`, `PII_TAX_ID` (10-digit contextual + `-003`), and `PII_CCCD` (9-digit CMND / 12-digit CCCD) before separator-tolerant `PII_PHONE`. | **RESOLVED** |
| **M2** | `has_active_consent` truncated at `limit=20` across purposes | `src/opc/privacy_guard.py:91-97` queries `consent_log` filtered directly by `WHERE subject_id = ? AND purpose = ? ORDER BY recorded_at DESC LIMIT 1`. | **RESOLVED** |
| **M3** | `/v1/checkout/status` hardcoded `PREMIUM` for VN SME tiers | `src/raas/checkout_router.py:108-120, 227-242` maps paid VND amounts via `_VND_TO_SME_TIER` (`starter`/`pilot_a`/`growth`/`agency` + `workflow_quota`) and `_VND_TO_COMMERCIAL_TIER`. | **RESOLVED** |
| **M4** | CLI `proposal` & `decide` lacked `ApprovalSecurityError` handler | `src/cli/commands/opc_command.py:111-115, 176-180` catches `ApprovalSecurityError` cleanly and exits with code `1` without traceback (verified via subprocess outside `pytest`). | **RESOLVED** |

---

### Critical Issues
None (`0`).

### High Priority
None (`0`).

### Medium Priority
None (`0`).

### Low Priority (Non-Blocking Follow-Ups)

#### L1. `dsar_requests` SQLite Status Row Remains `NO_RECORDS_FOUND` When Erasure Occurs Only in `opc_db_path`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/privacy_guard.py:135-138`
- **Detail:** When `enforce_consent=False` (so `consent_log` in `privacy.db` has 0 rows for `subject_id`, while `opc_runs` in `opc_state.db` has matching rows), `erase_subject_under_72h` updates `dsar["status"] = "COMPLETED"` in the returned dict, whereas the `dsar_requests` row persisted inside `PrivacyEngine.handle_dsar_request` stays `"NO_RECORDS_FOUND"`. Under `enforce_consent=True`, `consent_log` rows exist so both return dict and DB row record `"COMPLETED"`.
- **Optional Polish:** Execute `UPDATE dsar_requests SET status = 'COMPLETED' WHERE request_id = ?` on `self.engine.db_path` when `opc_erased > 0`.

#### L2. Minor Type/Memo Tightening Opportunities in `reconcile_signed_vietqr_webhook`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/accounting_draft.py:58, 84-89`
- **Detail:** (1) `isinstance(raw_amt, float)` is not rejected prior to `int(raw_amt)` (so a JSON float like `1000000.9` in an HMAC-signed payload truncates to `1000000`); (2) `_memo_binds_exclusively_to_run` permits an empty `memo` when the HMAC-signed body explicitly supplies `"matched_order_id": expected_run_id` and no conflicting `run_*` token appears in `memo`. Neither is exploitable because `verify_webhook_signature` authenticates the raw payload first.

#### L3. Pre-Existing Advisory Scanners in `gates.yml` (`G2 Security`)
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/.github/workflows/gates.yml:145-160`
- **Detail:** Accurately documented in `plans/reports/forensic-audit-baseline-v01-v08.md` (`V-08`), `bandit --exit-zero`, `semgrep` (`continue-on-error: true`), and `trivy` (`exit-code: 0`) remain advisory from baseline.

---

### Behavioral & Hard Invariant Checklist

- [x] **Concurrency:** Verified SQLite WAL `BEGIN IMMEDIATE` in `WorkflowQuotaGuard` (`src/opc/quota.py:85`) and `UsageLedger.reserve_budget` (`src/opc/usage.py:81`), plus atomic `StateStore.consume_approval_atomic` (`src/opc/state.py:121`).
- [x] **Error boundaries:** All external HTTP/JSON/SQLite/CLI boundaries fail closed with typed domain exceptions and clean CLI exit codes (`1`).
- [x] **API contracts:** `verify_confidence_and_math` halts on `NaN`/`inf`/out-of-range confidence and negative amounts; `ZaloOAConnector` rejects non-dict JSON and `bool` error codes; `/v1/checkout/status` resolves SME tiers and `workflow_quota`.
- [x] **Backwards compatibility:** `COMMERCIAL_TIERS` (`basic`, `premium`, `enterprise`, `master`) and `POST /webhook/polar` (`HTTP 410 Gone`) remain 100% intact (`test_dual_rail_checkout.py` 12/12 passed).
- [x] **Input validation:** `QuarantineFloor` (NFD->NFC + zero-width strip), `_TENANT_SLUG_RE` path-traversal guard, and SQL `LIKE ... ESCAPE '\'` DSAR sanitization verified.
- [x] **Auth/authz paths:** Mandatory HMAC-SHA256 `>= 16` UTF-8 bytes outside `pytest`; mandatory Zalo webhook MAC on live `ZaloOAConnector`; HMAC-SHA256 bank webhook verification before reconciliation.
- [x] **Data leaks & PDPD:** Consent lookup free of `limit=20` truncation; DSAR `<72h` erasure preserves `PRAGMA foreign_key_check == []`; VN PII redaction covers email, bank account, 10/13-digit MST, 9/12-digit CMND/CCCD, and separator-formatted phones.
- [x] **`phase_559_opencore_25_step_catalog.py` & `.mekong/company.json`:** Byte-for-byte unchanged (`git status` clean).
- [x] **`<= 185 LOC` ceiling:** `18 / 18` `src/opc/**/*.py` files pass (max `183 LOC`) and `8 / 8` OPC test files pass (max `179 LOC`).
- [x] **AST boundary (`src/opc/**/*.py`):** `0` forbidden country-pack imports or module names (`zalo_oa.py` removed).
- [x] **Zero secrets / `.env` / `.claude/` leaks:** Verified (`test_opencore_git_boundary_guard.py` 8/8 passed).

---

### Plan Task Status (`plans/261114-GH-153-strategy-e-forensic-pilot-a-bench15/plan.md`)

| Phase | Deliverable | Round-2 Status |
| :--- | :--- | :--- |
| **Phase 1** | Read-Only Forensic Audit (`V-01..V-08` & `G0..G13`) | **COMPLETE** |
| **Phase 2** | Fail-Closed HMAC Approval (`approval.py`, `engine.py`, `opc_command.py`) | **COMPLETE** |
| **Phase 3** | `ZaloOAConnector`, `PilotPrivacyGuard`, `verifier.py`, `accounting_draft.py`, `PilotAWorkflow` | **COMPLETE** |
| **Phase 4** | Parallel `VN_SME_WORKFLOW_TIERS` & Atomic `WorkflowQuotaGuard` Live Wiring | **COMPLETE** |
| **Phase 5** | `MEKONG-BENCH v1.0` (15/15 Deterministic Runtime Layers) & `<= 185 LOC` Suites | **COMPLETE** |
| **Phase 6** | Verification, Isolated Round-2 Code Review, PR & Issue `#153` Lifecycle | **READY FOR COMMIT & PR** |

### Metrics
- **Linting Issues (`ruff check src/ tests/`):** `0`
- **Gate & VN Regression Tests Executed:** `624 / 624 passed` (`249` G1 gate + `375` VN/credits, `100%`)
- **`src/opc/**/*.py` LOC Ceiling (`<= 185`):** `18 / 18 passed` (max `183 LOC`)
- **OPC Contract Test Files LOC Ceiling (`<= 185`):** `8 / 8 passed` (max `179 LOC`)

### Unresolved Questions
None blocking merge.

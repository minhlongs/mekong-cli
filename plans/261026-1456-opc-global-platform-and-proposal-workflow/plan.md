---
id: 261026-1456-opc-global-platform-and-proposal-workflow
title: "One-Person Company (OPC) Global Platform Architecture & Client Proposal Workflow"
status: completed
branch: feat/opc-global-platform-and-proposal-workflow
created: 2026-10-26
route: feature
mode: official
---

# Plan — One-Person Company (OPC) Global Platform Architecture & Client Proposal Workflow

## 1. Context & Objective

Transform `mekong-cli` into a neutral, production-grade community platform for One-Person Companies (OPC) across the globe, with the first target profile: **technical consultants, freelancers, and solo technical agencies**.

The core must be neutral (no hardcoded C-Suite titles `cto`/`cmo`/`coo`), business flows are modularized into declarative **Business Packs** & **Country Packs** (`opc-pack/v1`), external actions are guarded with **Payload-Bound Approvals** (SHA-256 action digest), and economics are truthful (`estimated`, `reserved`, `actual`, `unknown`).

The first business flow must be 100% executable offline without network or API keys:
`Client Request (Intake) → Business Profile & Proposal Draft → Human Approval (Payload Bound) → Follow-up Draft`.

## 2. Invariants & Guardrails

1. **Byte-for-byte OpenCore Catalog Invariant:** Never modify `src/core/opencore/phase_559_opencore_25_step_catalog.py` (enforced by `tests/test_durian_grab_honest_diagnosis.py`).
2. **LOC Limits:** All new modules in `src/opc/` and test suites must strictly adhere to `<= 185 LOC`.
3. **Zero `:any` in TypeScript & Complete Typing in Python:** Full type hints on all newly added APIs.
4. **No Code Execution on Manifest Load:** Pack manifests (`pack.json`) must be parsed as declarative data without executing python code.
5. **Backwards Compatibility:** All 39 CLI command groups in `src/cli/app_setup.py` and RaaS Dual-Rail routes in `src/raas/` must remain 100% operational.

## 3. Scope & Disjoint Parallel Implementation Waves

| Wave | Module / Paths | Deliverables |
|---|---|---|
| **Wave 1 (OPC Domain Core & Manifest Engine)** | `src/opc/models.py`, `src/opc/manifest.py`, `src/opc/approval.py` | Typed dataclasses (`PackManifest`, `BusinessProfile`, `ProposalInput`, `ActionPayload`, `ApprovalToken`), `ManifestValidator` (`opc-pack/v1`), and `PayloadBoundApprovalEngine` (SHA-256 action digest, single-use, expiration, revocation). |
| **Wave 2 (State Store & Usage Economics)** | `src/opc/state.py`, `src/opc/usage.py` | SQLite WAL state store (`opc_runs`, `opc_approvals`, `opc_actions`), idempotency keys, and 4-tier usage ledger (`estimated`, `reserved`, `actual`, `unknown`). |
| **Wave 3 (Business Pack & Offline Connectors)** | `src/opc/connectors/base.py`, `src/opc/connectors/mock.py`, `src/opc/packs/client-proposal-followup/` | Pack manifest `pack.json`, Jinja2/string templates for proposal & follow-up draft, sample fixtures, and `MockConnector` for 100% deterministic offline runs. |
| **Wave 4 (Engine Orchestration & CLI Wiring)** | `src/opc/engine.py`, `src/cli/commands/opc_command.py`, `src/cli/app_setup.py`, `src/core/runtime_adapter.py` | `OPCEngine` executing the complete intake→quote→approval→followup flow, `mekong opc` command group (`packs validate`, `run`, `approve`, `status`), support for `--pack` on `mekong run`, and neutralizing C-Suite bindings in `runtime_adapter.py`. |
| **Wave 5 (Acceptance Test Suite A–O & Wheel Clean Build)** | `tests/test_opc_platform_contract.py`, `tests/test_opc_approval_security.py` | Automated test suite verifying all 15 acceptance criteria (A through O), wheel build verification (`poetry build` into a clean virtual environment), and zero regressions across existing test suites. |

## 4. Acceptance Criteria (A–O)

- [x] **A:** `mekong --help` and existing 39 groups still function.
- [x] **B:** Core runtime runs independently of fixed C-Suite titles.
- [x] **C:** Fixture pack outside kernel is discovered and executed.
- [x] **D:** Malformed manifest, incompatible runtime, and un-declared capabilities fail validation.
- [x] **E:** Full OPC flow executes end-to-end offline from clean artifact.
- [x] **F:** Altering action payload (recipient, amount, text, connector) invalidates approval digest.
- [x] **G:** Denial prevents external connector dispatch.
- [x] **H:** Repeated runs with same action ID / idempotency key do not duplicate side-effects.
- [x] **I:** Uncertain action status is flagged for reconciliation.
- [x] **J:** Unknown usage stays unknown, not zero; duplicate events are not double-counted.
- [x] **K:** Currency (USD, VND, EUR), IANA timezones, and bilingual support (EN/VN) verified.
- [x] **L:** Legacy RaaS checkout and token verifier contracts pass 100%.
- [x] **M:** CLI help output matches documentation.
- [x] **N:** Zero secrets in code, fixtures, or logs.
- [x] **O:** Working diff strictly scoped to OPC platform additions.

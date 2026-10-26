---
id: 261026-1930-opc-core-runtime-unification
title: "OPC Core Runtime Unification (2-Goal Lifecycle, Atomic SQLite Approval, Budget Reservation, PackRegistry & Country Pack AST Boundary)"
status: completed
branch: feat/opc-core-runtime-unification
issue: 113
created: 2026-10-26
route: feature
mode: official
---

# Plan — OPC Core Runtime Unification & Verifiable Proposal Workflow

## 1. Context & Objective

Unify `src/opc/` into the canonical `MekongCoreRuntimeImpl` (`src/core/runtime_adapter.py`), `CapabilityBus` (`src/core/capability.py`), and `Governance` (`src/core/governance.py`) via a 2-Goal lifecycle (`Goal 1: intake_to_draft`, `Goal 2: decision_to_followup`), eliminating the parallel-island execution bypass in `src/commands/run.py`, enforcing atomic SQLite approval token consumption against multi-worker races, pre-dispatch budget reservation (`RESERVED`), `PackRegistry` duplicate/entrypoint validation, Country Pack (`vn-sme-ops`) AST boundary isolation, and clean wheel packaging.

## 2. Invariants & Guardrails

1. **Byte-for-byte OpenCore Catalog Invariant:** Never modify `src/core/opencore/phase_559_opencore_25_step_catalog.py`.
2. **LOC Ceiling:** Every file in `src/opc/`, `src/core/opencore/`, and OPC test files must remain strictly `<= 185 LOC`.
3. **Complete Typing:** Full type annotations across all touched Python modules; zero `:any`.
4. **No Code Execution on Manifest Load:** Pack manifests (`pack.json`) are parsed purely as JSON data.
5. **Backwards Compatibility:** All 39+ CLI command groups in `src/cli/app_setup.py` and RaaS Dual-Rail routes in `src/raas/` remain 100% operational.

## 3. Disjoint Implementation Waves (Parallel-Safe File Ownership)

| Wave | Owner / Scope | Files Modified / Created | Deliverables |
|---|---|---|---|
| **Wave 1: Manifest Registry & Country Pack** | Pack Contract | `src/opc/manifest.py`, `src/opc/packs/vn-sme-ops/pack.json` | Add `ENTRYPOINT_RE` (`module:attr`) check, `PackRegistry` with duplicate `pack_id` rejection, and `vn-sme-ops` Country Pack manifest with legal reference metadata (`jurisdiction: "VN"`). |
| **Wave 2: Atomic SQLite State & Budget Reservation** | Persistence & Economics | `src/opc/state.py`, `src/opc/usage.py`, `src/opc/approval.py` | Add `consume_approval_atomic()` (`UPDATE ... WHERE consumed=0 AND revoked=0 AND expires_at >= ?`), `store_action_payload` / `get_action_payload` for 2-Goal resumption, and `reserve_budget()` with `BEGIN IMMEDIATE` transaction guard. |
| **Wave 3: 2-Goal Core Runtime Integration & CLI** | Runtime & CLI | `src/opc/engine.py`, `src/cli/commands/opc_command.py`, `src/commands/run.py` | Wire `OPCEngine.run_via_core_runtime()` through `MekongCoreRuntimeImpl` + `CapabilityBus` + `Governance`; enforce `manifest.capabilities` & `manifest.connectors` allowlists; generate decision-specific `followup_draft` (`approve`, `reject`, `revise`); add `mekong opc decide` and `mekong opc status`; wire `mekong run --pack <pack_id>` through `_build_runtime()`. |
| **Wave 4: Packaging, Docs & Acceptance Suite A–O** | Quality & Packaging | `pyproject.toml`, `README.md`, `README.vi.md`, `docs/architecture.md`, `tests/test_opc_platform_contract.py`, `tests/test_opc_approval_security.py` | Include `src/opc/packs/**/*` in wheel build; document `mekong opc {validate-pack, proposal, decide, status}`; add AST Country Pack isolation test, 2-worker atomic approval concurrency test, budget reservation test, and clean wheel verification. |

## 4. Acceptance Criteria (A–O)

- [ ] **A:** `mekong --help` and all >= 39 CLI groups function without regression.
- [ ] **B:** Core runtime (`runtime_adapter.py`, `capability.py`, `governance.py`) and `src/opc/` have zero AST imports of `zalo_engine`, `thue_dnvn`, `ke_toan`, or `tt78`.
- [ ] **C:** External fixture pack outside kernel is discovered via `PackRegistry` and executed through `MekongCoreRuntimeImpl`.
- [ ] **D:** Malformed manifest, duplicate `pack_id`, invalid entrypoint format, incompatible runtime, and undeclared capabilities/connectors fail validation.
- [ ] **E:** Full 2-Goal OPC flow (`proposal` -> `status` -> `decide`) executes end-to-end offline from a clean wheel installed in an isolated `venv` outside the repo directory.
- [ ] **F:** Mutating any `ActionPayload` field (recipient, budget_amount, content, attachments, connector) invalidates the SHA-256 approval digest.
- [ ] **G:** Rejection (`reject`), revision (`revise`), expiration, or revocation blocks external connector dispatch while producing appropriate follow-up drafts.
- [ ] **H:** Concurrent 2-worker consumption of the same `ApprovalToken` allows exactly 1 worker to succeed (`rowcount == 1`) and blocks the second; duplicate `idempotency_key` deduplicates side-effects.
- [ ] **I:** Uncertain connector outcome marks action and run as `reconciliation_required` without automatic retry.
- [ ] **J:** `UsageLedger` enforces pre-dispatch `reserve_budget()`, preserves `UNKNOWN` costs (`has_unknown_costs=True`) without coercing to zero, and deduplicates repeated `event_id`s.
- [ ] **K:** Multi-currency (`USD`, `VND`, `EUR`), IANA timezones, and bilingual (`en`, `vi`) templates/outputs verified.
- [ ] **L:** Legacy 25-Step Open-Core, RaaS Dual-Rail checkout, and HMAC license verifier suites pass 100%.
- [ ] **M:** README and architecture docs match installed CLI `--help` output.
- [ ] **N:** Zero secrets in code, fixtures, logs, or reports.
- [ ] **O:** All `src/opc/*.py` and OPC test files strictly `<= 185 LOC`.

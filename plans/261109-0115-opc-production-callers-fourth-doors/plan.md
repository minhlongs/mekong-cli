---
title: "OPC Production Callers & Fourth-Door Closure"
status: completed
created: 2026-11-09
issue: 142
---

# OPC Production Callers & Fourth-Door Closure

- **Project:** minhlongs/mekong-cli
- **Branch:** `feat/opc-production-callers-and-fourth-doors`
- **Base:** `06d4e09eaa`
- **Issue:** #142
- **Route:** feature — close fourth-door bypasses and wire all production callers for OPC Quarantine, HMAC Approval, Pilot A, and MEKONG-BENCH
- **Ship mode:** official/stable (`--ship`)

## Objective

Close the four remaining production-caller and fourth-door security gaps across
`src/opc/engine.py`, `src/core/promise/service.py`, `src/cli/commands/opc_command.py`,
and `src/core/cli_domain_handlers.py`, while keeping all `src/opc/` and
`src/core/opencore/` modules strictly `<= 185 LOC` and preserving the 189
registered CLI groups invariant.

| # | Surface | Verified gap at `06d4e09eaa` | Closure |
| - | ------- | ---------------------------- | ------- |
| D1 | `OPCEngine.generate_draft` (`src/opc/engine.py`) | Direct callers (including `mekong opc proposal`) bypass `QuarantineFloor` | `OPCEngine.generate_draft` enforces `QuarantineFloor.guard_proposal_input` + `enforce_before_tool` before drafting or saving state |
| D2 | `PromiseService._require_approval` & `decide_approval` (`src/core/promise/service.py`) | `_require_approval` only checks bare `action_digest` and `consume_approval_atomic` without HMAC verification; `decide_approval` resumes without verifying/consuming the token | Verify `ApprovalToken` HMAC-SHA256 via `self.approvals.verify_and_consume(token, payload, now=now_ts)` and consume atomically in both paths |
| D3 | `mekong opc` CLI (`src/cli/commands/opc_command.py`) | No CLI subcommands for `pilot-a`, `quarantine`, `bench`; `decide` hardcodes `client-proposal-followup` and drops `draft_data`/`action_payload_data` | Add `pilot-a`, `quarantine`, and `bench` subcommands; resolve pack by `run_data["pack_id"]`; register `ZaloSandboxConnector`; preserve draft/action payload on status updates |
| D4 | `_handle_opc` (`src/core/cli_domain_handlers.py`) & `dna/core-dna.json` | `_handle_opc` only lists packs; `core-dna-gate` requires manifest update when `src/cli/` changes | Support `list_packs`, `quarantine`, `pilot_a`, and `bench` actions in `_handle_opc`; record review entry in `dna/core-dna.json` |

## Phases

1. `phase-01-opc-engine-and-promise-doors.md` — Enforce `QuarantineFloor` in `OPCEngine.generate_draft` and HMAC-SHA256 verification in `PromiseService._require_approval` & `decide_approval` (D1, D2)
2. `phase-02-cli-and-domain-handlers.md` — Wire `pilot-a`, `quarantine`, and `bench` into `mekong opc` CLI and `_handle_opc`, fix `decide_proposal` pack resolution & state preservation, and update `dna/core-dna.json` (D3, D4)

## Dependencies

Phase 01 and Phase 02 touch disjoint production files (`src/opc/engine.py` + `src/core/promise/service.py` vs. `src/cli/commands/opc_command.py` + `src/core/cli_domain_handlers.py` + `dna/core-dna.json`). Phase 02 CLI tests exercise Phase 01's `OPCEngine.generate_draft` quarantine enforcement.

## Acceptance Criteria

- [x] `OPCEngine.generate_draft` enforces `QuarantineFloor` on `ProposalInput` before drafting or persisting state into SQLite, keeping `src/opc/engine.py <= 185 LOC`.
- [x] `PromiseService._require_approval` and `decide_approval` verify `ApprovalToken` HMAC-SHA256 via `PayloadBoundApprovalEngine.verify_and_consume` and consume the token atomically, rejecting forged or SQLite-tampered tokens with `APPROVAL_SECURITY_VIOLATION` (`HTTP 409`) while preserving `APPROVAL_PAYLOAD_MISMATCH` and `APPROVAL_REPLAY_OR_EXPIRED`.
- [x] `mekong opc` CLI exposes `pilot-a`, `quarantine`, and `bench` subcommands; `decide` resolves the run's actual pack manifest (`client-proposal-followup` or `vn-sme-ops`), registers `ZaloSandboxConnector`, and preserves `draft_data`/`action_payload_data` in SQLite; `proposal` catches `QuarantineViolationError` cleanly.
- [x] `_handle_opc` in `src/core/cli_domain_handlers.py` dispatches `list_packs` (default), `quarantine`, `pilot_a`, and `bench` actions.
- [x] `dna/core-dna.json` is updated for `core-dna-gate`; all files in `src/opc/` and `src/core/opencore/` stay `<= 185 LOC`; `len(build_app().registered_groups) == 189`; `ruff check` and test suites pass.

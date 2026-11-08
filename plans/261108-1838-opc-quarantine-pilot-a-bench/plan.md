---
title: "OPC Quarantine Floor, HMAC Approval Binding, Pilot A Slice & MEKONG-BENCH"
status: completed
created: 2026-11-08
issue: 140
---

# OPC Quarantine Floor, HMAC Approval Binding, Pilot A Slice & MEKONG-BENCH

- **Project:** minhlongs/mekong-cli
- **Branch:** `feat/opc-quarantine-pilot-a-and-bench`
- **Base:** `3256268662`
- **Route:** feature — four engineering items left from the strategic-research advice
- **Ship mode:** official/stable

## Objective

Close the four remaining engineering items from the Mekong CLI Strategic Research
advice, keeping the whole change inside `src/opc/` so `src/core/` provider
neutrality, the CLI command surface (189 groups), the OpenCore LOC ceilings and
the byte-for-byte catalog invariant are all untouched.

| # | Item | Verified state at base | Closure |
| - | ---- | ---------------------- | ------- |
| H1 | Approval tokens are payload-bound by a bare SHA-256 digest, so a token rewritten in memory or in SQLite (same digest) is accepted | `src/opc/approval.py` verifies only digest/lifecycle; `src/opc/packs/vn-sme-ops/pack.json` points at the non-existent entrypoint `src.opc.packs.vn:VnSmePack` and declares a TT78/NĐ123 published-invoice workflow | HMAC-SHA256 signature over the full token identity; valid manifest and non-claiming legal references for every pack |
| H2 | Nothing stands between untrusted customer text and the tool bus | No `questions`, no quarantine surface anywhere under `src/opc/` | `src/opc/quarantine.py` tags untrusted text and blocks injection / tool-hijack attempts before any tool runs |
| H3 | No end-to-end slice proves the Zalo OA offer path is safe | `src/opc/engine.py` already prices deterministically with `Decimal` and dispatches through an approval gate; there is no Zalo entry, no VietQR, no 48-hour window check | `src/opc/pilot_a.py` wires message → window → quarantine → price → VietQR → approval card → dispatch |
| H4 | No deterministic oracle suite exists for the autonomy runtime | No `src/opc/mekong_bench.py` | Five layers with oracles and a rendered PASS/FAIL table |

## Phases

1. `phase-01-hmac-and-pack-hygiene.md` — HMAC approval binding and pack manifest hygiene (H1)
2. `phase-02-quarantine-floor.md` — untrusted-input quarantine and injection blocking (H2)
3. `phase-03-pilot-a-slice.md` — Zalo OA → quote → VietQR → approval card slice (H3)
4. `phase-04-mekong-bench.md` — five-layer deterministic benchmark (H4)

## Dependencies

H1 → H3 and H1 → H4 (both use `PayloadBoundApprovalEngine`).
H2 → H3 (Pilot A routes every message through the quarantine floor).
H4 is the last phase: it exercises the finished surface.

Phases 01 and 02 touch disjoint files and may be implemented together, then
reviewed as one change.

## Acceptance Criteria

- [x] Tampering with any `ApprovalToken` field, or with the bound `ActionPayload`, raises `ApprovalSecurityError`; the signature is an HMAC-SHA256 over the token identity, not a bare digest comparison.
- [x] `load_pack_manifest` succeeds for every pack under `src/opc/packs/`, and no pack declares a published TT78/NĐ123 invoice workflow.
- [x] 50/50 Vietnamese and English prompt-injection samples produce zero tool calls and are reported as blocked; legitimate quote requests pass untouched.
- [x] `mekong_pilot_a` runs message → 48h-window check → quarantine → deterministic `Decimal` quote → VietQR EMVCo payload → HMAC approval card → approved dispatch, and refuses a quarantined message, an expired/revoked token, a tampered payload, and a replayed idempotency key.
- [x] `tests/test_mekong_bench.py` renders a PASS/FAIL table with all five layers passing.
- [x] VAT/price arithmetic, Decimal rounding, EMVCo payload shape and the existing approval test expectations are unchanged (existing tests still pass).
- [x] `test_core_boundary`, `test_raas_license_verifier`, `test_durian_grab_honest_diagnosis`, `test_github_content_25_step_sync` pass; `ruff check src/ tests/` clean; `build_app().registered_groups` is still 189.
- [x] No file under `src/core/opencore/` or `src/core/raas_license_verifier.py` exceeds 185 LOC; `src/core/opencore/phase_559_opencore_25_step_catalog.py` and `.mekong/company.json` are byte-identical to base.

## Non-goals

- No LangGraph, LiteLLM Proxy, or Inngest integration.
- No new or removed CLI command group (the 189-group surface is frozen).
- No real Zalo network call, no paid API, no outbound message to a real customer.
- No change to pricing values, VAT computation, VAS journal logic, or EMVCo structure.
- No contact with `src/core/opencore/phase_559_opencore_25_step_catalog.py` or `.mekong/company.json`.

## Constraints

- OpenCore modules under `src/core/opencore/` and `src/core/raas_license_verifier.py` stay `<= 185 LOC`.
- `src/core/` stays provider-neutral per `tests/test_core_boundary.py` — no vendor SDK imports.
- The whole change lives under `src/opc/` and `tests/`; `src/cli/` and `src/commands/` are untouched, so `core-dna-gate` needs no manifest change.
- All tests run deterministically against tmp SQLite via each engine's `db_path` argument; no network.
- The existing approval-severity tests (`tests/test_opc_approval_security.py`) keep passing without modification to their intent.

## Rollback

Revert the single PR. The change adds modules and one HMAC field plus a manifest
correction; a revert restores base behaviour with no data cleanup.

---
title: "VN Legal Compliance Closure — Rail Gate, Draft-Invoice Truthfulness, Consent Log & Erasure"
status: completed
created: 2026-11-08
---

# VN Legal Compliance Closure

- **Project:** minhlongs/mekong-cli
- **Branch:** `fix/vn-legal-compliance-rail-and-draft-invoice`
- **Base:** `e2797d447`
- **Route:** bugfix — three live legal violations, each already half-built
- **Ship mode:** official/stable

## Objective

Close three Vietnamese legal-compliance violations live at HEAD `e2797d447`. None
needs a new subsystem: scout showed two of the three are already half-implemented,
and the defect sits in the unfinished half.

| # | Violation | Verified state at HEAD | Closure |
| - | --------- | ----------------------- | ------- |
| L1 | A Vietnamese legal-entity tenant can select the USDT (`nowpayments`) rail | `src/raas/checkout_router.py:89` branches on the request's rail with no jurisdiction check | Fail-closed org rail gate |
| L2 | Three engines self-certify e-invoice compliance with no licensed TVAN integration anywhere. `ke_toan_engine.create_invoice()` self-issues numbers and `invoice_tt78_structure` returns **PASS** citing NĐ 123/2020 and TT 78/2021; `ecommerce_engine.py:467` stamps `invoice_schema: "Thông tư 78/2021 & Nghị định 123/2020"` into the returned payload; `taxadmin_engine.py:400` **fabricates a Tax Authority code** (`CQT-{date}-{uuid4}`) and writes `issue_status: "ISSUED"` — a real `Mã của cơ quan thuế` can only be granted by the General Department of Taxation through a licensed TVAN, so this one is the most severe | Math and persistence are correct in all three; the compliance claims are false | Draft-only artifacts, no self-minted authority code, no statutory citation |
| L3 | DSAR requests are recorded but never honoured — `handle_dsar_request` inserts a `PROCESSING` row and deletes nothing; no consent table exists | `src/core/privacy_engine.py:139-210`, `:559-613` | Consent log + real erasure across live stores |

## Phases

1. `phase-01-rail-gate.md` — fail-closed rail policy for Vietnamese orgs (L1)
2. `phase-02-draft-invoice-honesty.md` — remove the false compliance claim (L2)
3. `phase-03-consent-and-erasure.md` — consent log and real subject erasure (L3)

## Dependencies

Phases are independent and touch disjoint files. They may be implemented in order
in one branch; L1 and L3 both touch test files, so they are sequenced rather than
run in parallel.

## Acceptance Criteria

- [x] A VN-jurisdiction checkout requesting `nowpayments` is rejected with a named error and a non-2xx status, proven by test.
- [x] An unresolved/unknown jurisdiction is denied the crypto rail (fail-closed), proven by test.
- [x] `/v1/pricing` and the Polar 410 payload advertise only the rails the caller's jurisdiction may settle on, failing closed to `vietqr` for an unattributable caller (revised from "unchanged" during the adversarial review — see the report).
- [x] No code path or test asserts that a locally produced invoice is a legally issued e-invoice; every artifact carries a draft disclaimer naming the TVAN requirement.
- [x] `invoice_tt78_structure` reports structure completeness only, with no statutory citation in its pass message.
- [x] VAT amounts, Decimal rounding, VAS journal balance, and XML shape are unchanged (existing tests still pass).
- [x] Recording and withdrawing consent works, and `erase_subject_data` actually deletes subject rows from `zalo_engine.followers`, `zalo_engine.messages`, and `dsar_requests`, with per-store counts returned.
- [x] `RIGHT_TO_DELETE` DSAR marks the request `COMPLETED` after a real purge, and names every store it cannot reach instead of closing silently.
- [x] `mekong privacy consent` and `mekong privacy erase` render help and execute against a tmp database.
- [x] Boundary and invariant suites pass: `test_core_boundary`, `test_raas_license_verifier`, `test_durian_grab_honest_diagnosis`, `test_github_content_25_step_sync`.
- [x] `ruff check src/ tests/` clean; CLI group count does not regress.

## Non-goals

- No rename of the `ke-toan` CLI command (it is listed in `dna/command-surface.json:130`, so a rename trips `core-dna-gate`). Compliance claims change; the command surface does not.
- No global removal of the `nowpayments` rail — non-VN tenants keep it.
- No change to VAT computation, VAS journal logic, Decimal rounding, or XML structure.
- No contact with `src/core/opencore/phase_559_opencore_25_step_catalog.py` (byte-for-byte invariant) or `.mekong/company.json`.
- Out of scope: Pilot A, quarantine floor, approval HMAC hardening, `MEKONG-BENCH` — separate change.

## Constraints

- OpenCore modules under `src/core/opencore/` and `src/core/raas_license_verifier.py` must stay `<= 185 LOC`.
- `tests/test_dual_rail_checkout.py` asserts both rails appear in `/v1/pricing` and the 410 payload; keep advertising, gate at checkout.
- `src/core/` stays provider-neutral per `tests/test_core_boundary.py` — no vendor SDK imports.
- No paid API calls, no real deployment, no secrets printed. Tests use tmp SQLite via each engine's `db_path` argument.
- User-facing CLI strings and docs stay Vietnamese.

## Rollback

Revert the single PR. Changes are additive DDL plus claim-wording edits; a revert
restores HEAD behaviour with no data cleanup.

---
title: "Phase 04 — MEKONG-BENCH 5-Layer Deterministic Suite & Gate Ledger"
status: completed
---

# Phase 04 — MEKONG-BENCH 5-Layer Deterministic Suite & Gate Ledger

## Context

To evaluate runtime trustworthiness without LLM grading bias, the strategic
research specifies a 5-layer deterministic benchmark (`MEKONG-BENCH`) where each
layer has an exact programmatic oracle, plus a Gate Ledger (`G0–G13`) tracking
all technical and commercial gates.

## Requirements

1. Create `src/opc/mekong_bench.py` implementing `MekongBenchRunner`:
   - `run_all(tmp_dir: Path | None = None) -> BenchSuiteResult` executing five
     deterministic layers:
     1. `layer_1_deterministic_task`: verifies exact `Decimal` quote math and
        EMVCo CRC16-CCITT determinism across repeated runs.
     2. `layer_2_dependency_graph`: verifies upstream failure / quarantine block
        halts downstream quote, approval, and connector nodes (`0` side effects).
     3. `layer_3_external_api_failure`: verifies connector timeout /
        `uncertain_reconciliation_required` transitions the run to
        `reconciliation_required` without blind retry duplication.
     4. `layer_4_duplicate_event`: verifies concurrent 2-worker token consumption
        and duplicate `idempotency_key` replay execute the side effect exactly once.
     5. `layer_5_human_approval_interruption`: verifies unapproved, expired,
        revoked, payload-tampered, and HMAC-forged tokens all raise
        `ApprovalSecurityError` and never reach the connector.
   - `format_markdown_table(result: BenchSuiteResult) -> str` rendering a clear
     `PASS/FAIL` summary table.
2. Create `tests/test_mekong_bench.py` asserting 5/5 layers pass (`pass_rate == 1.0`)
   and verifying the rendered markdown table.
3. Write `plans/reports/gate-status-g0-g13.md` recording the verified status and
   command evidence for Gates `G0` through `G13`.

## Files

- `src/opc/mekong_bench.py`
- `tests/test_mekong_bench.py`
- `plans/reports/gate-status-g0-g13.md`

## Validation

- `python3 -m pytest tests/test_mekong_bench.py -v`

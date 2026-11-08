# Mekong CLI — Gate Status Ledger (`G0`–`G13`) & `MEKONG-BENCH` Evaluation Report

**Date:** 2026-11-08  
**Issue:** [#140](https://github.com/minhlongs/mekong-cli/issues/140)  
**Branch:** `feat/opc-quarantine-pilot-a-and-bench`

---

## 1. Strategic Gate Status Ledger (`G0`–`G13`)

| Gate | Gate Name | Status | Verification Command / Programmatic Evidence |
| :--- | :--- | :---: | :--- |
| **G0** | Strategic Problem & Wedge Lock | **VERIFIED IN CODE** | Pilot A wedge (`Zalo OA → Quarantine → Quote + VietQR → Approval Card`) locked and implemented in `src/opc/pilot_a.py`. |
| **G1** | Neutral Core & AST Boundary | **VERIFIED IN CODE** | `python3 -m pytest tests/test_core_boundary.py tests/test_opc_platform_contract.py` (`16 passed` — 0 forbidden imports in `src/core/` and `src/opc/`). |
| **G2** | Promise Spine & Durable State | **VERIFIED IN CODE** | `python3 -m pytest tests/test_promise_spine_wave1.py` (`38 passed` — SQLite WAL state & transition invariants). |
| **G3** | Capability Bus & Governance | **VERIFIED IN CODE** | `python3 -m pytest tests/test_autonomous_runtime_trust_matrix.py` (`20 passed` — capability registration & risk gating). |
| **G4** | Payload-Bound HMAC Approval & Atomic Single-Use | **VERIFIED IN CODE** | `python3 -m pytest tests/test_opc_approval_security.py` (`6 passed` — SHA-256 payload digest + HMAC-SHA256 signature binding + 2-worker SQLite atomic lock). |
| **G5** | Honest Usage & Pre-Execution Budget Reservation | **VERIFIED IN CODE** | `tests/test_opc_approval_security.py::test_criterion_j_budget_reservation_and_honest_unknown_usage` (`passed` — hard ceiling blocks overspend; unknown BYOK stays unknown). |
| **G6** | Untrusted Input Quarantine Floor | **VERIFIED IN CODE** | `python3 -m pytest tests/test_quarantine_floor.py` (`4 passed` — 50/50 VI+EN injection samples blocked across NFC/NFD/zero-width obfuscation, `0` tool calls dispatched, `<untrusted_customer_input>` boundary tag neutralization). |
| **G7** | Pack Manifest Contract & VN Pack Hygiene | **VERIFIED IN CODE** | `src/opc/packs/vn-sme-ops/pack.json` (`entrypoint="src.opc.engine:OPCEngine"`, pre-accounting draft compliance caveats) + `fixtures/` verified by `tests/test_opc_platform_contract.py`. |
| **G8** | Pilot A End-to-End Vertical Slice | **VERIFIED IN CODE** | `python3 -m pytest tests/test_pilot_a_e2e.py` (`4 passed` — 48h Zalo window check, QuarantineFloor, `Decimal` quote math, EMVCo VietQR `000201010212...` + CRC16-CCITT, HMAC approval card, idempotent dispatch). |
| **G9** | `MEKONG-BENCH` 5-Layer Deterministic Suite | **VERIFIED IN CODE** | `python3 -m pytest tests/test_mekong_bench.py` (`2 passed` — 5/5 layers pass with `pass_rate=100.00%` against programmatic oracles). |
| **G10** | OpenCore 25-Step Catalog & RaaS Verifier Integrity | **VERIFIED IN CODE** | `python3 -m pytest tests/test_raas_license_verifier.py tests/test_github_content_25_step_sync.py tests/test_durian_grab_honest_diagnosis.py` (`19 passed`; `registered_groups=189`; all OpenCore/OPC modules `<= 185 LOC`). |
| **G11** | Live Zalo OA Production Webhook Onboarding | **PENDING COMMERCIAL / OPS** | Requires merchant-owned Zalo Official Account production app secret & webhook verification in customer environment (waived for offline repo verification). |
| **G12** | Live Napas 247 / Sepay Bank Webhook Settlement | **PENDING COMMERCIAL / OPS** | Requires live merchant bank webhook credentials; offline EMVCo QR generation & HMAC webhook verifier are verified in `src/core/vietqr_engine.py`. |
| **G13** | Paid Design-Partner Cohort Conversion (5–10 VN SMEs) | **PENDING COMMERCIAL / OPS** | Commercial pilot milestone following Pilot A technical readiness. |

---

## 2. `MEKONG-BENCH` 5-Layer Deterministic Suite Results

Executed via:

```bash
python3 -c "from src.opc.mekong_bench import MekongBenchRunner; r = MekongBenchRunner(); print(r.format_markdown_table(r.run_all()))"
```

| Layer | Benchmark Name | Verdict | Assertions | Programmatic Oracle Evidence |
| :--- | :--- | :--- | :---: | :--- |
| L1 | Deterministic Task (Decimal Quote + EMVCo CRC16) | PASS | 4 | `amount_vnd=5000000, crc16=7AAC` |
| L2 | Dependency Graph Halting on Quarantine Failure | PASS | 2 | `quarantine_blocked=True, dispatches=0` |
| L3 | External API Timeout Reconciliation Guard | PASS | 2 | `status=reconciliation_required, blind_retries=0` |
| L4 | Duplicate Event & Concurrent Worker Idempotency | PASS | 5 | `atomic_wins=1, first=completed, second=deduplicated` |
| L5 | Human Approval Interruption & HMAC Binding | PASS | 5 | `blocked=5/5, dispatches=0` |

**Summary:** 5/5 layers passed (`pass_rate=100.00%`).

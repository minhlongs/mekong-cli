# Kiến trúc Công nghệ: Maritime Phases 371–374

**Tiêu chuẩn Kiến trúc:** Hybrid Modular Facade (<200 LOC/file), Clean Architecture, Zero-Mock Testing, Type-Safe Ergonomics.

## 1. Công nghệ & Nền tảng
- **Runtime:** Python 3.11+
- **Kiến trúc Lõi (Core Engines):** Standard Library (`dataclasses`, `math`, `typing`, `enum`) — Không phụ thuộc ngoại vi nặng, bảo đảm tính toán thời gian thực determinism và latency < 1ms.
- **Giao diện Dòng lệnh (CLI):** Typer (v0.9.0+) với 8 song ngữ Việt - Anh aliases (`shaftpto`/`mayphattruc`, `berthalloc`/`dieudocauport`, `biofoul`/`sambanhabien`, `wasteoil`/`dauthaicang`).
- **AI Agent Integration:** FastMCP (Model Context Protocol) với 4 công cụ bất đồng bộ phục vụ Sophia AI Factory & Mekong Copilot.
- **Kiểm thử Tự động:** Pytest zero-mock unit & integration suites, kiểm thử 100% logic biên và cảnh báo an toàn.

## 2. Tiêu chuẩn Kỹ thuật Quốc tế & Pháp lý Việt Nam
| Phân hệ | Cơ quan Ban hành | Văn bản / Công ước Áp dụng |
|---|---|---|
| **Phase 371** | DNV / IEC / IMO | DNV-RU-SHIP Pt.4 Ch.8, IEC 60092-501, IMO MEPC.333(76) (EEXI/CII) |
| **Phase 372** | UNCTAD / PIANC / Bộ GTVT | UNCTAD Port Handbook, PIANC WG 158, Quyết định 1579/QĐ-TTg |
| **Phase 373** | IMO / BIMCO / Bộ TNMT | IMO Res. MEPC.378(80), BIMCO IWC 2021, Luật BVMT 2020, QCVN 08-MT:2015 |
| **Phase 374** | IMO / Bộ TNMT / Bộ GTVT | MARPOL Annex I Reg 12/13, Basel Conv, Thông tư 02/2022, TT 39/2023 |

## 3. Cấu trúc Mô-đun Code (<200 LOC/file)
1. `src/core/maritime/phase_371_shaft_generator_pto_pti.py`: PTO/PTI hybrid propulsion, SFOC optimization, torque & speed inhibits.
2. `src/core/maritime/phase_372_port_berth_crane_bap_qcsp.py`: Continuous Berth Allocation (BAP) & Quay Crane Scheduling (QCSP), tidal gating, crane non-crossing.
3. `src/core/maritime/phase_373_biofouling_hull_cleaning.py`: Level of Fouling (LoF 0–5), hydrodynamic fuel penalty, in-water cleaning capture criteria.
4. `src/core/maritime/phase_374_port_waste_oil_coprocessing.py`: Reception flash point test (>= 60°C), centrifugal dewatering (15 ppm), RFO clinker co-processing offset.
5. `src/core/maritime_pto_berth_biofoul_waste_engine.py`: Central Unified Multi-Domain Facade.
6. `src/cli/commands/maritime_pto_berth_biofoul_waste_command.py`: 4 Typer CLI command groups & JSON formatters.
7. `scripts/mcp_server.py`: 4 FastMCP async tool endpoints.
8. `tests/test_maritime_pto_berth_unit_suite.py`: Unit test suite cho Phases 371 & 372.
9. `tests/test_maritime_biofoul_waste_unit_suite.py`: Unit test suite cho Phases 373 & 374.
10. `tests/test_maritime_371_to_374_cli_mcp_suite.py`: E2E CLI & FastMCP integration test suite.

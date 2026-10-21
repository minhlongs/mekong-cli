# Implementation Plan: Maritime Phases 363–366

## Overview
Triển khai hệ thống 4 phân hệ kỹ thuật hàng hải, an toàn sinh mạng LSA, lưới điện tàu PMS, môi trường trầm tích cảng biển & thẩm định tàu lai OVID Phases 363–366:
1. Phase 363: LSA Free-Fall Lifeboat & Hydrostatic Release Unit (HRU) Engine (SOLAS III/13, MSC.81(70), a_max <= 15g, angle 50°-65°, HRU depth 1.5 - 4.0m).
2. Phase 364: Marine Generator PMS & Blackout Prevention Engine (SOLAS II-1/53, IEC 60092-202, auto-start >= 85% MCR, preferential tripping stages 1-3, under-freq trip 57.0Hz).
3. Phase 365: Port Dredging Sediment Quality & Beneficial Reuse Engine (London Protocol 1996, QCVN 43:2017 Class 1, TBT <= 0.001 mg/kg, solids >= 60%, UCS >= 50 kPa).
4. Phase 366: OCIMF OVID Tug Vetting & Towing Winch Safety Engine (OCIMF OVID, winch brake hold >= 80% MBL, certified continuous BP, STCW III/3 endorsement).

## Task Checklist
- [x] Bước 1: Tạo 4 micro-engines độc lập trong `src/core/maritime/` (< 200 LOC/file)
  - `phase_363_lsa_lifeboat_hru_release.py`
  - `phase_364_marine_generator_pms_blackout.py`
  - `phase_365_dredging_sediment_beneficiation.py`
  - `phase_366_ovid_tug_winch_vetting.py`
- [x] Bước 2: Tạo Facade trung tâm `src/core/maritime_lsa_pms_dredge_tug_engine.py` (< 200 LOC)
- [x] Bước 3: Tạo lệnh CLI Typer với 8 bí danh tiếng Việt trong `src/cli/commands/maritime_lsa_pms_dredge_tug_command.py` (< 200 LOC)
- [x] Bước 4: Đăng ký CLI groups vào `src/cli/app_setup.py` và 4 FastMCP tools vào `scripts/mcp_server.py`
- [x] Bước 5: Viết 3 test suites zero-mock (< 200 LOC/file):
  - `tests/test_maritime_lsa_pms_unit_suite.py`
  - `tests/test_maritime_dredge_tug_unit_suite.py`
  - `tests/test_maritime_363_to_366_cli_mcp_suite.py`
- [x] Bước 6: Chạy kiểm thử pytest 100% pass, kiểm tra ruff linter và cập nhật roadmap, changelog & memory

## Phase Dependencies
- Phase 363 & 364: Hoàn toàn độc lập ở tầng core logic.
- Phase 365 & 366: Hoàn toàn độc lập ở tầng core logic.
- Facade, CLI & MCP phụ thuộc vào 4 micro-engines.

# Implementation Plan: Maritime Phases 351–354

## Overview
Triển khai hệ thống 4 phân hệ kỹ thuật hàng hải, bảo vệ môi trường biển & chứng nhận số Phases 351–354:
1. Phase 351: Bulk Carrier Loading Computer, Stability & Hull Stress Engine (SOLAS XII/11, IACS UR S1/S1A, 2008 IS Code GM/GZ)
2. Phase 352: HNS Chemical Spill Drift Trajectory & Hazard Zone Engine (OPRC-HNS 2000, CEDRE SEACARAMB, surface leeway drift)
3. Phase 353: Central Seawater Cooling & MGPS Bio-Fouling Prevention Engine (Plate heat exchanger LMTD, scoop energy savings, Cu/Al ion dosing)
4. Phase 354: Marine E-Certificates & W3C Verifiable Credentials Engine (IMO FAL.5/Circ.39/Rev.2, UTN lineage, digital signature verification)

## Task Checklist
- [x] Bước 1: Tạo 4 micro-engines độc lập trong `src/core/maritime/` (< 200 LOC/file)
  - `phase_351_bulk_loading_stability.py` (SOLAS XII/11 BM/SF, GM fluid, GZ righting arm) (103 LOC)
  - `phase_352_hns_chemical_spill_drift.py` (OPRC-HNS 2000, CEDRE SEACARAMB drift vector, hazard zone) (113 LOC)
  - `phase_353_central_cooling_mgps.py` (PHE LMTD, seawater scoop, MGPS Cu/Al ion dosing) (105 LOC)
  - `phase_354_marine_ecert_verification.py` (FAL.5/Circ.39 UTN, cryptographic proof, certificate lifecycle) (100 LOC)
- [x] Bước 2: Tạo Facade trung tâm `src/core/maritime_loading_hns_cool_ecert_engine.py` (45 LOC < 200 LOC)
- [x] Bước 3: Tạo lệnh CLI Typer với 8 bí danh tiếng Việt trong `src/cli/commands/maritime_loading_hns_cool_ecert_command.py` (138 LOC < 200 LOC)
- [x] Bước 4: Đăng ký CLI groups vào `src/cli/app_setup.py` và 4 FastMCP tools vào `scripts/mcp_server.py`
- [x] Bước 5: Viết test suites zero-mock (< 200 LOC/file):
  - `tests/test_maritime_loading_hns_cool_ecert_unit_suite.py` (101 LOC)
  - `tests/test_maritime_cooling_ecert_unit_suite.py` (133 LOC)
  - `tests/test_maritime_loading_hns_cool_ecert_cli_mcp_suite.py` (134 LOC)
- [x] Bước 6: Chạy kiểm thử pytest 100% pass (16/16 tests passed) và cập nhật tài liệu roadmap & memory

# Implementation Plan: Maritime Phases 355–358

## Overview
Triển khai hệ thống 4 phân hệ kỹ thuật hàng hải, bảo vệ môi trường biển & an toàn an ninh số Phases 355–358:
1. Phase 355: LPG Cargo Reliquefaction & Compressor Control Engine (IGC Code Ch.7, cascade refrigeration COP, BOG re-condensation, MARVS margin)
2. Phase 356: MARPOL Annex I Bilge Sludge Management & Incinerator Control Engine (MEPC.259(68), sludge dewatering, 850°C/1100°C chamber interlock, OWS 15 ppm valve)
3. Phase 357: Smart Mooring Line Tension & Quay Berth Surge Monitoring Engine (OCIMF MEG4, WLL/MBL limits, passing ship hydrodynamic surge interaction, snap-back hazard boundary)
4. Phase 358: Maritime Cyber Risk Management & OT/IT Network Resilience Engine (IMO Res. MSC.428(98), IACS UR E26/E27, IEC 62443 zones, NMEA anomaly detection, satellite failover)

## Task Checklist
- [x] Bước 1: Tạo 4 micro-engines độc lập trong `src/core/maritime/` (< 200 LOC/file)
  - `phase_355_lpg_reliquefaction_compressor.py` (IGC Ch.7 BOG, COP, MARVS relief margin)
  - `phase_356_marpol_sludge_incinerator.py` (MARPOL Reg 12 sludge gen, incinerator interlocks, OWS 15 ppm)
  - `phase_357_smart_mooring_surge_meg4.py` (OCIMF MEG4 WLL, hydrodynamic surge force, snap-back zones)
  - `phase_358_maritime_cyber_resilience.py` (IACS UR E26/E27 OT/IT zones, NMEA spoof detection, satellite failover)
- [x] Bước 2: Tạo Facade trung tâm `src/core/maritime_lpg_sludge_mooring_cyber_engine.py` (< 200 LOC)
- [x] Bước 3: Tạo lệnh CLI Typer với 8 bí danh tiếng Việt trong `src/cli/commands/maritime_lpg_sludge_mooring_cyber_command.py` (< 200 LOC)
- [x] Bước 4: Đăng ký CLI groups vào `src/cli/app_setup.py` và 4 FastMCP tools vào `scripts/mcp_server.py`
- [x] Bước 5: Viết 3 test suites zero-mock (< 200 LOC/file):
  - `tests/test_maritime_lpg_sludge_unit_suite.py`
  - `tests/test_maritime_mooring_cyber_unit_suite.py`
  - `tests/test_maritime_lpg_sludge_mooring_cyber_cli_mcp_suite.py`
- [x] Bước 6: Chạy kiểm thử pytest 100% pass, kiểm tra ruff linter và cập nhật tài liệu roadmap & memory

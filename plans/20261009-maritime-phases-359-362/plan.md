# Implementation Plan: Maritime Phases 359–362

## Overview
Triển khai hệ thống 4 phân hệ kỹ thuật hàng hải, cơ khí động lực trục, khí trơ & môi trường cảng xa bờ Phases 359–362:
1. Phase 359: Adaptive Autopilot & Rudder Angle Monitoring Engine (IMO Res. MSC.64(67), ISO 11674, Norrbin non-linear steering model, adaptive sea-state deadband, SOLAS II-1/29 rudder follow-up lag alert).
2. Phase 360: Propeller Shaft Alignment & Whirling Vibration Engine (IACS UR M68, aft stern tube bearing ASTB load pressure <= 0.8 MPa, blade passing frequency BPF, barred speed range BSR).
3. Phase 361: N2 Inert Gas Generator & Dew Point Control Engine (IMO IGC Code Ch.9, hollow-fiber membrane O2 <= 1.0% vol, dew point T_dew <= -40°C, dryer delta-P regeneration alert).
4. Phase 362: Remote Seaport Wastewater Recycling & Zero-Discharge Engine (MARPOL Annex IV, QCVN 14/40, MBR/UV BOD5 <= 20 mg/L, zero-liquid discharge recovery >= 85%, brackish RO trigger).

## Task Checklist
- [x] Bước 1: Tạo 4 micro-engines độc lập trong `src/core/maritime/` (< 200 LOC/file)
  - `phase_359_adaptive_autopilot_rudder.py` (111 LOC)
  - `phase_360_shaft_alignment_vibration.py` (102 LOC)
  - `phase_361_n2_inert_gas_dew_point.py` (98 LOC)
  - `phase_362_seaport_wastewater_recycling.py` (103 LOC)
- [x] Bước 2: Tạo Facade trung tâm `src/core/maritime_autopilot_shaft_inert_waste_engine.py` (< 200 LOC, 118 LOC)
- [x] Bước 3: Tạo lệnh CLI Typer với 8 bí danh tiếng Việt trong `src/cli/commands/maritime_autopilot_shaft_inert_waste_command.py` (< 200 LOC, 145 LOC)
- [x] Bước 4: Đăng ký CLI groups vào `src/cli/app_setup.py` và 4 FastMCP tools vào `scripts/mcp_server.py`
- [x] Bước 5: Viết 3 test suites zero-mock (< 200 LOC/file):
  - `tests/test_maritime_autopilot_shaft_unit_suite.py` (121 LOC)
  - `tests/test_maritime_inert_waste_unit_suite.py` (116 LOC)
  - `tests/test_maritime_359_to_362_cli_mcp_suite.py` (127 LOC)
- [x] Bước 6: Chạy kiểm thử pytest 100% pass, kiểm tra ruff linter và cập nhật roadmap, changelog & memory

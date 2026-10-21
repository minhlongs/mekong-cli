# Implementation Plan: Maritime Phases 367–370

## Overview
Triển khai hệ thống 4 phân hệ kỹ thuật hàng hải, chất lượng nhiên liệu ISO 8217, hệ thống pin tích năng tàu biển BESS, chỉ số tàu xanh ESI & điều khiển tời buộc tàu cân bằng sóng AHC Phases 367–370:
1. Phase 367: Marine Fuel Oil Quality Assessment & ISO 8217 Bunker Compatibility Engine (ISO 8217:2024, Al+Si <= 60 ppm, flash point >= 60°C, TSP <= 0.10%, ASTM D4740 spot test 1-5).
2. Phase 368: Marine Battery Energy Storage System (BESS) & Peak Shaving Safety Engine (DNV-RU-SHIP Pt.6 Ch.2, IEC 62619, SoC 15-90%, C-rate, off-gas H2/CO 3-stage safety trip).
3. Phase 369: World Ports Environmental Ship Index (ESI) & Green Port Dues Incentive Engine (IAPH WPCI ESI, Thông tư 39/2023/TT-BGTVT, OPS cold-ironing bonus +35, rebate 5-20%).
4. Phase 370: Mooring Winch Auto-Tension & Active Heave Compensation (AHC) Engine (OCIMF MEG4, ISO 3730, IMCA D 018, render/heave window, AHC efficiency >= 85%).

## Task Checklist
- [ ] Bước 1: Tạo 4 micro-engines độc lập trong `src/core/maritime/` (< 200 LOC/file)
  - `phase_367_fuel_oil_iso8217_compatibility.py`
  - `phase_368_marine_battery_bess_safety.py`
  - `phase_369_port_esi_green_incentive.py`
  - `phase_370_mooring_autotension_ahc.py`
- [ ] Bước 2: Tạo Facade trung tâm `src/core/maritime_fuel_bess_esi_ahc_engine.py` (< 200 LOC)
- [ ] Bước 3: Tạo lệnh CLI Typer với 8 bí danh tiếng Việt trong `src/cli/commands/maritime_fuel_bess_esi_ahc_command.py` (< 200 LOC)
- [ ] Bước 4: Đăng ký CLI groups vào `src/cli/app_setup.py` và 4 FastMCP tools vào `scripts/mcp_server.py`
- [ ] Bước 5: Viết 3 test suites zero-mock (< 200 LOC/file):
  - `tests/test_maritime_fuel_bess_unit_suite.py`
  - `tests/test_maritime_esi_ahc_unit_suite.py`
  - `tests/test_maritime_367_to_370_cli_mcp_suite.py`
- [ ] Bước 6: Chạy kiểm thử pytest 100% pass, kiểm tra ruff linter và cập nhật roadmap, changelog & memory

## Phase Dependencies
- Phase 367 & 368: Hoàn toàn độc lập ở tầng core logic.
- Phase 369 & 370: Hoàn toàn độc lập ở tầng core logic.
- Facade, CLI & MCP phụ thuộc vào 4 micro-engines.

# Implementation Plan: Maritime Phases 347–350

## Overview
Triển khai hệ thống 4 phân hệ kỹ thuật hàng hải & thương mại điện tử chuyên sâu Phases 347–350:
1. Phase 347: Impressed Current Cathodic Protection (ICCP) & Sacrificial Anode Engine
2. Phase 348: Marine Engine SCR & Dual-Fuel ME-GI NOx Tier III Engine
3. Phase 349: Port Anchorage Windlass Holding Power & Ground Tackle Scope Engine
4. Phase 350: Electronic Bill of Lading (e-BL) Title Transfer & MLETR Engine

## Task Checklist
- [x] Bước 1: Tạo 4 micro-engines độc lập trong `src/core/maritime/` (< 200 LOC/file)
  - `phase_347_iccp_cathodic_protection.py` (NACE SP0176, Ag/AgCl reference potential, current density)
  - `phase_348_engine_scr_megi_nox.py` (MARPOL VI Tier III NOx, SCR urea dosing, methane slip)
  - `phase_349_anchorage_windlass_holding.py` (IACS UR A1 EN, anchor holding power, dragging alert)
  - `phase_350_ebl_mletr_transfer.py` (MLETR title transfer, hash lineage, release verification)
- [x] Bước 2: Tạo Facade trung tâm `src/core/maritime_iccp_scr_anchor_ebl_engine.py` (< 200 LOC)
- [x] Bước 3: Tạo lệnh CLI Typer với 8 bí danh tiếng Việt trong `src/cli/commands/maritime_iccp_scr_anchor_ebl_command.py` (< 200 LOC)
- [x] Bước 4: Đăng ký CLI groups vào `src/cli/app_setup.py` và 4 FastMCP tools vào `scripts/mcp_server.py`
- [x] Bước 5: Viết 2 test suites zero-mock (< 200 LOC/file):
  - `tests/test_maritime_iccp_scr_anchor_ebl_unit_suite.py`
  - `tests/test_maritime_iccp_scr_anchor_ebl_cli_mcp_suite.py`
- [x] Bước 6: Chạy kiểm thử pytest 100% pass và cập nhật tài liệu roadmap & memory

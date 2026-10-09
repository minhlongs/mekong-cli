# Implementation Plan: Maritime Phases 343–346

## Overview
Triển khai hệ thống 4 phân hệ hàng hải kỹ thuật cao Phases 343–346 theo chuẩn Hybrid Modular Facade:
1. Phase 343: ECDIS Passage Planning & Safety Contour Navigation Engine
2. Phase 344: Bunkering MFM Coriolis Mass Balance & Cappuccino Alert Engine
3. Phase 345: Marine Boiler Water Chemistry Treatment & Blowdown Rate Engine
4. Phase 346: Port Agency PDA/FDA Disbursements Account Reconciliation Engine

## Task Checklist
- [x] Bước 1: Tạo 4 micro-engines độc lập trong `src/core/maritime/` (< 200 LOC/file)
- [x] Bước 2: Tạo Facade trung tâm `src/core/maritime_ecdis_mfm_boiler_agency_engine.py` (< 200 LOC)
- [x] Bước 3: Tạo lệnh CLI Typer với 8 bí danh tiếng Việt trong `src/cli/commands/maritime_ecdis_mfm_boiler_agency_command.py` (< 200 LOC)
- [x] Bước 4: Đăng ký CLI groups vào `src/cli/app_setup.py` và 4 FastMCP tools vào `scripts/mcp_server.py`
- [x] Bước 5: Viết 2 test suites zero-mock: Unit test suite và CLI/MCP suite (< 200 LOC/file)
- [x] Bước 6: Chạy kiểm thử pytest 100% pass và cập nhật tài liệu roadmap & memory

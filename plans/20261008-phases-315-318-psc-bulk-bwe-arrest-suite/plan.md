# Implementation Plan: Phases 315-318 Maritime PSC, Bulk Cargo, BWE & Vessel Arrest Suite

## Executive Overview
Triển khai bộ 4 nghiệp vụ hàng hải tuân thủ quốc tế & tài chính tranh chấp theo kiến trúc Simplest Viable:
- **Phase 315**: Tokyo MoU Port State Control (PSC) Inspection Targeting & Deficiency Risk Engine.
- **Phase 316**: IMSBC Code Solid Bulk Cargo Liquefaction & TML/FMP Transport Safety Engine.
- **Phase 317**: BWM Convention Ballast Water Exchange (D-1) vs Treatment (D-2) Compliance Engine.
- **Phase 318**: Maritime Lien Enforcement, Judicial Sale & Vessel Arrest Waterfall Engine (Bộ luật Hàng hải VN 2015).

---

## Technical Architecture & Files
1. **Core Engine**: `src/core/maritime_psc_bulk_bwe_arrest_engine.py`
   - `PscTargetingEngine`: Đánh giá Ship Risk Profile (HRS/SRS/LRS) và cửa sổ kiểm tra PSC.
   - `BulkCargoLiquefactionEngine`: Đánh giá rủi ro hóa lỏng hàng rời theo IMSBC Code (FMP/TML).
   - `BallastWaterComplianceEngine`: Thẩm tra phương thức tuân thủ D-1 vs D-2, khoảng cách bờ >= 200 NM, độ sâu >= 200m.
   - `VesselArrestWaterfallEngine`: Thứ tự ưu tiên giải quyết khiếu nại hàng hải và bán đấu giá tàu (Art 37 Bộ luật Hàng hải VN).
2. **Unit Tests**: `tests/test_maritime_psc_bulk_bwe_arrest_suite.py` (100% zero-mock, deterministic).
3. **CLI Commands**: `src/cli/commands/maritime_psc_bulk_bwe_arrest_command.py` (Typer sub-apps).
4. **App Setup**: Đăng ký 8 nhóm lệnh CLI mới vào `src/cli/app_setup.py`.
5. **FastMCP Server**: Đăng ký 4 công cụ MCP mới vào `scripts/mcp_server.py`.
6. **Documentation & Memory**: Cập nhật `MEMORY.md`.

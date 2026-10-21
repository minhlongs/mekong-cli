# Implementation Plan: Phases 319-322 Maritime Navigation, GA, VGM & Insurance Suite

## Executive Overview
Triển khai bộ 4 nghiệp vụ hàng hải cốt lõi theo tiêu chuẩn quốc tế và Bộ luật Hàng hải Việt Nam 2015 theo triết lý Simplest Viable (Zero external dependencies, 100% deterministic):
- **Phase 319**: COLREGs 1972 Collision Prevention & Risk of Collision Assessment Engine (Rules 7, 8, 13, 14, 15, 16, 17, CPA/TCPA).
- **Phase 320**: York-Antwerp Rules 2016 General Average (Tổn thất chung) Adjustment Engine (Contributory values, GA sacrifice, GA expenditure & rate).
- **Phase 321**: SOLAS VI/2 Container Verified Gross Mass (VGM) Safety Engine (Method 1 & Method 2, tolerance check, max payload & No-VGM-No-Load rule).
- **Phase 322**: Institute Time Clauses - Hulls (ITC-Hulls 1/10/83) Marine Insurance Settlement Engine (Particular Average, CTL/ATL test, 3/4 RDC collision liability & Deductible).

---

## Technical Architecture & Files
1. **Core Engine**: `src/core/maritime_colregs_ga_vgm_insurance_engine.py`
   - `ColregsNavigationEngine`: Đánh giá góc mạn (relative bearing), phân loại tình huống gặp nhau (Head-on, Crossing, Overtaking), tính CPA/TCPA, xác định tàu nhường đường (Give-way) vs tàu giữ hướng (Stand-on) và khuyến cáo điều động.
   - `GeneralAverageAdjustmentEngine`: Phân bổ tổn thất chung (GA Contribution) theo YAR 2016 và Điều 292-297 Bộ luật Hàng hải VN 2015. Tính tỷ lệ đóng góp tổn thất chung dựa trên giá trị chịu phân bổ (Vessel + Cargo CIF + Freight).
   - `ContainerVgmComplianceEngine`: Thẩm tra khối lượng toàn bộ của container (VGM) theo SOLAS VI/2 và TT 41/2016/TT-BGTVT. Kiểm tra dung sai $\pm 5\%$ hoặc tối đa $1000\text{ kg}$, chặn container quá tải Payload.
   - `ItcHullsClaimEngine`: Tính toán bồi thường bảo hiểm thân tàu theo ITC-Hulls 1/10/83 và Bộ luật HHVN. Đánh giá điều kiện tổn thất toàn bộ ước tính (CTL), khấu trừ (Deductible Clause 12), phân bổ 3/4 trách nhiệm đâm va (3/4 RDC Clause 8).

2. **Unit Tests**: `tests/test_maritime_colregs_ga_vgm_insurance_suite.py`
   - 100% zero-mock, deterministic unit tests kiểm thử cả 4 engine.

3. **CLI Commands**: `src/cli/commands/maritime_colregs_ga_vgm_insurance_command.py`
   - 4 Typer sub-apps:
     - `colregs_app`: Lệnh `assess`
     - `ga_app`: Lệnh `calculate`
     - `vgm_app`: Lệnh `verify`
     - `insurance_app`: Lệnh `settle`

4. **App Setup**: Đăng ký 8 nhóm lệnh CLI mới vào `src/cli/app_setup.py`.

5. **FastMCP Server**: Đăng ký 4 công cụ MCP mới vào `scripts/mcp_server.py`.

6. **Documentation & Memory**: Cập nhật `MEMORY.md` và `docs/development-roadmap.md`.

# Báo cáo Động não & Kiến trúc Tái cấu trúc: Phân hệ Hàng hải Phases 323–326

## 1. Problem Statement & Requirements
- **Mục tiêu**: Tái cấu trúc và hoàn thiện 4 phân hệ an toàn hàng hải kỹ thuật cao (Phases 323–326):
  - **Phase 323**: Rửa dầu thô (COW) MARPOL Annex I & Rửa két hóa chất IBC Code Ch.16 / P/A Manual.
  - **Phase 324**: Quản lý khí bốc tự nhiên BOG & Đo đạc chuyển giao thương mại LNG CTMS (IGC Code / GIIGNL).
  - **Phase 325**: Cơ cấu móc nhả an toàn xuồng cứu sinh & Thiết bị giữ chống rơi Fall Preventer Device FPD (SOLAS III, MSC.1/Circ.1392 & Circ.1327).
  - **Phase 326**: Cấp phép vào không gian kín Enclosed Space & Kiểm định 4-Gas (IMO Res. A.1050(27), MSC.1/Circ.1401).
- **Ràng buộc**:
  - Quy tắc kích thước file: Giới hạn context dưới 200 LOC/file.
  - Tương thích ngược: Giữ nguyên import contracts, không phá vỡ mô hình CLI 39 groups và FastMCP 52k LOC.
  - Chất lượng code: Zero fake data/mocks, kiểm thử thuần 100% Python, mã băm SHA-256 audit trail chống gian lận.

---

## 2. Evaluated Approaches & Trade-off Analysis

### Cách tiếp cận 1: Micro-Modular (< 200 LOC per file)
- **Cấu trúc**: Tách nhỏ từng Phase thành file riêng (`tanker_wash.py`, `lng_bog.py`, `lifeboat_fpd.py`, `enclosed_space.py`).
- **Ưu điểm**: Triệt để tuân thủ quy tắc 200 LOC, module hóa cao, dễ đọc khi LLM load từng file đơn lẻ.
- **Nhược điểm**: Tăng số lượng file, phân mảnh import nếu không có facade tập trung.

### Cách tiếp cận 2: Domain Cohesion + Refactor
- **Cấu trúc**: Nhóm theo 2 khối nghiệp vụ tự nhiên (Tanker/Gas vs LSA/Enclosed Space), thiết kế registry tự động đăng ký CLI/MCP.
- **Ưu điểm**: Cân bằng tối ưu giữa kích thước file và tính gắn kết logic nghiệp vụ, giảm tải cho `app_setup.py` và `mcp_server.py`.
- **Nhược điểm**: Đòi hỏi thiết kế registry chuẩn để không gây duplicate logic.

### Cách tiếp cận 3: Standard Precedent (Status Quo)
- **Cấu trúc**: Tiếp tục file đơn khối 536 LOC `src/core/maritime_tanker_gas_lsa_enclosed_engine.py`, thêm command file tập trung và test suite như Phases 283–322.
- **Ưu điểm**: Zero overhead cấu trúc mới, tốc độ triển khai nhanh nhất, khớp 100% với 30 suite hàng hải trước đó.
- **Nhược điểm**: Vi phạm quy tắc file < 200 LOC, tiếp tục làm phình to `app_setup.py` (2.6k LOC) và `mcp_server.py` (52k LOC).

---

## 3. Final Recommended Solution: "Cả 3" — Hybrid Unified Modular Architecture
Người dùng đã phê duyệt kết hợp thế mạnh của **Cả 3 cách tiếp cận**:

1. **Lớp Lõi Module hóa (Micro-modular < 200 LOC)**:
   - Tách logic chi tiết thành các sub-module chuyên biệt dưới 200 LOC:
     - `src/core/maritime/phase_323_tanker_wash.py` (~150 LOC)
     - `src/core/maritime/phase_324_lng_gas_custody.py` (~150 LOC)
     - `src/core/maritime/phase_325_lifeboat_fpd.py` (~130 LOC)
     - `src/core/maritime/phase_326_enclosed_space.py` (~130 LOC)
2. **Lớp Mặt tiền Thống nhất (Standard Precedent Facade)**:
   - File `src/core/maritime_tanker_gas_lsa_enclosed_engine.py` đóng vai trò Facade trung tâm re-export toàn bộ dataclasses, Enums và Engines. Đảm bảo mọi bài test, lệnh CLI và script hiện hữu import trực tiếp không bị lỗi.
3. **Lớp CLI & FastMCP Chuẩn hóa (Domain Cohesion & Compatibility)**:
   - CLI Command: `src/cli/commands/maritime_tanker_gas_lsa_enclosed_command.py` với 4 Typer apps (`cow_app`, `bog_app`, `lifeboat_app`, `enclosed_app`) và 8 bí danh tiếng Việt trực quan.
   - Đăng ký vào `src/cli/app_setup.py` theo đúng chuẩn 39 groups.
   - Thêm 4 tools chuyên dụng vào `scripts/mcp_server.py` có validation tham số chặt chẽ.

---

## 4. Implementation Considerations & Risks
- **Rủi ro Import vòng (Circular Imports)**: Tránh tuyệt đối việc sub-module import ngược lại facade; facade chỉ re-export một chiều.
- **Kiểm soát Sai số Số học (Floating Precision)**:
  - Phase 324: Đảm bảo hằng số quy đổi $1\text{ MMBtu} = 1055.05585\text{ MJ}$ làm tròn 2 chữ số thập phân cho báo cáo kiểm toán thương mại.
  - Phase 325: Đảm bảo kiểm tra $FPD\text{ Safety Factor} \ge 6.0$ xử lý an toàn mẫu số 0 khi tải trọng bằng 0.
- **Tính toàn vẹn Dữ liệu (Tamper-evidence)**:
  - Mỗi kết quả đánh giá bắt buộc nhúng `audit_hash` chuẩn SHA-256 xác thực thời gian thực.

---

## 5. Success Metrics & Validation Criteria
1. **Kiểm thử Đơn vị & Tích hợp**:
   - Viết bài test toàn diện tại `tests/test_maritime_tanker_gas_lsa_enclosed_suite.py` bao phủ tối thiểu 20 test cases biên (edge cases).
   - `python3 -m pytest tests/test_maritime_tanker_gas_lsa_enclosed_suite.py -v` đạt 100% Passed.
2. **Kiểm tra Cú pháp & Linting**:
   - `python3 -m ruff check src/ tests/` đạt 0 error/0 warning.
3. **CLI Wiring**:
   - Lệnh `mekong cow --help`, `mekong bog --help`, `mekong lifeboat --help`, `mekong enclosed --help` hoạt động trơn tru với cả bí danh tiếng Việt (`mekong ruaketdau`, `mekong khigaslng`, `mekong xuongcuusinh`, `mekong khonggiankin`).
4. **Cập nhật Tiến độ**:
   - Đánh dấu hoàn thành 100% Phases 323–326 trong `docs/development-roadmap.md`.

---

## 6. Next Steps & Dependencies
1. Chuyển giao sang giai đoạn lập kế hoạch chi tiết (`/plan:fast` hoặc `/plan:hard`).
2. Triển khai phân tách module và hoàn thiện CLI, MCP, Unit Tests.
3. Xác minh toàn bộ test suite và đồng bộ git conventional commit.

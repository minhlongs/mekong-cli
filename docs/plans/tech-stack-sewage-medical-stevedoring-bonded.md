# Kiến trúc Kỹ thuật & Tech Stack: Phases 291–294

## 1. Nguyên tắc Thiết kế Lõi (Core Principles)
- **Zero External Dependencies cho Core Engine**: Toàn bộ logic tính toán MARPOL Annex IV, STCW Medical, Stevedoring Tariffs và Kho Ngoại quan được viết bằng Python 3 standard library (`dataclasses`, `enum`, `datetime`, `typing`, `hashlib`, `math`).
- **Deterministic & Cryptographic Audit Trails**: Sử dụng SHA-256 để tạo mã chứng thực 24 ký tự (`token`) cho các quyết định xả thải nước thải, giấy chứng nhận y tế thuyền viên, biểu hóa đơn bốc dỡ và biên bản giám sát kho ngoại quan.
- **Fail-Closed Safety**: Mặc định từ chối xả thải nếu không thỏa mãn cả 3 điều kiện (khoảng cách, vận tốc, chất lượng STP); từ chối đi biển nếu thuyền viên vi phạm bất kỳ tiêu chuẩn bệnh lý hoặc thị lực/thính lực; gắn cờ nghi vấn tịch thu nếu hàng lưu kho ngoại quan quá hạn 90 ngày.

## 2. Tech Stack Chi tiết

| Thành phần | Công nghệ / Thư viện | Vai trò & Mục đích |
| :--- | :--- | :--- |
| **Lõi nghiệp vụ (Core Engine)** | Python 3.10+ (Standard Library) | `dataclasses`, `enum.Enum`, `hashlib.sha256`, `datetime`. Đảm bảo hiệu năng cao, zero-dependency, dễ bảo trì theo chuẩn YAGNI/KISS/DRY. |
| **Giao diện dòng lệnh (CLI)** | Typer & Rich | Xây dựng 4 ứng dụng Typer con, hiển thị bảng biểu Rich, thanh tiến trình, cảnh báo vi phạm màu sắc trực quan, hỗ trợ 8 bí danh song ngữ Việt - Anh. |
| **Giao thức MCP (FastMCP)** | `mcp.server.fastmcp.FastMCP` | Tích hợp 4 tools chuẩn hóa vào `scripts/mcp_server.py`, hỗ trợ AI Agent tương tác qua JSON-RPC theo kiến trúc Sophia & Mekong CLI. |
| **Kiểm thử tự động (Testing)** | `pytest`, `pytest-asyncio` | Bộ kiểm thử Zero-Mock (không giả lập, không mock), kiểm tra 100% case biên, vi phạm quy định và kiểm tra tích hợp chéo. |
| **Định dạng & Linter** | `ruff`, `mypy` | Kiểm tra cú pháp, loại bỏ import thừa, đảm bảo mã nguồn sạch sẽ, không có lỗi runtime. |

## 3. Cấu trúc Module & Tương tác Dữ liệu

```
src/core/maritime_sewage_medical_stevedoring_bonded_engine.py
├── Phase 291: SewageDischargeEngine (MARPOL Annex IV & MEPC.227(64))
├── Phase 292: SeafarerMedicalEngine (STCW I/9, MLC A1.2, TT 22/2017/TT-BYT)
├── Phase 293: StevedoringTariffEngine (Thông tư 39/2023 & Thông tư 12/2024)
└── Phase 294: BondedWarehouseEngine (Luật Hải quan 2014 & Nghị định 08/2015)

src/cli/commands/maritime_sewage_medical_stevedoring_bonded_command.py
├── sewage_app (`sewage` / `nuocthai`)
├── medical_app (`seafarermedical` / `suckhoethuyenvien`)
├── stevedore_app (`stevedoretariff` / `bocdocangbien`)
└── bonded_app (`bondedwh` / `khongoaiquan`)

scripts/mcp_server.py
├── mekong_marpol_sewage_discharge_evaluate
├── mekong_stcw_seafarer_medical_fitness_verify
├── mekong_port_stevedoring_tariff_calculate
└── mekong_bonded_warehouse_dwell_supervise

tests/test_maritime_sewage_medical_stevedoring_bonded_suite.py
└── 20+ test cases kiểm thử độc lập, không dùng mock
```

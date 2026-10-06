# Product Development Requirements (PDR) — Mekong Enterprise Suite

## 1. Executive Summary
- **Mục tiêu**: Tích hợp bộ giải pháp điều hành doanh nghiệp toàn diện dành cho doanh nhân một thành viên và doanh nghiệp SME Việt Nam vào hệ sinh thái Mekong CLI v6.0.
- **Phạm vi**: 5 trụ cột gồm Tuân thủ Doanh nghiệp & FDI, Sở hữu Trí tuệ, Lao động & BHXH, Đối soát Napas 247 VietQR, và Hợp đồng Thương mại.
- **Nguyên tắc kỹ thuật**: 100% Python Standard Library, Zero external runtime dependencies, 100% deterministic testing.

## 2. Business & Legal Requirements
1. **Doanh nghiệp & FDI**:
   - Luật Doanh nghiệp 2020 (Điều 47, 75): Tính chuẩn thời hạn 90 ngày góp vốn điều lệ từ ngày cấp ĐKKD.
   - Nghị định 122/2021/NĐ-CP: Phạt tiền 30-50 triệu đồng khi vi phạm góp vốn.
   - Luật Đầu tư 2020: Thẩm tra FOL (Foreign Ownership Limits) và yêu cầu chấp thuận sở hữu nước ngoài.
2. **Sở hữu Trí tuệ**:
   - Luật SHTT 2005/2022: Phân loại 45 nhóm Nice quốc tế; thuật toán tính điểm phân biệt (>= 50/100).
3. **Lao động & BHXH**:
   - Nghị định 74/2024/NĐ-CP & Luật Việc làm 2013: 4 vùng lương tối thiểu; trích nộp BHXH/BHYT/BHTN theo trần độc lập; Thuế TNCN 7 bậc.
4. **VietQR & Ngân hàng**:
   - Chuẩn Napas 247 EMVCo QR Code: Đóng gói TLV, tính CRC16-CCITT checksum.
   - Webhook HMAC-SHA256 & Bút toán VAS Nợ 112 / Có 131.
5. **Hợp đồng Thương mại**:
   - Luật Thương mại 2005 (Điều 301): Trần phạt vi phạm tối đa 8% giá trị phần nghĩa vụ bị vi phạm.

## 3. Architecture & Implementation
- **Core Engine**: `src/core/enterprise_suite_engine.py` (5 engine classes).
- **CLI Commands**: `src/cli/commands/enterprise_command.py` (`mekong enterprise` & `mekong doanhnghiep`).
- **MCP Integration**: `src/core/mcp_server.py` (FastMCP) & `scripts/mcp_server.py` (stdio JSON-RPC).
- **Test Coverage**: `tests/test_enterprise_suite.py` (28 deterministic tests, 100% pass rate).

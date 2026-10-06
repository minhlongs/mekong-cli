# System Architecture — Mekong Enterprise Suite

## High-Level Topology

```
                  ┌────────────────────────────────────────┐
                  │    Mekong CLI / AI Agent Interface     │
                  └───────────────────┬────────────────────┘
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          │                                                       │
          ▼                                                       ▼
┌──────────────────┐                                   ┌──────────────────────┐
│ CLI App Surface  │                                   │ MCP Server Surface   │
│ mekong enterprise│                                   │ FastMCP & stdio JSON │
└─────────┬────────┘                                   └──────────┬───────────┘
          │                                                       │
          └───────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
             ┌─────────────────────────────────────────────────┐
             │       Enterprise Suite Core Engines Layer       │
             │     (src/core/enterprise_suite_engine.py)       │
             ├─────────────────────────────────────────────────┤
             │ 1. EnterpriseFDIEngine (Luật DN 2020 & Đầu tư)  │
             │ 2. IntellectualPropertyEngine (Luật SHTT 2022)  │
             │ 3. LaborHRMEngine (BLLĐ 2019 & NĐ 74/2024)      │
             │ 4. VietQRReconEngine (Napas 247 EMVCo QR)       │
             │ 5. EnterpriseAuditEngine (Luật Thương mại 2005) │
             └─────────────────────────────────────────────────┘
```

## Key Components

1. **EnterpriseFDIEngine**:
   - Quản lý vòng đời và tiến độ góp vốn điều lệ trong hạn 90 ngày.
   - Kiểm tra ngưỡng sở hữu vốn FDI theo tỷ lệ WTO và Luật Đầu tư.

2. **IntellectualPropertyEngine**:
   - Từ điển chuẩn hóa 45 nhóm Nice.
   - Thuật toán bóc tách dấu hiệu chung và chấm điểm khả năng cấp bằng nhãn hiệu.

3. **LaborHRMEngine**:
   - Bóc tách phân bổ trách nhiệm chi trả BHXH giữa Người lao động (10.5%) và Người sử dụng lao động (23.5%).
   - Tự động áp dụng trần BHXH/BHYT (20x lương cơ sở) và BHTN (20x lương tối thiểu vùng).
   - Bảng tính Thuế TNCN lũy tiến 7 bậc.

4. **VietQRReconEngine**:
   - Bộ đóng gói payload TLV chuẩn EMVCo Napas 247.
   - Bộ giải mã và xác thực chữ ký Webhook HMAC-SHA256 với constant-time comparison.
   - Khớp giao dịch ngân hàng và sinh bút toán VAS Nợ TK 112 / Có TK 131.

5. **EnterpriseAuditEngine**:
   - Kiểm tra giới hạn 8% phạt vi phạm hợp đồng thương mại (Điều 301 Luật Thương mại 2005).
   - Tổng hợp chỉ số sức khỏe doanh nghiệp 360 độ từ 5 trụ cột.

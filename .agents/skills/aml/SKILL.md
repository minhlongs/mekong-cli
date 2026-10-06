---
name: aml
description: >-
  AML — Vietnamese Anti-Money Laundering, Counter-Terrorist Financing & Sanctions Suite
---

# /aml — AML — Vietnamese Anti-Money Laundering, Counter-Terrorist Financing & Sanctions Suite

AML — Vietnamese Anti-Money Laundering, Counter-Terrorist Financing & Sanctions Suite.

## Usage

```bash
// turbo
mekong aml $ARGUMENTS
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `cdd` | Thực hiện định danh khách hàng CDD, phân tầng rủi ro và xác minh chủ hưởng lợi cuối cùng (UBO). |
| `lctr` | Ghi nhận giao dịch tiền mặt và kiểm tra ngưỡng báo cáo LCTR (>= 400 triệu đồng). |
| `str` | Lập báo cáo giao dịch đáng ngờ (STR) gửi Cục Phòng, chống rửa tiền NHNN. |
| `screening` | Rà soát đối tượng với danh sách đen cấm vận HĐBA LHQ, Bộ Công an và cá nhân PEP. |
| `assess` | Đánh giá quy chế kiểm soát nội bộ về phòng chống rửa tiền và mức độ sẵn sàng FATF. |
| `list` | Tra cứu danh mục hồ sơ CDD, báo cáo LCTR, báo cáo STR, rà soát cấm vận và đánh giá thể chế. |
| `status` | Hiển thị tổng quan các chỉ số telemetry phòng chống rửa tiền quốc gia. |

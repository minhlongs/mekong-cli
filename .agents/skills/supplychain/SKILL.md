---
name: supplychain
description: >-
  SupplyChain — Vietnamese agricultural & timber traceability, EUDR anti-deforestation & EPCIS custody tracking
---

# /supplychain — SupplyChain — Vietnamese agricultural & timber traceability, EUDR anti-deforestation & EPCIS custody tracking

SupplyChain — Vietnamese agricultural & timber traceability, EUDR anti-deforestation & EPCIS custody tracking.

## Usage

```bash
// turbo
mekong supplychain $ARGUMENTS
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `plot` | Đăng ký lô đất canh tác nông lâm sản kèm tọa độ GPS định vị phục vụ EUDR (Quy định 2023/1115). |
| `batch` | Tạo lô hàng xuất khẩu gom từ các vùng trồng, sinh mã vân tay băm SHA-256 khởi tạo. |
| `event` | Ghi nhận sự kiện lưu ký chuỗi cung ứng chuẩn GS1 EPCIS với băm chuỗi bảo chứng toàn vẹn. |
| `eudr` | Tổng hợp Bộ hồ sơ Thẩm định Chuỗi cung ứng Chống phá rừng (EUDR Due Diligence Statement). |
| `trace` | Truy vết toàn bộ hành trình chuỗi cung ứng từ nông trại đến cảng xuất khẩu. |
| `list` | Liệt kê danh sách các vùng trồng hoặc các lô hàng truy xuất nguồn gốc đã đăng ký. |
| `status` | Truy vấn telemetry hệ thống truy xuất nguồn gốc chuỗi cung ứng & giám sát EUDR. |

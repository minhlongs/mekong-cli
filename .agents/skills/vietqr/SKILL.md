---
name: vietqr
description: >-
  VietQR — thanh toán chuyển khoản Napas 247, mã QR EMVCo & đối soát
---

# /vietqr — VietQR — thanh toán chuyển khoản Napas 247, mã QR EMVCo & đối soát

VietQR — thanh toán chuyển khoản Napas 247, mã QR EMVCo & đối soát.

## Usage

```bash
// turbo
mekong vietqr $ARGUMENTS
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `generate` | Tạo mã thanh toán VietQR chuẩn EMVCo và QuickLink Napas 247. |
| `banks` | Tra cứu danh sách các ngân hàng liên kết Napas 247 và mã BIN. |
| `transactions` | Xem lịch sử các giao dịch chuyển khoản ngân hàng đã đối soát. |
| `record` | Ghi nhận đối soát giao dịch chuyển khoản ngân hàng (idempotent). |
| `status` | Kiểm tra trạng thái hệ thống VietQR và số liệu thanh toán. |

---
name: vietqr
description: VietQR and Napas 247 dynamic EMVCo QR code generation, banking webhook verification, and payment reconciliation.
---

# /vietqr — Autonomous VietQR / Napas 247 Instant Payment, Dynamic EMVCo QR Code & Banking Webhook Verification Engine

Providing deterministic banking compliance, EMVCo Tag-Length-Value QR generation with CRC16-CCITT checksums, QuickLink URL synthesis, and idempotent banking webhook reconciliation (Sepay / Napas / Open Banking) under State Bank of Vietnam regulations.

## Statutory Regulations & Standards

1. **Căn cứ Pháp lý & Tiêu chuẩn Quốc gia**:
   - **Quyết định 201/QĐ-NHNN**: Phê duyệt đề án phát triển thanh toán không dùng tiền mặt tại Việt Nam.
   - **Thông tư 07/VBHN-NHNN**: Quy định về hoạt động thanh toán liên ngân hàng và hệ thống bù trừ tự động (Napas 247).
   - **EMVCo QR Code Specification for Payment Systems**: Quy chuẩn quốc tế cho mã QR thanh toán bán lẻ & chuyển khoản nhanh.
2. **Cấu trúc Dữ liệu EMVCo VietQR**:
   - **Tag 00**: Payload Format Indicator (`000201`).
   - **Tag 01**: Point of Initiation Method (`010212` động / `010211` tĩnh).
   - **Tag 38**: Merchant Account Information (GUID Napas `A000000727`, Mã ngân hàng BIN, Số tài khoản).
   - **Tag 53**: Transaction Currency (`5303704` VND).
   - **Tag 54**: Transaction Amount (Số tiền VND).
   - **Tag 58**: Country Code (`5802VN`).
   - **Tag 62**: Additional Data Field Template (Subtag 08: Nội dung chuyển khoản / Memo).
   - **Tag 63**: CRC16-CCITT Checksum (`6304XXXX` đa thức `0x1021`, giá trị khởi tạo `0xFFFF`).
3. **Mã BIN Các Ngân Hàng Napas 247 Phổ Biến**:
   - MBBank: `970422`
   - Vietcombank (VCB): `970436`
   - VietinBank (CTG): `970415`
   - BIDV: `970418`
   - Agribank (VBA): `970405`
   - Techcombank (TCB): `970407`
   - ACB: `970416`
   - TPBank: `970423`
   - VPBank: `970432`

## Architecture

```
mekong vietqr
     │
     ├── (overview)         ── Executive payment telemetry, default account, and volume totals
     ├── generate [AMOUNT]  ── Construct dynamic EMVCo QR string and Napas QuickLink URL
     ├── banks              ── Lookup Napas 247 participant bank BIN codes and short names
     ├── transactions       ── Inspect reconciled bank transfer history
     ├── record <TX_ID>     ── Idempotent payment recording & invoice matching
     └── status             ── Gateway operational status and volume metrics
```

## CLI Usage

```bash
// turbo
mekong vietqr [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong vietqr` | `[--json]` | Overview dashboard with default account, transaction count, and received volume. |
| `mekong vietqr generate` | `[amount] [--memo M] [--bank B] [--account A] [--name N] [--json]` | Generate dynamic EMVCo VietQR payload and QuickLink image URL. |
| `mekong vietqr banks` | `[--json]` | Browse supported Napas 247 banks with BIN codes. |
| `mekong vietqr transactions`| `[--limit N] [--json]` | List incoming bank payment transactions and reconciliation statuses. |
| `mekong vietqr record` | `<tx_id> <amount> [--memo M] [--order O] [--json]` | Record incoming payment with duplicate protection. |
| `mekong vietqr status` | `[--json]` | Telemetry and database records in `.mekong/vietqr.db`. |

## Native MCP Tools

| MCP Tool Name | Arguments | Description |
|---------------|-----------|-------------|
| `mekong_vietqr_generate` | `amount, memo, bank, account_number, account_name` | Generate EMVCo QR code string and Napas QuickLink. |
| `mekong_vietqr_banks` | *(none)* | List supported Napas 247 banks and BIN codes. |
| `mekong_vietqr_transactions`| `limit` | Query recent bank transfer transactions. |
| `mekong_vietqr_record` | `bank_tx_id, amount_vnd, memo, order_id` | Record and reconcile payment transaction idempotently. |
| `mekong_vietqr_status` | *(none)* | Retrieve payment gateway status and volume metrics. |

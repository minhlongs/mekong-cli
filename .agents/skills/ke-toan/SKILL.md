---
name: ke-toan
description: >-
  VAS Vietnamese Accounting Standard engine, TT78/2021 electronic invoices, journal entries, and XML reports.
---

# /ke-toan — Autonomous Vietnamese Accounting Standard (VAS), Circular 78 Electronic Invoices & Journal Entry Engine

Serving as the deterministic regulatory compliance, electronic invoicing, and general ledger engine for solo founders, SMEs, and enterprise agents operating under Vietnamese commercial laws, `mekong ke-toan` manages Circular 78/2021/TT-BTC electronic invoice schemas, balanced double-entry VAS journal entries, and XML tax compliance exports.

## Statutory Regulations & Accounts Embedded

1. **Thông tư 78/2021/TT-BTC & Nghị định 123/2020/NĐ-CP**:
   - Tiêu chuẩn dữ liệu hóa đơn điện tử của Tổng cục Thuế (TCT).
   - Định dạng XML chuẩn: `<HDon>`, `<TTChung>`, `<NDHDon>`, `<NBan>`, `<NMua>`, `<DSHHDVu>`, `<TToan>`.
2. **Hệ Thống Tài Khoản Kế Toán VAS (TT200/2014 & TT133/2016)**:
   - **TK 111**: Tiền mặt (Cash)
   - **TK 112**: Tiền gửi ngân hàng (Bank deposits)
   - **TK 131**: Phải thu của khách hàng (Trade receivables)
   - **TK 1331**: Thuế GTGT được khấu trừ (Deductible VAT)
   - **TK 331**: Phải trả cho người bán (Trade payables)
   - **TK 3331**: Thuế GTGT phải nộp (Output VAT payable)
   - **TK 511**: Doanh thu bán hàng và cung cấp dịch vụ (Revenue)
   - **TK 632**: Giá vốn hàng bán (Cost of Goods Sold)
   - **TK 642**: Chi phí quản lý doanh nghiệp (Administrative expenses)
   - **TK 911**: Xác định kết quả kinh doanh (Income summary)
3. **Double-Entry Bookkeeping Balance Validation**:
   - Bắt buộc kiểm tra tính cân đối `Tổng Nợ (Debit) == Tổng Có (Credit)` trong mọi bút toán ghi sổ.

## Architecture

```
mekong ke-toan
      │
      ├── (overview)             ── Executive accounting telemetry, turnover & ledger status
      ├── create <amount>        ── Create TT78 e-invoice & persist to .mekong/ke_toan.db
      ├── xml <amount>           ── Export General Department of Taxation (TCT) XML schema
      ├── journal <amount>       ── Generate balanced VAS double-entry journal (Nợ 131 / Có 511, Có 3331)
      ├── summary <amount>       ── Text format human-readable invoice summary
      ├── list                   ── Query historical invoices or journal entries
      └── status                 ── System status, ledger turnover, and chart of accounts count
```

## CLI Usage

```bash
// turbo
mekong ke-toan [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong ke-toan` | `[--json]` | Overview dashboard showing invoice count, total revenue, VAT output, and VAS ledger. |
| `mekong ke-toan create` | `<amount> [--vat 0\|5\|8\|10] [--buyer S] [--seller S] [--mst S] [--desc S] [--json]` | Create e-invoice and persist to database. |
| `mekong ke-toan xml` | `<amount> [--vat 0\|5\|8\|10] [--buyer S] [--seller S] [--mst S] [--desc S]` | Output official Circular 78 XML invoice structure. |
| `mekong ke-toan journal` | `<amount> [--vat 0\|5\|8\|10] [--buyer S] [--seller S] [--mst S] [--desc S] [--json]` | Generate balanced VAS double-entry journal entry. |
| `mekong ke-toan summary` | `<amount> [--vat 0\|5\|8\|10] [--buyer S] [--seller S] [--mst S] [--desc S]` | Generate human-readable text invoice summary. |
| `mekong ke-toan status` | `[--json]` | Inspection of accounting engine telemetry and turnover. |
| `mekong ke-toan list` | `[--type invoice\|journal\|all] [--limit N] [--json]` | List historical invoices or journal postings from database. |

## Native MCP Tools Integration

The Accounting engine provides 4 native MCP tools for autonomous finance agents:

1. **`mekong_ke_toan_create(amount: float, buyer: str, vat_rate: int = 10, seller: str = "Doanh Nghiệp", seller_tax_code: str = "0000000000", buyer_tax_code: str = "", description: str = "Hàng hóa/Dịch vụ")`**:
   Create an electronic invoice compliant with Decree 123 & Circular 78 and save to accounting database.

2. **`mekong_ke_toan_xml(amount: float, buyer: str, vat_rate: int = 10, seller: str = "Doanh Nghiệp", seller_tax_code: str = "0000000000", description: str = "Hàng hóa/Dịch vụ")`**:
   Generate electronic invoice XML complying with Circular 78/2021/TT-BTC schema.

3. **`mekong_ke_toan_journal(amount: float, buyer: str, vat_rate: int = 10, seller: str = "Doanh Nghiệp", seller_tax_code: str = "0000000000", description: str = "Hàng hóa/Dịch vụ")`**:
   Generate balanced VAS double-entry journal entry (Nợ 131 / Có 511, Có 3331) for sales revenue.

4. **`mekong_ke_toan_status()`**:
   Retrieve Vietnamese accounting system status, invoice totals, VAT output, and general ledger statistics.

Both FastMCP and pure-Python stdio JSON-RPC 2.0 engines support 100% parity.

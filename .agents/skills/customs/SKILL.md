---
name: customs
description: Customs clearance, VNACCS/VCIS channeling, AHTN 8-digit HS code tariffs, import duty and VAT calculation, and Rules of Origin (C/O) compliance.
---

# /customs — Autonomous Customs Clearance, HS Tariff & Cross-Border Logistics Engine

Autonomous Vietnamese Customs Clearance and Cross-Border Logistics conforming to:
- **Luật Hải quan 2014 (Luật số 54/2014/QH13) & Nghị định 08/2015/NĐ-CP (sửa đổi bởi NĐ 59/2018/NĐ-CP)**.
- **Hệ thống VNACCS/VCIS** (Vietnam Automated Cargo and Port Consolidated System):
  - **Luồng Xanh (Green Channel)**: Miễn kiểm tra hồ sơ và thực tế hàng hóa, thông quan tự động.
  - **Luồng Vàng (Yellow Channel)**: Kiểm tra chi tiết bộ hồ sơ hải quan điện tử (Invoice, Packing List, C/O, B/L).
  - **Luồng Đỏ (Red Channel)**: Kiểm tra chi tiết hồ sơ kết hợp kiểm tra thực tế hàng hóa (máy soi / thủ công).
- **Thông tư 31/2022/TT-BTC**: Danh mục hàng hóa xuất nhập khẩu Việt Nam (AHTN 8 chữ số).
- **Nghị định 31/2018/NĐ-CP**: Quy định chi tiết Luật Quản lý ngoại thương về xuất xứ hàng hóa (C/O Forms: EUR.1, CPTPP, D, E) và tiêu chí RVC (Regional Value Content) >= 40%.

## Architecture

```
mekong customs
     │
     ├── (overview)         ── Customs clearance posture, total duties collected, channel distribution
     ├── hs-lookup          ── Look up 8-digit AHTN HS code, MFN duty, VAT, and FTA preferences
     ├── duty-calc          ── Itemized CIF valuation, import duty, and import VAT calculation
     ├── channel            ── Evaluate VNACCS automated risk criteria (Green / Yellow / Red)
     ├── declare            ── Create & register VNACCS electronic customs declaration
     ├── origin             ── Verify Rules of Origin, RVC percentage, and C/O eligibility
     ├── list               ── Query historical customs declarations
     └── status             ── Customs regulatory telemetry in .mekong/customs.db
```

## CLI Usage

```bash
// turbo
mekong customs [OPTIONS]
```

### Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong customs` | `[--json]` | Overview customs dashboard, declarations, and tax metrics |
| `mekong customs hs-lookup` | `<hs_code> [--fta MFN|EVFTA|CPTPP] [--json]` | Look up 8-digit HS code tariff rates |
| `mekong customs duty-calc` | `<value_usd> [--hs CODE] [--freight F] [--insurance I] [--fta MFN] [--json]` | Calculate import duty and VAT |
| `mekong customs channel` | `<tax_id> <hs_code> <value_usd> [--tier T] [--has-co/--no-co] [--json]` | Evaluate VNACCS Green/Yellow/Red channeling |
| `mekong customs declare` | `<tax_id> <hs_code> <name> <value_usd> [--origin US] [--json]` | Synthesize VNACCS electronic declaration |
| `mekong customs origin` | `<form> <hs_code> <fob_usd> <non_orig_usd> [--json]` | Verify C/O Rules of Origin (RVC >= 40%) |
| `mekong customs list` | `[--limit N] [--json]` | Query registered customs declarations |
| `mekong customs status` | `[--json]` | Customs engine status and database metrics |

## MCP Tools Integration

- `mekong_customs_hs_lookup(hs_code, fta="MFN")`: Look up HS code tariff.
- `mekong_customs_duty_calc(invoice_value_usd, hs_code="8471.30.20", freight_usd=0.0, insurance_usd=0.0, fta="MFN")`: Calculate import duty & VAT.
- `mekong_customs_channel(enterprise_tax_id, hs_code, invoice_value_usd, origin_country="US", compliance_tier="TIER_2_NORMAL", has_valid_co=True)`: Evaluate VNACCS channel.
- `mekong_customs_declare(enterprise_tax_id, hs_code, commodity_name, invoice_value_usd, origin_country="US", declaration_type="IMPORT_BUSINESS")`: Register customs declaration.
- `mekong_customs_origin(form_type, hs_code, fob_value_usd, non_originating_value_usd, exporter_name="", importer_country="DE")`: Verify C/O eligibility.
- `mekong_customs_status()`: Retrieve customs engine status.

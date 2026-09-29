---
name: esg
description: Vietnamese environmental protection, GHG inventory (ISO 14064-1), EU CBAM carbon border adjustment, and carbon credit trading under Law on Environmental Protection 2020.
---

# /esg — Autonomous Environmental, Social & Governance (ESG) & Carbon Trading Compliance Engine

Autonomous Vietnamese Environmental Protection, GHG inventory & Carbon Trading management conforming to:
- **Luật Bảo vệ Môi trường 2020 (Luật số 72/2020/QH14)**:
  - **Điều 91**: Giảm nhẹ phát thải khí nhà kính (GHG mitigation) và bảo vệ tầng ô-dôn.
  - **Điều 93 & 94**: Phát triển và vận hành thị trường carbon trong nước (Domestic Carbon Credit Market) & kết nối quốc tế theo Điều 6 Thỏa thuận Paris.
  - **Điều 39**: Giấy phép môi trường (GPMT - Environmental Permit) bắt buộc.
- **Nghị định 06/2022/NĐ-CP & Quyết định 13/2024/QĐ-TTg**:
  - Danh mục cơ sở phát thải bắt buộc kiểm kê KNK định kỳ 2 năm một lần (ngưỡng ≥ 3,000 tCO2e/năm hoặc ≥ 1,000 TOE/năm).
  - Hệ số phát thải lưới điện quốc gia Việt Nam: 0.7221 tCO2/MWh.
  - Định mức quy đổi: 1 tín chỉ carbon = 1 tấn CO2 tương đương (1 credit = 1 tCO2e).
  - Quy chuẩn MRV (Đo đạc, Báo cáo, Thẩm định) theo chuẩn GHG Protocol / ISO 14064-1 cho Scope 1, Scope 2, Scope 3.
- **Cơ chế Điều chỉnh Biên giới Carbon EU (CBAM - Regulation EU 2023/956)**:
  - Khai báo suất phát thải carbon nhúng (Embedded Emissions) cho sắt thép, nhôm, xi măng, phân bón xuất khẩu sang EU.
- **Tiêu chuẩn công bố thông tin ESG (Thông tư 96/2020/TT-BTC & GRI Standards)**:
  - Báo cáo Phát triển bền vững doanh nghiệp niêm yết (Trụ cột E, S, G và xếp hạng tín nhiệm xanh).

## Architecture

```
mekong esg
     │
     ├── (overview)         ── National ESG dashboard, tracked GHG emissions, carbon trades
     ├── ghg                ── ISO 14064-1 Scope 1, 2, 3 inventory & mandatory MRV threshold check
     ├── cbam               ── EU CBAM embedded emissions & financial certificate liability evaluation
     ├── audit              ── Corporate ESG scoring (E 40%, S 30%, G 30%) and credit rating (AAA-CCC)
     ├── carbon-trade       ── Execute carbon credit trade (BUY/SELL) or emission offset surrender (Điều 93/94)
     ├── list               ── Query registered GHG inventories and carbon transaction ledger
     └── status             ── ESG engine database telemetry in .mekong/esg.db
```

## CLI Usage

```bash
// turbo
mekong esg [OPTIONS]
```

### Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong esg` | `[--json]` | Overview ESG dashboard, tracked emissions, carbon transactions |
| `mekong esg ghg` | `<enterprise> <year> [--diesel L] [--gasoline L] [--coal T] [--electricity kWh] [--json]` | Compute 3-Scope GHG inventory & MRV status |
| `mekong esg cbam` | `<product> <volume_tons> <direct_co2> [--indirect-co2 N] [--carbon-price P] [--json]` | Evaluate EU CBAM embedded emissions and liability |
| `mekong esg audit` | `<enterprise> [--iso-14001] [--renewable %] [--bhxh] [--female-lead %] [--json]` | Compute ESG score and rating grade |
| `mekong esg carbon-trade` | `<project> <credit_type> <quantity> <price_usd> [--action BUY/SELL/OFFSET] [--json]` | Trade or surrender carbon credits |
| `mekong esg list` | `[--limit N] [--json]` | Query GHG inventories and trade ledger |
| `mekong esg status` | `[--json]` | ESG engine status and metrics |

## MCP Tools Integration

- `mekong_esg_ghg(enterprise_name, reporting_year, fuel_diesel_liters=0.0, fuel_gasoline_liters=0.0, coal_tons=0.0, lpg_kg=0.0, electricity_kwh=0.0, scope3_logistics_tco2e=0.0)`: Compute GHG inventory.
- `mekong_esg_cbam(product_type, export_volume_tons, direct_emissions_tco2, indirect_emissions_tco2=0.0, cbam_carbon_price_eur_per_ton=75.0)`: Evaluate EU CBAM liability.
- `mekong_esg_audit(enterprise_name, has_iso_14001=True, renewable_energy_ratio_pct=20.0, has_waste_treatment_license=True, full_social_insurance_compliance=True, workplace_accident_rate=0.0, female_leadership_ratio_pct=30.0, independent_board_members_ratio_pct=33.3, has_anti_corruption_policy=True, has_audited_financial_report=True)`: Compute ESG rating.
- `mekong_esg_carbon_trade(project_name, credit_type, quantity_tco2e, unit_price_usd, action="BUY", counterparty="Sàn giao dịch Carbon Quốc gia")`: Execute carbon credit trade.
- `mekong_esg_list(limit=20)`: List GHG inventories and carbon trades.
- `mekong_esg_status()`: Retrieve ESG engine status and metrics.

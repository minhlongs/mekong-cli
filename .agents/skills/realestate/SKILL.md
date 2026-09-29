---
name: realestate
description: Vietnamese commercial real estate, industrial land leasing, building density compliance (QCVN 01:2021/BXD), and title due diligence under Land Law 2024 & Decree 96/2024/ND-CP.
---

# /realestate — Autonomous Commercial Real Estate, Industrial Land & EPC Leasing Compliance Engine

Autonomous Vietnamese Commercial & Industrial Real Estate management conforming to:
- **Luật Đất đai 2024 (Luật số 31/2024/QH15)**:
  - **Điều 33 & 34**: Phân định quyền và nghĩa vụ giữa hình thức trả tiền thuê đất hàng năm (`ANNUAL_RENT`) và trả tiền một lần cho cả thời gian thuê (`LUMP_SUM_RENT`).
  - **Điều 159**: Bảng giá đất theo nguyên tắc thị trường, xóa bỏ khung giá đất cũ.
  - **Điều 202**: Quản lý quỹ đất khu công nghiệp, cụm công nghiệp, khu công nghệ cao (thời hạn thuê ≤ 50 năm, tối đa 70 năm).
- **Luật Kinh doanh Bất động sản 2023 (Luật số 29/2023/QH15)**:
  - **Điều 14**: Điều kiện đưa bất động sản vào kinh doanh (Giấy chứng nhận QSDĐ, không tranh chấp, không kê biên).
  - **Điều 23.5**: Tiền đặt cọc trong kinh doanh bất động sản.
  - **Nghị định 96/2024/NĐ-CP**: Mẫu hợp đồng chuẩn hóa cho thuê văn phòng thương mại, nhà xưởng xây sẵn (RBF), đất KCN và nhà xưởng Built-To-Suit (BTS/EPC).
- **Quy chuẩn Kỹ thuật Quốc gia về Quy hoạch Xây dựng (QCVN 01:2021/BXD)**:
  - Mật độ xây dựng thuần lô đất công nghiệp: tối đa 70% đối với công trình cao ≤ 40m.
  - Tỷ lệ diện tích đất cây xanh tối thiểu: ≥ 10% trong khuôn viên dự án KCN.
  - Tiêu chuẩn thẩm duyệt PCCC (Nghị định 50/2024/NĐ-CP) và đấu nối xả thải (QCVN 40:2011/BTNMT).

## Architecture

```
mekong realestate
     │
     ├── (overview)         ── Commercial real estate dashboard, portfolio area, active leases
     ├── finance            ── Multi-year cash flow schedule, deposit calculation, escalation rate
     ├── density            ── Building footprint density (≤70%) & green space (≥10%) QCVN 01:2021
     ├── audit              ── Legal title due diligence, construction readiness & leasing permits
     ├── draft              ── Synthesize statutory lease agreement under Decree 96/2024/ND-CP
     ├── list               ── Query registered properties and industrial parks
     └── status             ── Real estate engine database telemetry in .mekong/realestate.db
```

## CLI Usage

```bash
// turbo
mekong realestate [OPTIONS]
```

### Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong realestate` | `[--json]` | Overview real estate dashboard, managed area, active contracts |
| `mekong realestate finance` | `<cat> <area> <unit_rent> [--months M] [--mgmt fee] [--deposit-months D] [--json]` | Compute lease cash flows, deposit, and total contract value |
| `mekong realestate density` | `<lot_area> <footprint> <green_area> [--height-tier T] [--json]` | Validate building density and green ratio under QCVN 01:2021/BXD |
| `mekong realestate audit` | `<name> <cat> <area> [--land-cert] [--permit] [--fire-safety] [--json]` | Legal title and leasing due diligence |
| `mekong realestate draft` | `<prop_id> <lessor> <lessee> <area> <unit_rent> [--months M] [--json]` | Draft statutory lease contract under Decree 96/2024/ND-CP |
| `mekong realestate list` | `[--category C] [--limit N] [--json]` | Query registered real estate properties |
| `mekong realestate status` | `[--json]` | Real estate engine status and metrics |

## MCP Tools Integration

- `mekong_realestate_finance(category, area_sqm, unit_rent_usd, lease_term_months=36, maintenance_fee_usd=0.5, deposit_months=3, annual_escalation_pct=3.0)`: Calculate leasing cash flows.
- `mekong_realestate_density(lot_area_sqm, building_footprint_sqm, green_space_sqm, building_height_tier="UP_TO_20M")`: Verify building density compliance.
- `mekong_realestate_audit(project_name, category, land_area_sqm, has_land_cert=True, has_construction_permit=True, has_fire_safety_cert=True, tenure_remaining_years=35.0, payment_term="ANNUAL_RENT", has_disputes=False, is_mortgaged_to_bank=False)`: Audit legal title and condition for lease.
- `mekong_realestate_draft(property_id, lessor_name, lessee_name, leased_area_sqm, unit_rent_usd, lease_term_months=36, maintenance_fee_usd=0.5, deposit_months=3, dispute_resolution="VIAC")`: Generate statutory lease contract.
- `mekong_realestate_list(category="ALL", limit=20)`: List registered properties.
- `mekong_realestate_status()`: Retrieve real estate engine status and metrics.

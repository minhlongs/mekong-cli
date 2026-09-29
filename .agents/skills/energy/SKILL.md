---
name: energy
description: Vietnamese Renewable Energy, Rooftop Solar (ĐMTMN), DPPA mechanisms & EV charging infrastructure.
---

# Vietnamese Renewable Energy & DPPA Power Market Engine (`mekong energy`)

Autonomous management engine for the Vietnamese Electricity Law 2024, Rooftop Solar PV Self-Consumption policies (Decree 135/2024/ND-CP), Direct Power Purchase Agreement (DPPA) mechanisms between renewable generators and large consumers (Decree 80/2024/ND-CP), and Smart EV Charging Station infrastructure (TCVN 13078 / IEC 61851 & TOU Tariffs).

## Core Capabilities

1. **Rooftop Solar PV Sizing & Self-Consumption Permitting (Decree 135/2024/ND-CP)**:
   - Evaluates system sizing based on regional solar irradiance (PSH): North (3.8), Central (4.6), South (5.1), Highlands (4.9), South Central (5.4).
   - Enforces the statutory 20% grid export surplus cap under Decree 135/2024.
   - Determines statutory permitting tier:
     - Tier 1: $\le 100$ kWp (License exempt, free self-consumption).
     - Tier 2: $100$ kWp to $1,000$ kWp (Notification to Department of Industry & Trade and EVN).
     - Tier 3: $> 1,000$ kWp (Mandatory ERAV electricity operating license).
   - Computes annual clean energy generation and carbon displacement (0.7221 tCO2/MWh).
2. **Direct Power Purchase Agreement (DPPA) & CfD Settlement (Decree 80/2024/ND-CP)**:
   - Validates statutory eligibility for large consumers ($\ge 200,000$ kWh/month for national grid DPPA).
   - Evaluates Private Line bilateral contracts vs National Grid wholesale electricity market (VWEM) contracts.
   - Calculates Contract-for-Differences (CfD) financial settlement between Strike Price and Spot Market Price.
3. **EV Charging Station Infrastructure & Time-of-Use (TOU) Smart Tariffs**:
   - Supports AC slow/medium chargers (7.4 kW, 22 kW Type 2) and DC fast superchargers (60 kW, 120 kW, 180 kW CCS2).
   - Calculates Time-of-Use (TOU) electricity costs across Off-peak, Normal, and Peak hours.
   - Computes charging session duration, service fees, and CO2 emissions saved.
   - Persistent SQLite WAL storage at `.mekong/energy.db`.

## CLI Usage

```bash
# System overview and renewable energy telemetry
mekong energy
mekong energy status --json

# Calculate rooftop solar sizing and Decree 135 permitting tier
mekong energy solar "ĐMT Nhà máy Bình Dương" "Công ty TNHH Sản xuất May Mặc" "SOUTH" 850 6500 --self-pct 85 --json
mekong energy solar "ĐMT Văn phòng Hà Nội" "Tập đoàn Công nghệ Hà Nội" "NORTH" 80 800 --self-pct 90 --json

# Evaluate DPPA contract and CfD settlement (Decree 80/2024/ND-CP)
mekong energy dppa "Trang trại Điện mặt trời Ninh Thuận" "Tập đoàn Thép Hòa Phát" "NATIONAL_GRID" 50 3500000 --strike-price 1850 --market-price 1720 --json
mekong energy dppa "Nhà máy Điện gió Cà Mau" "Khu công nghiệp Sóng Thần" "PRIVATE_LINE" 15 800000 --strike-price 1900 --json

# Calculate EV fast charging session billing & carbon savings
mekong energy ev "STATION-HCM-01" "DC_120KW" 55.5 --tou "PEAK" --service-fee 800 --json
mekong energy ev "STATION-DANANG-02" "DC_60KW" 42.0 --tou "OFF_PEAK" --json

# List solar projects or DPPA contracts
mekong energy list --type solar --region SOUTH --json
mekong energy list --type dppa --json
```

## Native MCP Tools

- `mekong_energy_solar`: Size rooftop solar PV system, compute generation, and evaluate Decree 135/2024 permitting tier.
- `mekong_energy_dppa`: Evaluate DPPA contract eligibility and CfD financial settlement under Decree 80/2024/ND-CP.
- `mekong_energy_ev`: Calculate EV charging session costs, TOU electricity rates, charging time, and CO2 displaced.
- `mekong_energy_list`: Query registered solar PV installations and direct power purchase agreements.
- `mekong_energy_status`: Retrieve renewable energy portfolio metrics, solar capacity, DPPA volume, and EV charging telemetry.

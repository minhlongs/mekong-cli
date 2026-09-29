---
name: maritime
description: Vietnamese Maritime Code 2015, seaport terminal operations, ICD container management & customs e-Manifest.
---

# Vietnamese Maritime Logistics & Port Terminal Engine (`mekong maritime`)

Autonomous management engine for the Vietnamese Maritime Code 2015 (Law No. 95/2015/QH13), Seaport Berthing & Navigation management (Decree 58/2017/ND-CP), Inland Container Depot (ICD Cảng cạn) operations (Decree 38/2017/ND-CP), Port Tariffs, Pilotage & Stevedoring (LoLo) calculations (Circular 39/2023/TT-BGTVT), and Electronic Sea Cargo Customs Manifest (VNACCS/VCIS e-Manifest & e-EIR).

## Core Capabilities

1. **Commercial Vessel Call & Berthing Allocation (Decree 58/2017/ND-CP)**:
   - Schedules and logs vessel arrivals and departures across Vietnam's 5 Seaport Groups:
     - Group 1: Northern Seaports (Hải Phòng, Lạch Huyện nước sâu, Quảng Ninh, Cái Lân).
     - Group 2: North Central Seaports (Nghi Sơn, Cửa Lò, Vũng Áng).
     - Group 3: Central Seaports (Đà Nẵng, Tiên Sa, Dung Quất, Quy Nhơn).
     - Group 4: Southeastern Seaports (Cát Lái TP.HCM, Cái Mép - Thị Vải nước sâu, Hiệp Phước, Đồng Nai).
     - Group 5: Mekong Delta Seaports (Cần Thơ, Cái Cui, Phú Quốc).
   - Validates draft requirements, deep-water channel eligibility, and navigation advisories.
2. **Container Yard & Inland Container Depot (ICD) Management (Decree 38/2017/ND-CP)**:
   - Allocates 3D container yard slots (Bay-Row-Tier).
   - Tracks standard container types: `20GP`, `40GP`, `40HC`, `20RF` (Reefer), `40RF` (Reefer).
   - Enforces Verified Gross Mass (VGM - SOLAS Convention Chapter VI Regulation 2) payload verification.
   - Monitors temperature-controlled reefer power status and IMO dangerous goods segregation.
3. **Statutory Port Tariffs & Stevedoring (LoLo) Calculation (Circular 39/2023/TT-BGTVT)**:
   - Calculates berth dues: $GRT \times \text{hours} \times \text{statutory rate}$.
   - Calculates maritime pilotage dues: $GRT \times \text{nautical miles} \times \text{statutory rate}$.
   - Computes container lift-on/lift-off (LoLo) stevedoring fees across loaded vs empty 20ft and 40ft units.
   - Computes reefer power and monitoring surcharges with real-time VND currency conversion.
4. **Electronic Sea Cargo Customs Manifest (VNACCS/VCIS e-Manifest)**:
   - Formats and records electronic manifests for National Single Window (Cổng thông tin Một cửa Quốc gia).
   - Links Bill of Lading (B/L), shipper, consignee, container count, and gross weight.
   - Persistent SQLite WAL storage at `.mekong/maritime.db`.

## CLI Usage

```bash
# System overview and maritime operations telemetry
mekong maritime
mekong maritime status --json

# Register commercial vessel call and berthing reservation
mekong maritime vessel "EVER GIVEN" "IMO9811000" "Panama" 199320 219079 399.9 16.0 "VNVUT" "Cảng Quốc tế Cái Mép (CMIT)" "2026-10-01 08:00" "2026-10-02 20:00" --json

# Register container in terminal yard or ICD depot
mekong maritime container "MSCU1234567" "40HC" 28500 "VN-SEAL-8899" "BL-MSK-20260901" --slot "YARD-B02-R05-T3" --json
mekong maritime container "ONEU9876543" "40RF" 26000 "VN-SEAL-9900" "BL-ONE-20260902" --reefer --slot "YARD-REEFER-01" --json

# Calculate statutory port tariffs and stevedoring charges (Circular 39/2023/TT-BGTVT)
mekong maritime tariff "CALL-001" "GROUP_4" 45000 24 --f20 200 --f40 350 --e20 50 --e40 30 --reefer-cnt 25 --reefer-hrs 24 --json

# Declare electronic customs manifest (VNACCS e-Manifest)
mekong maritime manifest "CALL-001" "MSK-VN-2026-001" "Doanh nghiệp May XK Việt Nam" "Hamburg Trading GmbH" "Hàng may mặc xuất khẩu" 15 285000 --json

# List active vessel calls or yard containers
mekong maritime list --type vessels --json
mekong maritime list --type containers --json
```

## Native MCP Tools

- `mekong_maritime_vessel`: Register commercial vessel call, schedule berthing, and audit channel draft requirements.
- `mekong_maritime_container`: Record container inventory, 3D yard slot location, and SOLAS VGM gross mass compliance.
- `mekong_maritime_tariff`: Compute statutory berth dues, pilotage fees, and container LoLo stevedoring tariffs (Circular 39/2023).
- `mekong_maritime_manifest`: Submit electronic sea cargo e-Manifest to VNACCS / National Single Window.
- `mekong_maritime_list`: Query scheduled vessel calls or container inventory in terminal yards and ICD depots.
- `mekong_maritime_status`: Retrieve Vietnamese maritime logistics, vessel schedule, and terminal yard metrics.

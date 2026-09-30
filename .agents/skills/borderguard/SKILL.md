---
name: borderguard
description: Vietnamese National Border, Territorial Sovereignty & Border Guard Defense Suite (Luật Biên phòng Việt Nam 2020 & Nghị định 34/2014/NĐ-CP).
---

# Border Guard & Territorial Sovereignty Suite (`mekong borderguard`)

Vietnamese National Border, Territorial Sovereignty & Border Guard Defense Suite governed by:
- **Law on Vietnam Border Defense 2020** (Law No. 66/2020/QH14)
- **Law on National Border 2003** (Law No. 06/2003/QH11)
- **Decree No. 34/2014/NĐ-CP** (Regime of Land Border Areas of the Socialist Republic of Vietnam)
- **Decree No. 106/2021/NĐ-CP** (Implementation Guidelines for Law on Vietnam Border Defense)
- **Circular No. 163/2021/TT-BQP** (Border Management and Protection Guidelines)

## Capabilities & Workflows

1. **National Border Markers & Landmarks (`mekong borderguard marker`)**:
   - Register and inspect border markers across 3 primary border segments: Vietnam-Laos, Vietnam-Cambodia, Vietnam-China.
   - Track coordinates, elevation, managing border posts (Đồn Biên phòng), and physical integrity status.
2. **Border Belt & Restricted Area Passes (`mekong borderguard permit`)**:
   - Issue official entry permits to border belts and restricted border areas under Decree 34/2014/NĐ-CP.
   - Enforce identification verification, validity periods, and nationality controls.
3. **Patrol & Reconnaissance Missions (`mekong borderguard patrol`)**:
   - Log routine foot patrols, motorized recon, joint bilateral patrols with foreign border guards, riverine sorties, and UAV aerial surveillance.
   - Automatically update inspection timestamps on all markers covered along the patrol route.
4. **Border Gate & Port of Entry Oversight (`mekong borderguard gate`)**:
   - Register and monitor international, bilateral main, sub-border gates, and border crossing points.
   - Track daily transit capacity, operational status, and controlling border stations.
5. **Border Incidents & Interdiction (`mekong borderguard incident`)**:
   - Report and investigate unauthorized border crossings, smuggling/narcotics, boundary line encroachment, armed transgressions, and disputed zone activities.
   - Track contraband seizures in VND and bilateral flag-level diplomatic talks.

## CLI Reference

```bash
# Executive Dashboard & Metrics
mekong borderguard
mekong borderguard --json
mekong borderguard status [--json]

# Register Border Marker
mekong borderguard marker \
  --id "BM-VN-LA-450" \
  --number "450" \
  --segment "VIETNAM_LAOS" \
  --post "Đồn Biên phòng Cửa khẩu Quốc tế Cầu Treo" \
  --province "Hà Tĩnh" \
  --lat 18.3892 \
  --lon 105.1873 \
  --type "MAIN_MONUMENT_GRANITE" \
  --elev 720.0 \
  --integrity "INTACT" \
  --json

# Issue Border Belt Pass
mekong borderguard permit \
  --id "PERMIT-2026-001" \
  --name "Nguyễn Văn Tuấn" \
  --id-doc "038090001234" \
  --zone "BORDER_BELT" \
  --purpose "Khảo sát thi công công trình đường tuần tra biên giới" \
  --post "Đồn Biên phòng Cửa khẩu Quốc tế Cầu Treo" \
  --from "2026-04-01" \
  --until "2026-04-30" \
  --json

# Log Patrol Mission
mekong borderguard patrol \
  --id "PATROL-2026-001" \
  --type "JOINT_BILATERAL_PATROL" \
  --post "Đồn Biên phòng Cửa khẩu Quốc tế Cầu Treo" \
  --leader "Trung tá Lê Quang Đạo" \
  --notes "Tuần tra song phương chung với Đại đội Biên phòng 253 Quân đội Lào, đoạn mốc 448 đến 452" \
  --team 8 \
  --markers "BM-VN-LA-450" \
  --duration 6.5 \
  --infringements 0 \
  --json

# Register Border Gate
mekong borderguard gate \
  --id "GATE-CAU-TREO" \
  --name "Cửa khẩu Quốc tế Cầu Treo" \
  --tier "INTERNATIONAL" \
  --country "LAOS" \
  --station "Trạm Kiểm soát Biên phòng Cầu Treo" \
  --capacity 2500 \
  --status "NORMAL_OPERATION" \
  --json

# Report Border Incident / Contraband Interdiction
mekong borderguard incident \
  --id "INC-BG-2026-001" \
  --type "SMUGGLING_CONTRABAND" \
  --severity "MAJOR" \
  --location "Khu vực đường mòn cánh gà gần mốc 450" \
  --post "Đồn Biên phòng Cửa khẩu Quốc tế Cầu Treo" \
  --persons 2 \
  --contraband 4500000000 \
  --talks \
  --status "CRIMINAL_CHARGES" \
  --json

# Query Records
mekong borderguard list --type all --limit 20 --json
```

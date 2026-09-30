---
name: civildefense
description: Vietnamese Civil Defense, Disaster Mitigation & National Emergency Response Suite (Luật Phòng thủ dân sự 2023 & Nghị định 02/2024/NĐ-CP).
---

# Civil Defense & Emergency Response Suite (`mekong civildefense`)

Vietnamese Civil Defense, Disaster Mitigation & National Emergency Response Suite governed by:
- **Law on Civil Defense 2023** (Law No. 18/2023/QH15, effective July 1, 2024)
- **Decree No. 02/2024/NĐ-CP** (Implementation Guidelines for Law on Civil Defense)
- **Prime Minister Decisions on National Civil Defense Strategy to 2030**
- **Decree No. 30/2017/NĐ-CP** (Incident, Disaster Response & Search and Rescue)

## Capabilities & Workflows

1. **Civil Defense Readiness Plans (`mekong civildefense plan`)**:
   - Register and manage civil defense plans across disaster categories: `WAR_CONFLICT`, `NUCLEAR_RADIATION`, `CHEMICAL_TOXIC`, `BIOLOGICAL_PANDEMIC`, and `CATACLYSMIC_GEOHAZARD`.
   - Track jurisdiction scope, commanding bodies, evacuation population capacity, and essential supplies reserves (Article 13).
2. **Emergency Alert Levels (`mekong civildefense alert`)**:
   - Declare, escalate, or deactivate civil defense emergency levels under Article 20 of Law 18/2023/QH15:
     - `LEVEL_1_DISTRICT`: District-level emergency.
     - `LEVEL_2_PROVINCIAL`: Multi-district / provincial emergency.
     - `LEVEL_3_REGIONAL`: Multi-provincial regional catastrophe.
     - `LEVEL_4_NATIONAL`: National disaster / State of Emergency.
   - Issue mandatory evacuation orders and immediate response directives.
3. **Shelters & Underground Hardened Fortifications (`mekong civildefense shelter`)**:
   - Register and inspect civil defense bunkers, specialized underground fortifications, dual-use subway basements, and public storm shelters (Article 27).
   - Track shelter capacity, air filtration/ventilation readiness, and CBRN protection ratings.
4. **Mobilized Forces & Core Units (`mekong civildefense force`)**:
   - Mobilize and deploy specialized military core units, police fire & rescue squads, militia self-defense teams, community shock forces, and chemical/engineer corps (Article 35).
   - Monitor mobilization readiness hours and specialized vehicles.
5. **Emergency Drills & Preparedness Exercises (`mekong civildefense drill`)**:
   - Log tabletop command-and-staff drills, field evacuation exercises, CBRN hazmat response sorties, and combined full-scale defense drills (Article 18).
   - Record quantitative evaluation scores and lessons learned.

## CLI Reference

```bash
# Executive Dashboard & Metrics
mekong civildefense
mekong civildefense --json
mekong civildefense status [--json]

# Register Civil Defense Plan
mekong civildefense plan \
  --id "PLAN-CD-HN-2026" \
  --name "Kế hoạch Phòng thủ Dân sự Ứng phó Thảm họa Hóa chất Đô thị" \
  --category "CHEMICAL_TOXIC" \
  --scope "Thành phố Hà Nội" \
  --body "UBND Thành phố Hà Nội" \
  --capacity 50000 \
  --supplies 30 \
  --json

# Issue Civil Defense Alert Level
mekong civildefense alert \
  --id "ALERT-CD-2026-001" \
  --category "CATACLYSMIC_GEOHAZARD" \
  --level "LEVEL_2_PROVINCIAL" \
  --region "Khu vực sạt lở thượng nguồn sông Đà, tỉnh Lai Châu" \
  --authority "Chủ tịch UBND Tỉnh Lai Châu" \
  --evacuation \
  --actions "Khẩn cấp sơ tán 1.200 hộ dân vùng nguy hiểm, huy động công binh cứu nạn" \
  --json

# Register Underground Shelter
mekong civildefense shelter \
  --id "SHELTER-HN-001" \
  --name "Hầm Trú ẩn Phòng thủ Dân sự Ga Metro Ngầm Cát Linh" \
  --type "DUAL_USE_SUBWAY_BASEMENT" \
  --address "Ga Cát Linh, Quận Đống Đa, Hà Nội" \
  --capacity 5000 \
  --filtration \
  --cbrn "LEVEL_2_HIGH" \
  --json

# Mobilize Response Force
mekong civildefense force \
  --id "FORCE-HN-01" \
  --unit "Tiểu đoàn Phòng hóa 78, Bộ Tư lệnh Hóa học" \
  --type "SPECIALIZED_ENGINEER_CORPS" \
  --base "Sơn Tây, Hà Nội" \
  --personnel 120 \
  --vehicles 18 \
  --readiness 0.5 \
  --officer "Thượng tá Nguyễn Hữu Dũng" \
  --json

# Log Emergency Drill
mekong civildefense drill \
  --id "DRILL-2026-01" \
  --code "PTDS-HN-26" \
  --name "Diễn tập Thực binh Phòng thủ Dân sự Ứng phó Sự cố Phóng xạ Đô thị" \
  --type "HAZMAT_CBRN_DRILL" \
  --agency "Bộ Tư lệnh Thủ đô Hà Nội" \
  --participants 650 \
  --duration 12.0 \
  --score 92.5 \
  --notes "Hoàn thành tốt tiêu tẩy thực địa và kiểm soát ô nhiễm" \
  --json

# List Records
mekong civildefense list --type all --limit 50 --json
mekong civildefense list --type shelters --json
```

## Dual MCP Integration

| Tool Name | Operation | FastMCP & JSON-RPC |
|-----------|-----------|--------------------|
| `mekong_civildefense_plan` | Register/update civil defense plan | Yes |
| `mekong_civildefense_alert` | Declare/escalate emergency alert level | Yes |
| `mekong_civildefense_shelter` | Register/inspect shelter or bunker | Yes |
| `mekong_civildefense_force` | Mobilize/deploy response unit | Yes |
| `mekong_civildefense_drill` | Record civil defense drill/exercise | Yes |
| `mekong_civildefense_list` | Query civil defense records | Yes |
| `mekong_civildefense_status` | Retrieve civil defense telemetry | Yes |

---
name: traffic
description: Vietnamese Road Traffic Safety, Demerit Points & Law Enforcement Suite (Luật Trật tự, an toàn giao thông đường bộ 2024 & Luật Đường bộ 2024).
---

# Road Traffic Safety, Demerit Points & Law Enforcement Suite (`mekong traffic`)

Vietnamese Road Traffic Safety, Demerit Points & Law Enforcement Suite governed by:
- **Law on Road Traffic Safety and Order 2024** (Law No. 36/2024/QH15 — Luật Trật tự, an toàn giao thông đường bộ 2024)
- **Road Law 2024** (Law No. 35/2024/QH15 — Luật Đường bộ 2024)
- **Decree No. 100/2019/NĐ-CP & Decree No. 123/2021/NĐ-CP** (Administrative Penalties in Road Traffic)
- **Circular No. 32/2023/TT-BCA** (Traffic Police Patrol, Control & Enforcement Procedures)
- **Circular No. 24/2023/TT-BCA** (Vehicle Registration & Identification Plate Regulations / Biển số định danh)

## Capabilities & Workflows

1. **Driver License & 12 Demerit Points System (`mekong traffic license`)**:
   - Manage driver licenses across statutory classes: `A1`, `A`, `B1`, `B`, `C1`, `C`, `D1`, `D2`, `D`, `BE`, `CE`, `DE` under Law 36/2024.
   - Enforce the statutory 12-points system (Article 58): points deduction upon violations, automatic suspension when points reach 0, and annual restoration.
2. **Traffic Police Citations & Penalties (`mekong traffic ticket`)**:
   - Issue statutory traffic violation citations, calculate administrative fines in VND, deduct demerit points, and record officer badge numbers (Article 65).
3. **Automated AI Camera Ticketing (`mekong traffic camera`)**:
   - Process automated AI camera detection notices (Phạt nguội) for speeding, red-light running, wrong lane usage, wrong-way driving, and illegal stopping (Article 72 & 73).
   - Track statutory 20-day notice and response periods.
4. **Motor Vehicle Roadworthiness & Emissions Inspection (`mekong traffic inspection`)**:
   - Record periodic motor vehicle safety and emissions inspections under Article 42.
   - Verify brake efficiency percentages ($\ge 65\%$), Euro 4/5/6 emissions compliance, and digital inspection certificate validity.
5. **Traffic Police Patrol Stops & Sobriety Screening (`mekong traffic stop`)**:
   - Log roadside stops and mandatory breathalyzer alcohol testing (strict zero-tolerance under Article 8.1) and rapid drug screening (opiates, meth, THC).
   - Record enforcement actions: cleared, ticketed, or vehicle impounded.

## CLI Reference

```bash
# Executive Dashboard & Metrics
mekong traffic
mekong traffic --json
mekong traffic status [--json]

# Register Driver License (12 Points)
mekong traffic license \
  --number "790123456789" \
  --name "Nguyễn Văn Tuấn" \
  --citizen-id "001095012345" \
  --class "B" \
  --points 12 \
  --json

# Issue Traffic Violation Ticket (Points Deduction)
mekong traffic ticket \
  --id "TCK-2026-0001" \
  --license "790123456789" \
  --plate "30A-998.88" \
  --code "D100-D5-D3" \
  --desc "Điều khiển xe chạy quá tốc độ quy định từ 10 km/h đến 20 km/h" \
  --fine 4000000 \
  --points 2 \
  --location "Km 18+300 Cao tốc Pháp Vân - Cầu Giẽ" \
  --officer "CSGT-88992" \
  --json

# Record Automated AI Camera Notice (Phạt nguội)
mekong traffic camera \
  --id "CAM-2026-0001" \
  --plate "51F-123.45" \
  --type "SPEEDING_OVER_LIMIT" \
  --location "Km 25+100 Cao tốc TP.HCM - Long Thành - Dầu Giây" \
  --value "132 km/h / 100 km/h" \
  --json

# Record Motor Vehicle Inspection
mekong traffic inspection \
  --id "INSP-DK-2026-01" \
  --plate "30A-998.88" \
  --vin "RL4H2928374928" \
  --type "PASSENGER_CAR" \
  --center "TTDK-2903D" \
  --brake 72.5 \
  --emissions "EURO_5" \
  --result "PASSED" \
  --json

# Log Roadside Stop & Sobriety Screening
mekong traffic stop \
  --id "STOP-2026-0001" \
  --plate "29B-123.99" \
  --reason "ROUTINE_ALCOHOL_CHECK" \
  --unit "Đội CSGT Số 6, Phòng CSGT Công an TP Hà Nội" \
  --alcohol 0.0 \
  --drug "NEGATIVE" \
  --action "CLEARED_NO_VIOLATION" \
  --json

# List Records
mekong traffic list --type all [--limit 50] [--json]
mekong traffic list --type licenses [--json]
mekong traffic list --type tickets [--json]
mekong traffic list --type camera [--json]
mekong traffic list --type inspections [--json]
mekong traffic list --type stops [--json]
```

## Native MCP Tools Reference

- `mekong_traffic_license`: Register a driver license and initialize 12 statutory points under Article 58 Law 36/2024/QH15.
- `mekong_traffic_ticket`: Issue a traffic citation, calculate fine amount, and deduct driver license points.
- `mekong_traffic_camera`: Record an automated AI camera traffic violation notice (phạt nguội) under Article 72.
- `mekong_traffic_inspection`: Record periodic motor vehicle safety and emissions inspection under Article 42.
- `mekong_traffic_stop`: Log a traffic police road stop, alcohol breathalyzer check, and drug screening.
- `mekong_traffic_list`: List driver licenses, citations, camera notices, vehicle inspections, and road stops.
- `mekong_traffic_status`: Aggregate telemetry metrics on driver points, citations, camera ticketing, and sobriety checks.

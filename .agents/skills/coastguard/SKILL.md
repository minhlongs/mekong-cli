---
name: coastguard
description: Vietnamese Coast Guard & Maritime Law Enforcement Suite (Luật Cảnh sát biển Việt Nam 2018 & Nghị định 61/2019/NĐ-CP).
---

# Coast Guard & Maritime Law Enforcement Suite (`mekong coastguard`)

Vietnamese Coast Guard & Maritime Law Enforcement Suite governed by:
- **Law on Vietnam Coast Guard 2018** (Law No. 33/2018/QH14)
- **Decree No. 61/2019/NĐ-CP** (Guiding the Implementation of Law on Vietnam Coast Guard)
- **Circular No. 15/2019/TT-BQP** (Coast Guard Operating Regulations, Patrol & Maritime Enforcement Procedures)
- **Decree No. 42/2019/NĐ-CP** (Administrative Sanctions in Fisheries, Anti-IUU Crackdown)
- **Decree No. 02/2021/NĐ-CP** (Flag, Badges, Emblems & Uniforms of Vietnam Coast Guard)

## Capabilities & Workflows

1. **Coast Guard Fleet & Cutter Registry (`mekong coastguard vessel`)**:
   - Register and manage Coast Guard patrol cutters, offshore patrol vessels (OPV DN-2000), fast patrol boats (TT-400/TT-200), rescue tugs, and special recon ships across 4 Coast Guard Regions (Vùng 1, 2, 3, 4).
   - Track displacement tonnage, home port bases, and mission-readiness statuses.
2. **Maritime Sovereignty Patrols (`mekong coastguard patrol`)**:
   - Log EEZ surveillance sorties, continental shelf patrols, Truong Sa/Hoang Sa sovereignty protection missions, and bilateral joint patrols with neighboring coast guards (China/Gulf of Tonkin, Cambodia, Indonesia, Philippines).
   - Record days at sea, nautical miles, and operational commands (Article 11).
3. **Maritime Boarding & Interdiction (`mekong coastguard inspect`)**:
   - Record law enforcement boardings, search and seizure at sea (Article 13).
   - Track routine checks, contraband smuggling (oil/diesel, minerals, narcotics), ship-to-ship (STS) illegal transfers, foreign vessel encroachments, and environmental violations.
   - Enforce statutory administrative fines in VND.
4. **Anti-IUU Fishing Crackdown (`mekong coastguard iuu`)**:
   - Combat Illegal, Unreported, and Unregulated (IUU) fishing to resolve European Commission (EC) Yellow Card sanctions.
   - Sanction VMS (Vessel Monitoring System) disconnections, border crossings into foreign maritime jurisdictions, "3-No" fishing boats, and prohibited fishing gear under Decree 42/2019/NĐ-CP.
   - Execute vessel impoundments and captain license revocations.
5. **Search and Rescue at Sea (`mekong coastguard sar`)**:
   - Coordinate and log maritime distress responses, vessel towing, medical evacuations at sea, shipwreck rescues, and typhoon escort operations (Article 8).
   - Track survivor counts and salvaging outcomes.

## CLI Reference

```bash
# Executive Dashboard & Metrics
mekong coastguard
mekong coastguard --json
mekong coastguard status [--json]

# Register Coast Guard Vessel
mekong coastguard vessel \
  --id "CSB-8002" \
  --hull "8002" \
  --class "OFFSHORE_PATROL_VESSEL_OPV" \
  --region "REGION_2_CENTRAL" \
  --port "Hải đoàn 21, Kỳ Hà, Quảng Nam" \
  --displacement 2400.0 \
  --year 2015 \
  --status "ACTIVE_MISSION_READY" \
  --json

# Log Maritime Sovereignty Patrol
mekong coastguard patrol \
  --id "PATROL-CSB-2026-01" \
  --vessel "CSB-8002" \
  --type "SOVEREIGNTY_PROTECTION_SORTIE" \
  --scope "Vùng biển Hoàng Sa và quần đảo Trường Sa" \
  --commander "Thượng tá Nguyễn Văn A" \
  --days 25 \
  --miles 3200.0 \
  --json

# Record Maritime Boarding & Inspection
mekong coastguard inspect \
  --id "INSP-CSB-2026-001" \
  --target "Tàu Dầu Hải Phòng 09" \
  --reg "HP-4589" \
  --reason "STS_ILLEGAL_TRANSFER" \
  --coords "09°45'N 107°12'E" \
  --by "CSB-8002" \
  --violations \
  --fine 150000000 \
  --contraband "Tạm giữ 350.000 lít dầu DO không rõ nguồn gốc" \
  --json

# Report IUU Fishing Violation
mekong coastguard iuu \
  --id "IUU-2026-001" \
  --vessel "BV-92837-TS" \
  --owner "Huỳnh Văn B" \
  --province "Bà Rịa - Vũng Tàu" \
  --violation "VMS_DISCONNECTION" \
  --authority "Bộ Tư lệnh Vùng Cảnh sát biển 3" \
  --penalty 25000000 \
  --revoke-license \
  --json

# Log Maritime Search & Rescue (SAR)
mekong coastguard sar \
  --id "SAR-2026-01" \
  --name "Cứu nạn 12 ngư dân tàu cá BĐ-97123-TS chìm tại Trường Sa" \
  --type "SHIPWRECK_SINKING_RESCUE" \
  --location "Khu vực đảo Song Tử Tây" \
  --target "BĐ-97123-TS" \
  --by "CSB-8002" \
  --rescued 12 \
  --salvaged \
  --json

# List Records
mekong coastguard list --type all --limit 50 --json
mekong coastguard list --type vessels --json
```

## Dual MCP Integration

| Tool Name | Operation | FastMCP & JSON-RPC |
|-----------|-----------|--------------------|
| `mekong_coastguard_vessel` | Register/inspect Coast Guard ship | Yes |
| `mekong_coastguard_patrol` | Log maritime patrol sortie | Yes |
| `mekong_coastguard_inspect` | Record boarding inspection | Yes |
| `mekong_coastguard_iuu` | Log IUU fishing crackdown/penalty | Yes |
| `mekong_coastguard_sar` | Log maritime search & rescue | Yes |
| `mekong_coastguard_list` | Query Coast Guard records | Yes |
| `mekong_coastguard_status` | Retrieve Coast Guard telemetry | Yes |

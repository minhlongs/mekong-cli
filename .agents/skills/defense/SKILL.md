---
name: defense
description: "Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Suite (Phase 100)."
commands:
  - "mekong defense"
  - "mekong defense license"
  - "mekong defense dual-use"
  - "mekong defense mobilization"
  - "mekong defense qa"
  - "mekong defense list"
  - "mekong defense status"
tools:
  - "mekong_defense_license"
  - "mekong_defense_dual_use"
  - "mekong_defense_mobilization"
  - "mekong_defense_qa"
  - "mekong_defense_list"
  - "mekong_defense_status"
---

# Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Suite (`mekong defense`)

Century Milestone (Phase 100) — Enterprise & sovereign regulatory compliance suite for Vietnam's defense industry, security export controls, and industrial mobilization preparedness.

## 1. Statutory Framework

1. **Law on National Defense and Security Industry and Industrial Mobilization 2024 (Law 38/2024/QH15)**:
   - Passed June 27, 2024 by the National Assembly of Vietnam.
   - Regulates core defense enterprises, designated private contractors, strategic dual-use goods, defense research & development, and peacetime/wartime industrial mobilization.
2. **Law on National Defense 2018 (Law 22/2018/QH14)**:
   - Fundamental principles of all-people national defense, armed forces equipment, and state emergency powers.
3. **Decrees on Dual-Use Goods & Security Export Controls**:
   - Mandatory End-User Certificates (EUC), foreign diplomatic verification, and strict prohibitions against unauthorized re-transfers.
4. **Military Technical Standards & Acceptance (TCVN/QS & TCVN/AN)**:
   - Environmental resilience (-10°C to +55°C, 96h salt fog resistance), ECM anti-jamming ($\ge 30.0\text{ dB}$), and precision mechanical tolerances ($\le 0.10\%$).

---

## 2. CLI Command Surface

```bash
# General status & telemetry dashboard
mekong defense
mekong defense status --json

# Audit defense facility licensing conditions (Articles 19-21)
mekong defense license "Nhà máy Z111" \
  --type STATE_OWNED_DEFENSE_ENTERPRISE \
  --category WEAPONS_AMMUNITION \
  --clearance TOP_SECRET \
  --personnel \
  --perimeter \
  --waste \
  --json

# Screen strategic dual-use technology export & EUC (Articles 28-30)
mekong defense dual-use "Module Vi cơ điện tử bán dẫn cấp quân sự" \
  --code DU_SEMI_MIL \
  --qty 500 \
  --dest "SINGAPORE" \
  --end-user "TechDefense Corp" \
  --euc \
  --no-retransfer \
  --permit \
  --json

# Evaluate industrial mobilization readiness plan (Articles 45-50)
mekong defense mobilization "Công ty CP Cơ khí Hàng không Dân dụng" \
  --capacity DRONE_AIRFRAME \
  --lines 2 \
  --stock-days 120 \
  --drill \
  --cyber \
  --json

# Assess military technical standard acceptance QA (Article 25)
mekong defense qa "Radar Cảnh giới Biển ven bờ thế hệ mới" \
  --standard TCVN_QS_789 \
  --temp "-10C to +55C" \
  --salt-fog 120 \
  --anti-jamming 35.0 \
  --tolerance 0.05 \
  --json

# List stored records
mekong defense list all --limit 20 --json
mekong defense list licenses --limit 10
mekong defense list dual_use --limit 10
mekong defense list mobilization --limit 10
mekong defense list qa --limit 10
```

---

## 3. Native MCP Tools

1. `mekong_defense_license`:
   - Audit defense and security production facility licensing conditions (Articles 19-21 Law 38/2024/QH15).
2. `mekong_defense_dual_use`:
   - Verify dual-use technologies and strategic goods export controls (Articles 28-30 Law 38/2024/QH15).
3. `mekong_defense_mobilization`:
   - Evaluate enterprise industrial mobilization readiness plan (Articles 45-50 Law 38/2024/QH15).
4. `mekong_defense_qa`:
   - Assess military technical standards and equipment QA testing under Article 25 Law 38/2024/QH15.
5. `mekong_defense_list`:
   - Query stored defense facility licenses, dual-use export records, mobilization plans, or technical QA records.
6. `mekong_defense_status`:
   - Aggregate national defense industry, dual-use trade controls, and industrial mobilization telemetry.

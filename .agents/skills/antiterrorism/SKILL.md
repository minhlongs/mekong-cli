---
name: antiterrorism
description: Vietnamese Anti-Terrorism, Homeland Security & Target Protection Suite (Luật Phòng, chống khủng bố 2013 & Nghị định 07/2014/NĐ-CP).
---

# Anti-Terrorism & Target Protection Suite (`mekong antiterrorism`)

Vietnamese Anti-Terrorism, Homeland Security & Critical Target Protection Suite governed by:
- **Law on Anti-Terrorism 2013** (Law No. 28/2013/QH13)
- **Decree No. 07/2014/NĐ-CP** (Command, Coordination and Implementation of Counter-Terrorism Operations)
- **Decree No. 37/2009/NĐ-CP** (List of Critical National Security Targets Guarded by Police)
- **Prime Minister Decision No. 42/2015/QĐ-TTg** (Security and Civil Defense of Vital Targets)

## Capabilities & Workflows

1. **Vital National Security Targets (`mekong antiterrorism target`)**:
   - Register and protect special-class and class-I national infrastructure (headquarters, hydro dams, central treasury, 500kV grid, embassies).
   - Enforce security perimeter cordons and police guard forces (K01, K02).
2. **Threat Alerts & Warning Tiers (`mekong antiterrorism alert`)**:
   - Issue multi-tier threat alerts (Elevated Blue, Substantial Yellow, Severe Orange, Critical Red) with automated target status elevation.
3. **Emergency Contingency Plans (`mekong antiterrorism plan`)**:
   - Register battle plans across tactical scenarios (hostage rescue, EOD bomb disposal, CBRN decontamination, cyber countermeasure).
4. **Terrorist Designation & Asset Freezes (`mekong antiterrorism designate` & `freeze`)**:
   - Designate terrorist organizations/individuals and mandate immediate freezing of bank accounts and funds (Article 34).
5. **Tactical Operations Log (`mekong antiterrorism operate`)**:
   - Record response operations, hostage rescue tallies, suspect neutralizations, and stand-down orders.

## CLI Reference

```bash
# Executive Dashboard & Metrics
mekong antiterrorism
mekong antiterrorism --json
mekong antiterrorism status [--json]

# Register Vital Target
mekong antiterrorism target \
  --id "TGT-BCA-01" \
  --name "Tòa nhà Quốc hội Nước CHXHCN Việt Nam" \
  --category "POLITICAL_HEADQUARTERS" \
  --level "SPECIAL_CLASS" \
  --guard "Bộ Tư lệnh Cảnh vệ K01" \
  --address "Số 1 đường Độc Lập, Ba Đình, Hà Nội" \
  --perimeter 250 \
  --json

# Issue Threat Warning
mekong antiterrorism alert \
  --id "ALERT-2026-001" \
  --source "Cục An ninh mạng và phòng, chống tội phạm công nghệ cao (A05)" \
  --type "CYBER_TERRORISM" \
  --level "SEVERE_ORANGE" \
  --summary "Nguy cơ tấn công từ chối dịch vụ và mã độc tống tiền vào trung tâm điều độ điện lưới quốc gia" \
  --targets "TGT-BCA-01,TGT-EVN-01" \
  --json

# Register Contingency Tactical Plan
mekong antiterrorism plan \
  --id "PLAN-CT-01" \
  --target-id "TGT-BCA-01" \
  --name "Phương án bảo vệ tuyệt đối mục tiêu trọng yếu và giải tán đám đông vũ trang" \
  --scenario "HOSTAGE_RESCUE" \
  --agency "Bộ Tư lệnh Cảnh vệ" \
  --units "K01,K02,Công an TP Hà Nội" \
  --drill "2026-02-15" \
  --json

# Terrorist Designation & Immediate Asset Freeze
mekong antiterrorism designate \
  --id "TERR-001" \
  --name "Tổ chức khủng bố X" \
  --type "ORGANIZATION" \
  --decision "Thông báo số 01/TB-BCA" \
  --aliases "Nhóm Hành động Tự do, Liên minh X" \
  --json

mekong antiterrorism freeze \
  --id "TERR-001" \
  --accounts 14 \
  --amount 12500000000 \
  --json

# Tactical Operation Log
mekong antiterrorism operate \
  --id "OP-2026-001" \
  --alert-id "ALERT-2026-001" \
  --target-id "TGT-BCA-01" \
  --action "DEPLOY_TACTICAL_SNIPERS_AND_CORDON" \
  --officer "Đại tá Nguyễn Văn Hùng" \
  --hostages 0 \
  --neutralized 2 \
  --status "RESOLVED_SUCCESS" \
  --json
```

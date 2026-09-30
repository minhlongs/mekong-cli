---
name: anticorruption
description: Vietnamese Anti-Corruption, Asset Declaration & Integrity Oversight Suite (Luật Phòng, chống tham nhũng 2018 & Nghị định 130/2020/NĐ-CP).
---

# Anti-Corruption & Asset Declaration Suite (`mekong anticorruption`)

Vietnamese Anti-Corruption, Asset Declaration & Integrity Oversight Suite governed by:
- **Law on Anti-Corruption 2018** (Law No. 36/2018/QH14)
- **Decree No. 130/2020/NĐ-CP** (Control of Assets and Income of Persons with Positions and Powers)
- **Decree No. 59/2019/NĐ-CP** (Guiding the Implementation of Anti-Corruption Measures)
- **Resolution No. 03/2020/NQ-HĐTP** (Judicial Guidance on Corruption & Position-Related Offenses)

## Capabilities & Workflows

1. **Asset & Income Declarations (`mekong anticorruption declare`)**:
   - Register initial, annual, supplementary, and appointment-vetting asset declarations.
   - Track real estate, movable property (gold, cash, shares >= 50M VND), overseas assets, and annual income.
2. **Integrity Verification Audits (`mekong anticorruption verify`)**:
   - Execute verification under annual random sampling (>=20% units, >=10% declarants) or suspicion grounds.
   - Detect and compute unexplained wealth and flag fraudulent concealment discrepancies.
3. **Gift Surrender Registry (`mekong anticorruption gift`)**:
   - Record gifts received in breach of protocol and track State Treasury deposit vouchers within 5 days.
4. **Conflict of Interest Registry (`mekong anticorruption conflict`)**:
   - Identify kinship procurement prohibitions, nepotism in appointments, and outside commercial conflicts.
   - Enforce recusal, transfer, or divestment mandates.
5. **Sanctions & Criminal Referrals (`mekong anticorruption sanction`)**:
   - Record administrative disciplinary penalties (reprimand, warning, demotion, dismissal).
   - Track criminal referral dockets to Supreme People's Procuracy (VKSNDTC) or Police Investigation Agency (C03).

## CLI Reference

```bash
# Executive Dashboard & Metrics
mekong anticorruption
mekong anticorruption --json
mekong anticorruption status [--json]

# Register Asset Declaration
mekong anticorruption declare \
  --id "DEC-2026-001" \
  --declarant-id "CCCD-001" \
  --name "Nguyễn Văn Quan" \
  --org "Sở Kế hoạch và Đầu tư" \
  --title "Phó Giám đốc" \
  --type "ANNUAL" \
  --year 2025 \
  --real-estate 15000000000 \
  --movable 2500000000 \
  --overseas 0 \
  --income 800000000 \
  --json

# Conduct Verification Audit
mekong anticorruption verify \
  --id "VER-2026-001" \
  --declaration "DEC-2026-001" \
  --agency "Thanh tra Tỉnh" \
  --ground "ANNUAL_RANDOM_SELECTION" \
  --verified-wealth 25000000000 \
  --summary "Phát hiện thêm 1 bất động sản và 2 tài khoản ngân hàng chưa giải trình nguồn gốc" \
  --json

# Record Gift Surrender to Treasury
mekong anticorruption gift \
  --id "GIFT-2026-001" \
  --declarant-id "CCCD-001" \
  --name "Nguyễn Văn Quan" \
  --org "Sở Kế hoạch và Đầu tư" \
  --desc "Bộ đồng hồ mạ vàng của nhà thầu X" \
  --giver "Công ty Cổ phần Xây dựng X" \
  --value 120000000 \
  --voucher "KB-2026-9912" \
  --json

# Conflict of Interest Management
mekong anticorruption conflict \
  --id "COI-2026-001" \
  --person-id "CCCD-001" \
  --name "Nguyễn Văn Quan" \
  --org "Sở Kế hoạch và Đầu tư" \
  --category "PROCUREMENT_BIDDING" \
  --relation "Em ruột là Tổng Giám đốc đơn vị dự thầu Gói thầu số 05" \
  --risk "PROHIBITED" \
  --remediation "Rút khỏi Hội đồng thẩm định và không tham gia phê duyệt kết quả trúng thầu" \
  --json

# Disciplinary Sanction / Criminal Referral
mekong anticorruption sanction \
  --id "SANCT-2026-001" \
  --target-id "CCCD-001" \
  --name "Nguyễn Văn Quan" \
  --case-ref "VER-2026-001" \
  --type "WARNING" \
  --authority "Chủ tịch UBND Tỉnh" \
  --decision "QĐ 142/QĐ-UBND" \
  --json
```

---
name: statesecret
description: Vietnamese State Secrets & Classified Intelligence Protection Suite (Luật Bảo vệ bí mật nhà nước 2018 & Nghị định 26/2020/NĐ-CP).
---

# State Secret & Classified Protection Suite (`mekong statesecret`)

Vietnamese State Secrets & Classified Intelligence Protection Suite governed by:
- **Law on Protection of State Secrets 2018** (Law No. 35/2018/QH14)
- **Decree No. 26/2020/NĐ-CP** (Guiding the Implementation of Law on Protection of State Secrets)
- **Circular No. 24/2020/TT-BCA** (Forms, Stamps, and Registers in State Secret Protection)
- **Prime Minister Sectoral Decisions on State Secret Lists**

## Capabilities & Workflows

1. **Classification & Carrier Registration (`mekong statesecret classify`)**:
   - Register and classify documents, encrypted USBs, cryptographic devices, or scientific models under Article 10.
   - Enforce statutory terms: Top Secret (Tuyệt mật: 30 years), Secret (Tối mật: 20 years), Confidential (Mật: 10 years).
   - Generate official classification stamp codes pursuant to Circular 24/2020/TT-BCA.
2. **Access & Operation Authorizations (`mekong statesecret authorize`)**:
   - Authorize access, copying, duplicating, extracting, or taking secret documents outside headquarters (Articles 11, 14, 15).
   - Track validity windows, authorized personnel, and copy quotas with an immutable audit trail.
3. **Declassification & Term Adjustments (`mekong statesecret adjust`)**:
   - Execute statutory declassification (full or partial), expiration, grade downgrading/upgrading, or term extensions (Articles 20, 21, 22).
4. **Secure Destruction Protocols (`mekong statesecret destruct`)**:
   - Record secure disposal via high-temperature incineration, chemical pulping, DIN 66399 P-7 shredding, or DoD cryptographic wipe (Article 23).
5. **Security Breach Investigation (`mekong statesecret incident`)**:
   - Report, contain, and investigate unauthorized leaks, losses, copies, or cyber thefts.
   - Manage immediate containment, quarantine, and referrals to internal political security agencies (A03/C03).

## CLI Reference

```bash
# Executive Dashboard & Metrics
mekong statesecret
mekong statesecret --json
mekong statesecret status [--json]

# Classify State Secret Document or Carrier
mekong statesecret classify \
  --id "SEC-BQP-2026-001" \
  --title "Kế hoạch Phòng thủ Chiến lược Vùng biển Đảo Quốc gia" \
  --level "TUYET_MAT" \
  --agency "Bộ Quốc phòng" \
  --auth "Bộ trưởng Bộ Quốc phòng" \
  --carrier "DOCUMENT_PAPER" \
  --scope "Thường trực Ban Bí thư, Thủ tướng Chính phủ, Bộ Tổng Tham mưu" \
  --stamp "DAU-TUYET-MAT-BQP-01" \
  --json

# Authorize Copying or Taking Outside Headquarters
mekong statesecret authorize \
  --id "AUTH-2026-001" \
  --item-id "SEC-BQP-2026-001" \
  --person "Thiếu tướng Nguyễn Văn A - Cục trưởng Cục Tác chiến" \
  --auth-by "Thủ trưởng Cơ quan" \
  --op "COPY_DUPLICATE" \
  --purpose "Phục vụ diễn tập chỉ huy tham mưu tác chiến cấp chiến dịch" \
  --copies 2 \
  --from "2026-04-01" \
  --until "2026-04-05" \
  --json

# Declassification / Grade Adjustment / Extension
mekong statesecret adjust \
  --id "DECLAS-2026-001" \
  --item-id "SEC-BQP-2026-001" \
  --type "GRADE_DOWNGRADE" \
  --new-level "TOI_MAT" \
  --decision "Quyết định số 15/QĐ-BQP" \
  --authority "Bộ trưởng Bộ Quốc phòng" \
  --reason "Đã hoàn thành giai đoạn 1, điều chỉnh độ mật để triển khai thực địa" \
  --json

# Secure Destruction Protocol
mekong statesecret destruct \
  --id "DEST-2026-001" \
  --item-id "SEC-BQP-2026-001" \
  --chair "Chủ tịch Hội đồng Tiêu hủy" \
  --method "INCINERATION_HIGH_TEMP" \
  --minutes "BB-TH-01/BQP" \
  --witnesses "Đại tá Trần B, Trung tá Lê C" \
  --json

# Security Incident Report & Investigation
mekong statesecret incident \
  --id "INC-2026-001" \
  --item-id "SEC-BQP-2026-001" \
  --type "LEAK_DISCLOSURE" \
  --severity "CRITICAL" \
  --suspect "Đối tượng nghi vấn X" \
  --quarantine "Thu hồi toàn bộ bản sao, vô hiệu hóa tài khoản mạng nội bộ" \
  --referral "Cục An ninh chính trị nội bộ (A03)" \
  --json

# Query Records
mekong statesecret list --type all --limit 20 --json
```

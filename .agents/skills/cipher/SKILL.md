---
name: cipher
description: Vietnamese National Cryptography, State Cipher & Civil Cryptography Suite (Luật Cơ yếu 2011 & Nghị định 58/2016/NĐ-CP).
---

# National Cryptography, State Cipher & Civil Cryptography Suite (`mekong cipher`)

Vietnamese National Cryptography, State Cipher & Civil Cryptography Suite governed by:
- **Law on Cryptography 2011** (Law No. 05/2011/QH13 — Luật Cơ yếu 2011)
- **Decree No. 58/2016/NĐ-CP & Decree No. 53/2018/NĐ-CP** (Licensing of Civil Cryptography Products & Services; Import/Export Permits)
- **Decree No. 09/2014/NĐ-CP** (Implementation Guidelines for Law on Cryptography)
- **Circular No. 23/2022/TT-BQP** (Technical Standards on Cryptographic Equipment & Evaluation)

## Capabilities & Workflows

1. **State Cipher Systems Registry (`mekong cipher system`)**:
   - Register and manage state cryptographic networks protecting state secrets across 4 organizational branches:
     - `PARTY_GOVERNMENT` (Cơ yếu Đảng - Chính quyền)
     - `MILITARY_DEFENSE` (Cơ yếu Quân đội nhân dân)
     - `PUBLIC_SECURITY` (Cơ yếu Công an nhân dân)
     - `DIPLOMATIC_FOREIGN` (Cơ yếu Ngoại giao)
   - Enforce security classification levels: `TUYET_MAT_TOP_SECRET`, `TOI_MAT_SECRET`, `MAT_CONFIDENTIAL`.
2. **Cryptographic Key Lifecycle Management (`mekong cipher key`)**:
   - Manage master root keys, transport session keys, encryption keys, and signing auth keys under Article 15 Law on Cryptography 2011.
   - Enforce minimum 128/256-bit key length, custodian officer assignment, periodic rotation intervals (30-365 days), and expiration tracking.
3. **Civil Cryptography Licensing (`mekong cipher license`)**:
   - Manage commercial licensing of civil cryptography products and services under Decree 58/2016/NĐ-CP and Decree 53/2018/NĐ-CP.
   - Authorize trading, service provision, and import/export permits across certified categories: `HARDWARE_HSM`, `SECURITY_IP_VPN`, `PKI_SMART_CARD`, `SECURE_MESSAGING_APP`, `ENCRYPTED_STORAGE`.
4. **Dedicated Equipment & Hardware Modules (`mekong cipher equipment`)**:
   - Register dedicated cryptographic encryptors, HSM appliances, and secure VPN routers under Article 12 Law on Cryptography 2011.
   - Certify tamper resistance levels: `PHYSICAL_ZEROIZE_SENSITIVE`, `TAMPER_EVIDENT`, `TAMPER_RESISTANT`, `COGNITIVE_SHIELDED`.
5. **Cryptographic Security Breach & Containment (`mekong cipher incident`)**:
   - Log and contain cryptographic security incidents, key compromise events, tamper alerts, and firmware anomalies under Article 20 Law on Cryptography 2011.
   - Record emergency zeroization, key revocation, and mitigation workflows.

## CLI Reference

```bash
# Executive Dashboard & Metrics
mekong cipher
mekong cipher --json
mekong cipher status [--json]

# Register State Cipher System
mekong cipher system \
  --id "SYS-GOV-01" \
  --name "Mạng Thông tin Mật mã Chính phủ điện tử Trục Quốc gia" \
  --branch "PARTY_GOVERNMENT" \
  --level "TUYET_MAT_TOP_SECRET" \
  --location "Trung tâm Dữ liệu Quốc gia, Hà Nội" \
  --algo "TCVN-7142-GOV" \
  --status "ACTIVE_OPERATIONAL" \
  --json

# Issue Cryptographic Key
mekong cipher key \
  --id "KEY-2026-A1" \
  --system "SYS-GOV-01" \
  --type "MASTER_ROOT_KEY" \
  --officer "Đại tá Trần Văn Bình" \
  --bits 256 \
  --interval 90 \
  --json

# Register Civil Cryptography Business License
mekong cipher license \
  --id "LIC-MMDS-2026-001" \
  --enterprise "Tập đoàn Công nghệ An ninh Mạng Quốc gia" \
  --tax-id "0109988776" \
  --type "PRODUCT_TRADING" \
  --category "HARDWARE_HSM" \
  --authority "Ban Cơ yếu Chính phủ - Cục QLMMDS" \
  --json

# Register & Certify Cryptographic Equipment
mekong cipher equipment \
  --id "EQ-HSM-2026-01" \
  --serial "VN-HSM-9988-X1" \
  --model "VNCIPHER-HSM-4000" \
  --type "HSM_APPLIANCE" \
  --tamper "PHYSICAL_ZEROIZE_SENSITIVE" \
  --unit "Cục Cơ yếu Đảng - Chính quyền" \
  --status "CERTIFIED_PASSED" \
  --json

# Report Cryptographic Incident
mekong cipher incident \
  --id "INC-CIPHER-2026-01" \
  --target "KEY-2026-A1" \
  --severity "HIGH_TAMPER_DETECTED" \
  --desc "Phát hiện can thiệp cảm biến mở vỏ vật lý tại nút mạng dự phòng" \
  --actions "Kích hoạt tự động Zeroize bộ nhớ khóa và thu hồi chứng thư khẩn cấp" \
  --officer "Thiếu tá Lê Hồng Quang" \
  --resolved \
  --json

# List Records
mekong cipher list --type all [--limit 50] [--json]
mekong cipher list --type systems [--json]
mekong cipher list --type keys [--json]
mekong cipher list --type licenses [--json]
mekong cipher list --type equipment [--json]
mekong cipher list --type incidents [--json]
```

## Native MCP Tools Reference

- `mekong_cipher_system`: Register or update a state cipher system under Law on Cryptography 2011.
- `mekong_cipher_key`: Issue and manage cryptographic key lifecycle under Article 15 Law on Cryptography 2011.
- `mekong_cipher_license`: Issue or manage civil cryptography business license under Decree 58/2016/NĐ-CP.
- `mekong_cipher_equipment`: Register and certify dedicated cryptographic equipment or HSM modules under Article 12 Law on Cryptography 2011.
- `mekong_cipher_incident`: Report cryptographic breach, key compromise, or tamper alert under Article 20 Law on Cryptography 2011.
- `mekong_cipher_list`: List cipher systems, keys, civil licenses, certified equipment, and incident reports.
- `mekong_cipher_status`: Aggregate telemetry metrics on state cipher networks, key health, and civil crypto compliance.

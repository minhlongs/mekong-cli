---
name: identity
description: Vietnamese National Identification, Electronic Identity (VNeID), Biometrics & Population Database Suite.
---

# `mekong identity` — Vietnamese National Identification, Electronic Identity (VNeID) & Biometrics Suite

Governed by:
- **Law on Identification 2023 (Law No. 26/2023/QH15 — Luật Căn cước 2023)**: Effective July 1, 2024, replacing the Law on Citizen Identification 2014. Establishes the 12-digit Identity Card (Thẻ Căn cước), biometric enrollment (iris, face, fingerprints, DNA, voice), and Identity Certificates for persons of Vietnamese origin without nationality.
- **Decree No. 69/2024/NĐ-CP**: Regulating electronic identification and electronic authentication, Level 1 and Level 2 VNeID accounts, and electronic citizen integration.
- **Decree No. 70/2024/NĐ-CP**: Detailed regulations guiding implementation of the Law on Identification.
- **Circular No. 16/2024/TT-BCA & Circular No. 17/2024/TT-BCA**: Standard templates, biometric specifications, and administrative management procedures.
- **Law on Residence 2020 (Law No. 68/2020/QH14)**: National Population Database connection and data verification.

---

## 1. Capabilities & Core Subcommands

| Subcommand | Description | Key Parameters |
|---|---|---|
| `mekong identity` | Executive dashboard overview of Identity Cards, VNeID, Biometrics, and KYC Audits | `--json` |
| `mekong identity card` | Issue or register a 12-digit Identity Card under Law 26/2023/QH15 | `--id`, `--name`, `--dob`, `--gender`, `--pob`, `--por`, `--ethnicity`, `--nationality`, `--status`, `--issue-date`, `--expiry-date`, `--authority`, `--json` |
| `mekong identity vneid` | Provision or upgrade an Electronic Identity (VNeID) account | `--id`, `--phone`, `--level <LEVEL_1\|LEVEL_2>`, `--email`, `--docs`, `--status`, `--json` |
| `mekong identity biometric` | Enroll biometric data (Iris scan, Facial portrait, Fingerprint, DNA, Voice) | `--id`, `--type`, `--collection`, `--score`, `--officer`, `--payload`, `--json` |
| `mekong identity cert` | Issue Identity Certificate for person of VN origin without nationality (Điều 30) | `--name`, `--dob`, `--gender`, `--origin`, `--residence`, `--cert-id`, `--validity`, `--unit`, `--json` |
| `mekong identity verify` | Authenticate identity card or certificate against National Database | `--id`, `--agency`, `--method <QR_CODE_SCAN\|NFC_CHIP_READ\|VNEID_APP_AUTH\|BIOMETRIC_MATCH_IRIS\|BIOMETRIC_MATCH_FACE>`, `--sample`, `--bypass-offline`, `--json` |
| `mekong identity list` | List records across cards, vneid, biometrics, certificates, and audits | `--category <cards\|vneid\|biometrics\|certificates\|audits\|all>`, `--limit <int>`, `--json` |
| `mekong identity status` | Aggregate operational telemetry metrics | `--json` |

---

## 2. MCP Tools Reference

The suite exposes 7 canonical MCP tools with dual-engine parity across FastMCP and JSON-RPC 2.0 stdio:

- `mekong_identity_card`: Issue or register Identity Card under Law 26/2023/QH15.
- `mekong_identity_vneid`: Provision or update VNeID account under Decree 69/2024/NĐ-CP.
- `mekong_identity_biometric`: Enroll biometric profile (iris, face, fingerprints, DNA, voice) into database.
- `mekong_identity_certificate`: Issue Identity Certificate for persons of Vietnamese origin under Article 30 Law 26/2023.
- `mekong_identity_verify`: Verify identity against National Population Database and record KYC audit log.
- `mekong_identity_list`: Query records across categories.
- `mekong_identity_status`: Aggregate operational telemetry on cards, accounts, and biometrics.

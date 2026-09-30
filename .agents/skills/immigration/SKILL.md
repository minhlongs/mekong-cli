---
name: immigration
description: "Vietnamese Immigration, Entry, Exit, Transit, Residence & Visa Management Suite (Law 47/2014 & Law 23/2023)."
---

# Vietnamese Immigration, Entry, Exit, Transit, Residence & Visa Management Suite (`mekong immigration` / `mekong entryexit`)

The **Immigration Suite** codifies statutory procedures for foreign visa issuance (EV, DL, DN, DT, LD, TT), temporary and permanent residence cards (TRC, PRC), border gate movement screening, entry suspensions, exit postponements, and Vietnamese citizen electronic passports with biometric chip and Autogate integration, under:
- **Law on Entry, Exit, Transit, and Residence of Foreigners in Vietnam 2014 (Law No. 47/2014/QH13)**, amended 2019 (Law No. 51/2019/QH14) and 2023 (Law No. 23/2023/QH15).
- **Law on Exit and Entry of Vietnamese Citizens 2019 (Law No. 49/2019/QH14)**, amended 2023 (Law No. 23/2023/QH15).
- **Decree No. 75/2020/ND-CP & Decree No. 127/2024/ND-CP** (Electronic Visas, Border Controls, Autogates).
- **Circular No. 22/2023/TT-BCA** of the Ministry of Public Security (Immigration Department - Cục Quản lý xuất nhập cảnh).

---

## Key Capabilities

1. **Foreigner Visas (Điều 8-10 Law 47/2014 & Law 23/2023)**:
   - Electronic visas (`EV`) up to 90 days (single or multiple entry).
   - Investor visas (`DT1-DT4`), business visas (`DN1-DN2`), work visas (`LD1-LD2`), tourist visas (`DL`), and relatives (`TT`).
   - Passport validity check (at least 30 days longer than visa validity under Art 10).
2. **Residence Cards (Điều 36-43)**:
   - Temporary Residence Cards (`TRC`) valid from 1 to 5 years (up to 10 years for DT1).
   - Permanent Residence Cards (`PRC`) for foreign contributors, scientists, and relatives residing continuously for >= 3 years.
3. **Border Clearance & Autogate Verification**:
   - Automated screening against active restriction orders (entry suspensions and exit postponements) across international airports, seaports, land border gates, and Autogates.
4. **Immigration Restrictions (Điều 21 & Điều 28)**:
   - Statutory entry suspensions (`ENTRY_SUSPENSION`) and exit postponements (`EXIT_POSTPONEMENT`).
5. **Vietnamese Citizen Passports (Law 49/2019 & Law 23/2023)**:
   - Electronic chip passports, biometric compliance, and Autogate kiosk enrollment.

---

## CLI Commands

```bash
# Executive Dashboard & Telemetry
mekong immigration
mekong immigration --json
mekong immigration status --json

# Foreigner Visa Application
mekong immigration visa --applicant "John Doe" --nationality "USA" --passport-number "US123456" --passport-expiry "2030-01-01" --visa-type EV --duration-days 90 --entries MULTIPLE --port "Noi Bai International Airport"

# Residence Card Issuance (TRC / PRC)
mekong immigration residence --holder "Alice Smith" --nationality "UK" --passport-number "GB987654" --card-type TRC --symbol DT1 --duration-months 36 --sponsor "Tech Corp Vietnam" --address "Tay Ho, Hanoi"

# Border Movement Clearance
mekong immigration border --person "John Doe" --nationality "USA" --passport-number "US123456" --direction ENTRY --gate "Noi Bai International Airport" --autogate

# Restriction Order Registration
mekong immigration restriction --subject "Robert Brown" --nationality "Australia" --passport-number "AU554433" --type EXIT_POSTPONEMENT --basis "Tax debt Art 28 Law 47/2014" --authority "Hanoi Tax Department"

# Vietnamese Citizen Passport
mekong immigration passport --name "Nguyen Van A" --citizen-id "001090123456" --birth-date "1990-05-12" --chip --autogate

# Query Records
mekong immigration list --category visa --limit 20
mekong immigration list --category movement --json
```

---

## Native MCP Tools

- `mekong_immigration_visa`: Register or evaluate foreigner visa application.
- `mekong_immigration_residence`: Issue or manage TRC / PRC card.
- `mekong_immigration_border`: Log border crossing event with automated restriction screening.
- `mekong_immigration_restriction`: Impose or register entry suspension / exit postponement order.
- `mekong_immigration_passport`: Issue citizen electronic chip passport with Autogate integration.
- `mekong_immigration_list`: List records by category.
- `mekong_immigration_status`: Return aggregate immigration telemetry.

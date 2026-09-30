---
name: civil-status
description: "Vietnamese Civil Status, Vital Statistics & Population Registration Suite (Law 60/2014 & Decree 123/2015)."
---

# Vietnamese Civil Status, Vital Statistics & Population Registration Suite (`mekong civilstatus` / `mekong hothich`)

The **Civil Status Suite** codifies statutory procedures for birth registration with 12-digit Personal Identification Number (Số định danh cá nhân - DDCN) assignment, civil marriage registration, death registration, civil status rectifications (change of name, ethnicity, gender, and clerical corrections), and verified digital extracts, under:
- **Law on Civil Status 2014 (Luật Hộ tịch - Law No. 60/2014/QH13)**.
- **Decree No. 123/2015/ND-CP** detailing the implementation of the Law on Civil Status.
- **Decree No. 87/2020/ND-CP** on Electronic Civil Status Database & Shared National Population Database.
- **Circular No. 04/2020/TT-BTP** guiding the Law on Civil Status and Decree No. 123/2015/ND-CP.
- **Law on Identification 2023 (Law No. 26/2023/QH15)** on Personal Identification Numbers (Số định danh cá nhân).

---

## Key Capabilities

1. **Birth Registration & DDCN Assignment (Điều 13-16 Law 60/2014 & Law 26/2023)**:
   - Registers birth and automatically assigns a 12-digit Personal Identification Number following Ministry of Public Security century/gender rules: `[3-digit province][1-digit century/gender][2-digit year][6-digit sequence]`.
   - Century/gender coding: 20th century (1900-1999) codes Male = 0, Female = 1; 21st century (2000-2099) codes Male = 2, Female = 3.
2. **Statutory Jurisdiction & Foreign Elements (Điều 35 & Điều 37)**:
   - Domestic births and marriages are handled by the Commune People's Committee (`UBND cấp xã`).
   - Events involving foreign elements or overseas Vietnamese are mandated to be registered at District level (`UBND cấp huyện`) or Vietnamese Diplomatic Missions abroad.
3. **Civil Marriage Registration (Điều 17-18 & Điều 37-38)**:
   - Registers civil marriages with domestic and foreign-element validation, issuing official marriage certificate serials and book records.
4. **Death Registration & Vital Statistics (Điều 32-34 & Điều 51-52)**:
   - Registers death events, records cause of death, informant details, and issues official death certificates.
5. **Civil Rectifications & Corrections (Điều 26-28 & Điều 40-42)**:
   - Handles legal name changes, ethnicity re-determinations, gender transitions, and civil status record clerical rectifications backed by official decisions.
6. **Electronic Civil Status Extracts (Nghị định 87/2020/NĐ-CP)**:
   - Issues cryptographically verifiable digital civil status extracts (`Bản sao trích lục hộ tịch điện tử`) with unique digital signature tokens.

---

## CLI Commands

```bash
# Executive Dashboard & Telemetry
mekong civilstatus
mekong civilstatus --json
mekong civilstatus status --json
mekong hothich --json

# Birth Registration
mekong civilstatus birth --name "Nguyen Van An" --gender MALE --birth-date "2024-03-15" --birth-place "Benh vien Phu san Trung uong, Ha Noi" --registrant "Nguyen Van Binh" --mother "Tran Thi Mai" --mother-id "001190123456"

# Foreign-Element Marriage Registration (District Level)
mekong civilstatus marriage --husband "John Doe" --husband-dob "1988-06-20" --husband-id "US98765432" --husband-nat "USA" --wife "Nguyen Thi Lan" --wife-dob "1992-09-10" --wife-id "001192112233" --wife-nat "Việt Nam" --level DISTRICT --foreign-element --authority "UBND Quan Hoan Kiem, Ha Noi"

# Death Registration
mekong civilstatus death --deceased "Pham Van D" --gender MALE --birth-date "1945-01-01" --death-date "2024-05-10" --death-place "Ha Noi" --cause "Natural causes" --informant "Pham Van Con" --authority "UBND Phuong Hang Gai, Hoan Kiem, Ha Noi"

# Civil Status Rectification (Name / Ethnicity / Gender)
mekong civilstatus rectify --name "Le Thi C" --citizen-id "001195654321" --type NAME_CHANGE --original "Le Thi C" --corrected "Le Hoang Chau" --legal-basis "Dieu 26 Luat Ho tich 2014" --decision "QD-123/UBND" --authority "UBND Quan Hoan Kiem, Ha Noi"

# Electronic Civil Status Extract
mekong civilstatus extract --type BIRTH --record-id "BIRTH-12345678" --name "Nguyen Van An" --authority "So Tu phap TP Ha Noi"

# Query Records
mekong civilstatus list --category birth --limit 20
mekong civilstatus list --category audit --json
```

---

## Native MCP Tools

- `mekong_civilstatus_birth`: Register birth and assign 12-digit Personal Identification Number (DDCN).
- `mekong_civilstatus_marriage`: Register domestic or foreign-element civil marriage.
- `mekong_civilstatus_death`: Register death and issue death certificate.
- `mekong_civilstatus_rectify`: Rectify or correct civil status record.
- `mekong_civilstatus_extract`: Issue electronic civil status extract with digital signature.
- `mekong_civilstatus_list`: List records by category.
- `mekong_civilstatus_status`: Return aggregate civil status and vital statistics telemetry.

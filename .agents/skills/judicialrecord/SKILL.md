---
name: judicialrecord
description: Vietnamese Judicial Records, Criminal Clearance & VNeID Electronic Certificates Suite (Luật Lý lịch tư pháp 2009 & BLHS 2015).
---

# Vietnamese Judicial Records & Criminal History Clearance Suite (`mekong judicialrecord`)

Comprehensive automated suite for managing Vietnamese Judicial Record Certificates (Phiếu Lý lịch tư pháp số 1 & số 2), automated criminal record remission (Xóa án tích), corporate prohibition orders, and VNeID electronic certification.

Compliant with:
- **Law on Judicial Records 2009 (Luật Lý lịch tư pháp - Luật số 28/2009/QH12)**
- **Decree No. 111/2010/ND-CP** detailing implementation of Law on Judicial Records
- **Decree No. 82/2020/ND-CP** on administrative penalties
- **Circular No. 06/2013/TT-BTP & Circular No. 04/2024/TT-BTP** on judicial record forms & VNeID electronic issuance
- **Penal Code 2015, amended 2017 (Bộ luật Hình sự - Articles 69, 70, 71, 72, 73 on Criminal Record Remission)**
- **Decree No. 59/2022/ND-CP** on Electronic Identification and Authentication (Level 2 VNeID digital certificates)

---

## Command Reference

### Executive Telemetry Dashboard
```bash
mekong judicialrecord
mekong lylich
mekong criminalrecord
mekong judicialrecord status --json
```

### 1. Request Judicial Record Certificate (Phiếu số 1 hoặc số 2)
```bash
# Request Form No. 1 for employment / civil purposes
mekong judicialrecord request \
  --form FORM_1 \
  --name "Nguyễn Văn Hùng" \
  --id "001088001234" \
  --dob "1988-06-15" \
  --gender "MALE" \
  --permanent "Số 25 Lý Thường Kiệt, Hoàn Kiếm, Hà Nội" \
  --current "Số 25 Lý Thường Kiệt, Hoàn Kiếm, Hà Nội" \
  --purpose "Bổ nhiệm cán bộ và xin việc làm" \
  --vneid \
  --json

# Request Form No. 2 for procedural agencies / individual full disclosure
mekong judicialrecord request \
  --form FORM_2 \
  --name "Trần Thị Mai" \
  --id "001190005678" \
  --dob "1990-09-20" \
  --gender "FEMALE" \
  --permanent "Quận 1, TP. Hồ Chí Minh" \
  --current "Quận 1, TP. Hồ Chí Minh" \
  --purpose "Tố tụng hình sự" \
  --vneid
```

### 2. Record Criminal Conviction from Court Judgment
```bash
mekong judicialrecord conviction \
  --id "001088001234" \
  --judgment "45/2020/HS-ST" \
  --court "Tòa án nhân dân TP Hà Nội" \
  --date "2020-05-15" \
  --offense "Vi phạm quy định về tham gia giao thông đường bộ" \
  --severity "LESS_SERIOUS" \
  --primary-penalty "01 năm tù cho hưởng án treo, thử thách 02 năm" \
  --penalty-completed-date "2022-05-15" \
  --civil \
  --fees
```

### 3. Evaluate Remission of Criminal Record (Xóa án tích)
```bash
# Automated evaluation under Article 70 Penal Code 2015
mekong judicialrecord clearance \
  --conviction-id "CONV-12345678" \
  --json
```

### 4. Record Prohibition from Corporate Office / Enterprise Management
```bash
mekong judicialrecord prohibition \
  --id "001088001234" \
  --type "Cấm thành lập, quản lý doanh nghiệp" \
  --court "Tòa án nhân dân Cấp cao tại Hà Nội" \
  --judgment "12/2021/KDTM-PT" \
  --start-date "2021-06-01" \
  --end-date "2026-06-01" \
  --details "Cấm quản lý công ty chứng khoán theo Luật Doanh nghiệp 2020"
```

### 5. Synthesize History & Issue Official Electronic Certificate
```bash
mekong judicialrecord issue \
  --request-id "REQ-LLTP-12345678" \
  --json
```

### 6. Query Records
```bash
mekong judicialrecord list --category request --limit 20
mekong judicialrecord list --category conviction --limit 20
mekong judicialrecord list --category certificate --json
```

---

## MCP Tools Integration

| Tool Name | Description |
|-----------|-------------|
| `mekong_judicialrecord_request` | Submit application for Judicial Record Certificate Form No. 1 or No. 2 |
| `mekong_judicialrecord_conviction` | Record criminal judgment and penalty into National Database |
| `mekong_judicialrecord_clearance` | Evaluate criminal record remission under Articles 70-73 Penal Code |
| `mekong_judicialrecord_prohibition` | Record prohibition from holding positions or enterprise management |
| `mekong_judicialrecord_issue` | Issue electronic Judicial Record Certificate with digital signature token |
| `mekong_judicialrecord_list` | Query judicial record entries across all categories |
| `mekong_judicialrecord_status` | Show national judicial record system telemetry |

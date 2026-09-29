---
name: education
description: Vietnamese Education, Higher Education, Accreditation & Degree Registry Suite.
---

# mekong education — Autonomous Vietnamese Education, Higher Education, Accreditation & Degree Registry Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Giáo dục 2019 (Luật số 43/2019/QH14) & Luật Giáo dục đại học 2018 (Luật số 34/2018/QH14)**:
   - Thống nhất quản lý nhà nước về hệ thống giáo dục quốc dân, quyền tự chủ đại học và trách nhiệm giải trình.
   - Cơ quan quản lý nhà nước: **Bộ Giáo dục và Đào tạo (Bộ GD&ĐT)** và Ủy ban nhân dân các cấp.
2. **Điều kiện đầu tư và hoạt động trong lĩnh vực giáo dục (Nghị định số 125/2024/NĐ-CP)**:
   - **Trường Đại học tư thục / Công lập tự chủ**: Vốn đầu tư tối thiểu **1,000 tỷ VND** (không tính giá trị đất), diện tích đất tối thiểu **5 ha** ($50,000\text{ m}^2$). Thẩm quyền quyết định: **Thủ tướng Chính phủ**.
   - **Phân hiệu trường Đại học**: Vốn đầu tư tối thiểu **250 tỷ VND**, diện tích tối thiểu **2 ha** ($20,000\text{ m}^2$). Thẩm quyền: **Bộ trưởng Bộ GD&ĐT**.
   - **Trường Phổ thông nhiều cấp học (K-12)**: Vốn đầu tư tối thiểu **100 tỷ VND** (bình quân $\ge 50\text{ triệu/học sinh}$), diện tích tối thiểu **1 ha** ($10,000\text{ m}^2$). Thẩm quyền: **Chủ tịch UBND cấp tỉnh**.
   - **Trường Cao đẳng nghề**: Vốn đầu tư tối thiểu **100 tỷ VND**, diện tích tối thiểu **2 ha**. Thẩm quyền: **Bộ LĐ-TB&XH**.
   - **Cơ sở GDĐH có vốn đầu tư nước ngoài (FDI)**: Vốn đầu tư tối thiểu **1,000 tỷ VND**, diện tích tối thiểu **5 ha**. Thẩm quyền: **Thủ tướng Chính phủ**.
3. **Kiểm định chất lượng cơ sở giáo dục đại học (Thông tư số 12/2017/TT-BGDĐT)**:
   - Bộ tiêu chuẩn kiểm định gồm **25 tiêu chuẩn** và **111 tiêu chí** (thang điểm 1-7, mức Đạt $\ge 4.0$).
   - Tỷ lệ sinh viên / giảng viên quy đổi: **STR $\le 20:1$** (Student-to-Faculty Ratio).
   - Tỷ lệ giảng viên cơ hữu có trình độ Tiến sĩ: **Tối thiểu $\ge 35\%$** (đối với đào tạo đại học) và $\ge 50\%$ (đối với sau đại học).
   - Diện tích sàn xây dựng phục vụ đào tạo bình quân: **Tối thiểu $\ge 2.8\text{ m}^2/\text{sinh viên}$**.
   - Đạt chuẩn kiểm định (ACCREDITED) nếu không vi phạm các điều kiện ngặt nghèo và đạt ít nhất 90 tiêu chí, hiệu lực **5 năm**.
4. **Xác định chỉ tiêu tuyển sinh đại học hàng năm (Thông tư số 03/2022/TT-BGDĐT)**:
   - Chỉ tiêu tuyển sinh được giới hạn bởi hai điều kiện ràng buộc: Năng lực đội ngũ giảng viên toàn thời gian (20 SV/GV quy đổi) và diện tích sàn xây dựng ($2.8\text{ m}^2/\text{SV}$).
   - Phân bổ chỉ tiêu tuyển sinh mới hàng năm tương ứng khoảng $1/4$ tổng quy mô năng lực đào tạo 4 năm.
5. **Cấp phát và xác thực văn bằng điện tử chống giả mạo (Thông tư số 21/2019/TT-BGDĐT)**:
   - Sổ cấp phát văn bằng quốc gia với số hiệu định danh duy nhất (`VB-YYYY-XXXX`).
   - Tích hợp dấu vân tay mật mã SHA-256 niêm phong toàn vẹn dữ liệu: Họ tên, số CCCD, ngành đào tạo, năm tốt nghiệp, xếp loại, đơn vị cấp bằng.
   - Cơ chế xác thực tức thời qua số hiệu văn bằng và số Căn cước công dân (CCCD).
6. **Lưu trữ SQLite WAL**: Bảng `educational_institutions`, `institutional_accreditations`, `enrollment_quotas`, `digital_degrees` tại `.mekong/education.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan telemetry giáo dục, kiểm định chất lượng, chỉ tiêu tuyển sinh và văn bằng số
mekong education

# Thẩm tra điều kiện đầu tư và cấp phép thành lập cơ sở giáo dục (Nghị định 125/2024/NĐ-CP)
mekong education license "Trường Đại học Công nghệ & Trí tuệ Nhân tạo Mekong" --type UNIVERSITY --tax-id "0109988771" --capital 1200000000000 --land 60000 --address "Khu Công nghệ cao, TP. Thủ Đức, TP. HCM"

# Kiểm định chất lượng cơ sở GDĐH theo 25 tiêu chuẩn, 111 tiêu chí (Thông tư 12/2017/TT-BGDĐT)
mekong education accredit "Trường Đại học Quốc tế Mekong" 12000 650 260 40000 --score 4.8 --passed 105 --year 2026

# Xác định chỉ tiêu tuyển sinh hàng năm theo năng lực giảng viên và mặt bằng (Thông tư 03/2022/TT-BGDĐT)
mekong education quota "Trường Đại học Quốc tế Mekong" "Khoa học Dữ liệu & Trí tuệ Nhân tạo" --level BACHELOR --faculty 35 --floor 8000 --year 2026

# Cấp văn bằng tốt nghiệp điện tử có số hiệu quốc gia và chữ ký mã hóa (Thông tư 21/2019/TT-BGDĐT)
mekong education degree "Nguyễn Văn An" "22IT0108" "079099001234" "Khoa học Máy tính" --type BACHELOR --year 2026 --rank "XUẤT SẮC" --institution "Trường Đại học Quốc tế Mekong"

# Tra cứu xác thực tính hợp pháp của văn bằng tốt nghiệp trên cơ sở dữ liệu quốc gia
mekong education verify "VB-2026-ABCD1234" "079099001234"

# Tra cứu danh mục hồ sơ giáo dục
mekong education list institutions
mekong education list accreditations
mekong education list quotas
mekong education list degrees

# Xuất báo cáo trạng thái hệ thống định dạng JSON
mekong education status --json
```

---

## MCP Tools Integration

| Tool Name | Engine Method | Mục Tiêu & Mô Tả Nghiệp Vụ |
|---|---|---|
| `mekong_education_license` | `license_institution` | Thẩm tra điều kiện vốn đầu tư, diện tích đất và cấp phép thành lập cơ sở GD (NĐ 125/2024). |
| `mekong_education_accredit` | `audit_accreditation` | Kiểm định chất lượng cơ sở GDĐH theo 25 tiêu chuẩn, 111 tiêu chí, STR và tỷ lệ tiến sĩ (TT 12/2017). |
| `mekong_education_quota` | `calculate_enrollment_quota` | Xác định chỉ tiêu tuyển sinh hàng năm theo năng lực giảng viên và diện tích sàn (TT 03/2022). |
| `mekong_education_degree` | `issue_degree_certificate` | Cấp văn bằng tốt nghiệp điện tử có số hiệu quốc gia và chữ ký mật mã SHA-256 (TT 21/2019). |
| `mekong_education_verify` | `verify_degree_authenticity` | Tra cứu và xác thực tính hợp pháp, phát hiện văn bằng giả mạo qua số hiệu và CCCD. |
| `mekong_education_list` | `list_*` | Tra cứu danh mục cơ sở GD, đợt kiểm định, chỉ tiêu tuyển sinh và sổ cấp phát văn bằng. |
| `mekong_education_status` | `get_status` | Báo cáo telemetry tổng hợp hệ thống giáo dục quốc gia, kiểm định chất lượng và văn bằng số. |

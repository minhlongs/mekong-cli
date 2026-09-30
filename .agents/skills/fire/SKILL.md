---
name: fire
description: Vietnamese Fire Prevention, Safety, Rescue & Engineering Standards Suite.
---

# mekong fire — Autonomous Vietnamese Fire Prevention, Safety & Rescue Standards Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Phòng cháy và chữa cháy 2001 & Luật sửa đổi, bổ sung 2013 (Luật số 40/2013/QH13)**:
   - Thống nhất quản lý phòng ngừa cháy nổ, cứu nạn cứu hộ và bảo vệ an toàn tính mạng, tài sản của nhân dân và doanh nghiệp.
   - Thẩm quyền quản lý nhà nước: **Bộ Công an (Cục Cảnh sát PCCC và CNCH, Công an các tỉnh, thành phố trực thuộc Trung ương)**.
   - Trách nhiệm của chủ đầu tư, chủ cơ sở: Phải tổ chức thẩm duyệt thiết kế PCCC trước khi thi công và nghiệm thu PCCC trước khi đưa công trình vào sử dụng.
2. **Nghị định số 136/2020/NĐ-CP & Nghị định số 50/2024/NĐ-CP (hiệu lực từ 15/05/2024)**:
   - Phân cấp thẩm quyền thẩm duyệt thiết kế và nghiệm thu PCCC đối với công trình xây dựng (Phụ lục V).
   - **Thẩm duyệt thiết kế về PCCC (Điều 13, 14)**: Bắt buộc đối với nhà cao tầng, chung cư, khách sạn, vũ trường/karaoke, trung tâm thương mại, nhà xưởng công nghiệp.
   - **Nghiệm thu về PCCC (Điều 15)**: Thử nghiệm thực tế hệ thống cấp nước chữa cháy (áp lực $\ge 0.4\text{ MPa}$), máy phát điện dự phòng ($\le 15\text{s}$), hệ thống hút khói sự cố, đèn chiếu sáng sự cố và cửa thoát nạn mở theo chiều thoát.
   - **Kiểm định phương tiện PCCC (Điều 38)**: Cấp Giấy chứng nhận kiểm định và dán tem kiểm định PCCC đối với bình chữa cháy, vòi chữa cháy, đầu phun Sprinkler, van báo động, sơn chống cháy kết cấu thép.
   - **Điều kiện kinh doanh dịch vụ PCCC (Điều 41)**:
     * Người đứng đầu có Chứng chỉ bồi dưỡng kiến thức về PCCC.
     * Tối thiểu 01 cá nhân có Chứng chỉ hành nghề tư vấn thiết kế, giám sát hoặc chỉ huy thi công PCCC.
     * Địa điểm, cơ sở vật chất, phương tiện thiết bị chuyên dùng bảo đảm hoạt động.
3. **Quy chuẩn kỹ thuật quốc gia QCVN 06:2022/BXD & Sửa đổi 1:2023 QCVN 06:2022/BXD**:
   - Quy chuẩn an toàn cháy cho nhà và công trình: Phân hạng nguy hiểm cháy và cháy nổ, bậc chịu lửa của công trình (Bậc I, II, III), giải pháp ngăn cháy lan, buồng thang bộ thoát hiểm loại N1, N2, N3.
   - Tiêu chuẩn TCVN 3890:2023 về trang bị phương tiện PCCC cho nhà và công trình.
4. **Nghị định số 144/2021/NĐ-CP**:
   - Phạt 40.000.000 - 50.000.000 VND và tạm đình chỉ hoạt động cơ sở đối với hành vi đưa công trình vào sử dụng khi chưa có văn bản chấp thuận kết quả nghiệm thu về PCCC.
   - Phạt 30.000.000 - 50.000.000 VND đối với hành vi thi công không có thẩm duyệt thiết kế PCCC.
5. **Lưu trữ SQLite WAL**: Bảng `fire_design_approvals`, `fire_acceptance_inspections`, `fire_equipment_verifications`, `fire_service_licenses` tại `.mekong/fire.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động an toàn PCCC, thẩm duyệt thiết kế và nghiệm thu
mekong fire

# Thẩm duyệt thiết kế PCCC theo QCVN 06:2022/BXD và Nghị định 136/2020 / NĐ 50/2024
mekong fire design "Tòa nhà Văn phòng & Thương mại Mekong Tower" --type COMMERCIAL_BUILDING --floors 18 --area 15000 --class CLASS_I --sprinkler --alarm --smoke

# Nghiệm thu công trình an toàn PCCC trước khi đưa vào hoạt động (Điều 15 NĐ 136/2020)
mekong fire accept "Chung cư Cao cấp Mekong Riverside" --pressure 0.45 --switch-sec 12 --smoke-ok --exit-ok --non-operational

# Kiểm định phương tiện PCCC và cấp tem kiểm định Bộ Công an (Điều 38 NĐ 136/2020)
mekong fire equip "EXT-2026-8888" --type EXTINGUISHER_ABC_4KG --mfr "Công ty Thiết bị PCCC Mekong" --pressure 14.0 --tested

# Thẩm tra điều kiện kinh doanh dịch vụ phòng cháy chữa cháy (Điều 41 NĐ 136/2020)
mekong fire license "Công ty CP Kỹ thuật An toàn PCCC Sài Gòn" --director "KS. Trần Anh Tuấn" --director-cert --engineers 3 --facility --scope DESIGN_AND_SUPERVISION

# Tra cứu danh mục hồ sơ thẩm duyệt, nghiệm thu, kiểm định hoặc giấy phép PCCC
mekong fire list designs
mekong fire list acceptances
mekong fire list equipments
mekong fire list licenses

# Báo cáo telemetry an toàn PCCC dạng JSON
mekong fire status --json
```

---

## MCP Tools Integration

- `mekong_fire_design`: Thẩm duyệt thiết kế PCCC theo QCVN 06:2022/BXD và Nghị định 136/2020 / NĐ 50/2024.
- `mekong_fire_accept`: Nghiệm thu an toàn PCCC thực tế công trình trước khi đưa vào khai thác sử dụng.
- `mekong_fire_equip`: Kiểm định phương tiện PCCC và cấp mã tem kiểm định phương tiện PCCC Bộ Công an.
- `mekong_fire_license`: Thẩm định điều kiện cấp phép hoạt động kinh doanh dịch vụ PCCC theo Điều 41.
- `mekong_fire_list`: Tra cứu danh mục hồ sơ thẩm duyệt, biên bản nghiệm thu, kiểm định hoặc cấp phép PCCC.
- `mekong_fire_status`: Báo cáo chỉ số telemetry tổng hợp hệ sinh thái an toàn phòng cháy chữa cháy quốc gia.

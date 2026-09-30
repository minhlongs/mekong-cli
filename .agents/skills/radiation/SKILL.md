---
name: radiation
description: Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Suite.
---

# mekong radiation — Autonomous Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Năng lượng nguyên tử 2008 (Luật số 18/2008/QH12)**:
   - Thống nhất quản lý an toàn bức xạ, an ninh nguồn phóng xạ, khai báo, đăng ký, cấp phép và thanh sát hạt nhân trên toàn lãnh thổ Việt Nam.
   - Thẩm quyền quản lý nhà nước: **Cục An toàn bức xạ và hạt nhân (VARANS - Bộ Khoa học và Công nghệ)** và Sở Khoa học và Công nghệ các tỉnh, thành phố trực thuộc Trung ương.
2. **Nghị định số 142/2020/NĐ-CP (Tiến hành công việc bức xạ và dịch vụ hỗ trợ ứng dụng NLNT)**:
   - Quy định chi tiết điều kiện cấp Giấy phép tiến hành công việc bức xạ (sử dụng thiết bị bức xạ, nguồn phóng xạ kín, nguồn phóng xạ hở, xử lý chất thải phóng xạ).
   - Điều kiện bắt buộc:
     * Người đứng đầu cơ sở phải bổ nhiệm **Người phụ trách an toàn bức xạ** có Chứng chỉ nhân viên bức xạ do Cục ATBXHN cấp (Điều 27 Luật NLNT).
     * Phải xây dựng và được cơ quan có thẩm quyền phê duyệt Kế hoạch ứng phó sự cố bức xạ cấp cơ sở (Điều 82).
     * Cơ sở vật chất, buồng chiếu, kho lưu giữ nguồn phóng xạ phải đáp ứng các tiêu chuẩn che chắn bức xạ, suất liều ngoài phòng chiếu không vượt quá $0.5\ \mu\text{Sv/h}$.
     * Thời hạn giấy phép: 03 năm đối với sử dụng thiết bị bức xạ, nguồn phóng xạ.
3. **Thông tư số 19/2012/TT-BKHCN (Kiểm soát và bảo đảm an toàn bức xạ trong chiếu xạ nghề nghiệp và công chúng)**:
   - Giới hạn liều hiệu dụng đối với nhân viên bức xạ:
     * Không quá $20\text{ mSv/năm}$ tính trung bình trong 5 năm liên tục.
     * Không quá $50\text{ mSv}$ trong một năm bất kỳ.
   - Giới hạn liều đối với công chúng: Không quá $1\text{ mSv/năm}$.
   - Đo đọc liều kế cá nhân (Personal Dosimeter): Bắt buộc thực hiện định kỳ tối thiểu 3 tháng/lần ($4\text{ lần/năm}$).
4. **Quyết định số 446/QĐ-BKHCN (An ninh nguồn phóng xạ & thiết bị NDT di động)**:
   - Đối với các nguồn phóng xạ di động dùng trong kiểm tra không phá hủy (NDT) như Ir-192, Co-60, Cs-137:
     * Bắt buộc phải gắn thiết bị giám sát hành trình GPS truyền dữ liệu thời gian thực 24/7 về Trung tâm điều hành của Cục ATBXHN.
     * Cảnh báo khẩn cấp khi nguồn phóng xạ di chuyển ra ngoài phạm vi cấp phép hoặc mất tín hiệu kết nối.
5. **Thông tư liên tịch số 13/2014/TTLT-BKHCN-BYT (An toàn bức xạ trong y tế)**:
   - Quy chuẩn phòng đặt máy chụp X-quang, CT Scanner, máy xạ trị gia tốc (Linac):
     * Chiều dày chì che chắn phòng: Tối thiểu $2.0\text{ mm Pb}$ (đối với X-quang chẩn đoán thông thường, CT Scanner); tối thiểu $1.0\text{ mm Pb}$ (đối với máy chụp răng Dental X-ray).
     * Kiểm định định kỳ thiết bị bức xạ y tế: 1 năm/lần (riêng máy chụp răng 2 năm/lần).
     * Bắt buộc có đèn báo phát tia và biển cảnh báo nguy hiểm phóng xạ ngoài cửa phòng chiếu.
6. **Lưu trữ SQLite WAL**: Bảng `radiation_facility_licenses`, `personal_dosimetry_records`, `radioactive_source_security_audits`, `medical_xray_qa_inspections` tại `.mekong/radiation.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan an toàn bức xạ, cấp phép cơ sở và an ninh nguồn phóng xạ
mekong radiation

# Thẩm tra điều kiện cấp Giấy phép tiến hành công việc bức xạ (Nghị định 142/2020/NĐ-CP)
mekong radiation license "Bệnh viện Đa khoa Quốc tế Mekong" --fac-type HOSPITAL_RADIOLOGY --equipment CT_SCANNER --officer --emergency --shielding --signs --leak-rate 0.25

# Ghi nhận và đánh giá kết quả đo liều kế cá nhân (Thông tư 19/2012/TT-BKHCN)
mekong radiation dose "Nguyễn Văn Hùng" --id "NV-RAD-042" --facility "Bệnh viện K" --quarter 1 --year 2026 --dose 1.2 --cumulative 4.5 --days 90

# Giám sát an ninh nguồn phóng xạ và thiết bị định vị GPS (Quyết định 446/QĐ-BKHCN)
mekong radiation source "SRC-IR192-8842" --isotope IR-192 --init-act 80.0 --cur-act 42.5 --type INDUSTRIAL_NDT --gps --signal --perimeter --vault

# Kiểm định định kỳ và đảm bảo chất lượng (QA) máy X-quang y tế (TTLT 13/2014)
mekong radiation xray "Phòng khám Đa khoa Hoàn Mỹ" --model "Siemens Multix Impact" --type CONVENTIONAL_XRAY --kvp 3.2 --timer 2.8 --lead 2.0 --months 6 --light

# Tra cứu lịch sử cấp phép, hồ sơ liều và kiểm định an toàn bức xạ
mekong radiation list all --limit 20
```

---

## FastMCP & JSON-RPC Tools
- `mekong_radiation_license(facility_name, facility_type, equipment_type, safety_officer_certified, emergency_plan_approved, storage_shielding_compliant, has_warning_signs, radiation_leak_dose_rate_uSv_h)`
- `mekong_radiation_dose(employee_name, employee_id, facility_name, quarter, year, effective_dose_mSv, cumulative_annual_dose_mSv, wearing_period_days)`
- `mekong_radiation_source(source_serial, isotope, initial_activity_curie, current_activity_curie, application_type, has_gps_tracker, gps_signal_active, within_authorized_perimeter, storage_vault_secured)`
- `mekong_radiation_xray(clinic_name, machine_model, machine_type, kvp_accuracy_pct, timer_accuracy_pct, lead_shielding_thickness_mm, last_inspection_months_ago, warning_light_operational)`
- `mekong_radiation_list(category, limit)`
- `mekong_radiation_status()`

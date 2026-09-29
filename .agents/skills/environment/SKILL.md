---
name: environment
description: Vietnamese Environmental Protection, EIA Impact Classification, GPMT, Carbon Credits & EPR Suite.
---

# mekong environment — Autonomous Vietnamese Environmental Protection, EIA & Carbon Credits Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Bảo vệ môi trường 2020 (Luật số 72/2020/QH14)**:
   - Hiệu lực thi hành từ ngày 01/01/2022, cải cách toàn diện chính sách bảo vệ môi trường, kiểm soát ô nhiễm và chuyển dịch kinh tế tuần hoàn.
   - Cơ quan quản lý nhà nước: **Bộ Tài nguyên và Môi trường (Bộ TN&MT)** và Ủy ban nhân dân các cấp.
2. **Phân loại dự án đầu tư theo mức độ tác động môi trường (Điều 28 Luật BVMT 2020 & Nghị định 08/2022/NĐ-CP)**:
   - **Nhóm I (Nguy cơ tác động xấu mức độ cao)**: Dự án quy mô lớn, có yếu tố nhạy cảm môi trường cao (rừng đặc dụng, nguồn nước sinh hoạt) hoặc loại hình công nghiệp ô nhiễm công suất lớn. Bắt buộc: Đánh giá sơ bộ tác động môi trường + Đánh giá tác động môi trường (ĐTM) chi tiết do Bộ TN&MT thẩm định. Thời hạn Giấy phép Môi trường (GPMT) là **07 năm**.
   - **Nhóm II (Nguy cơ tác động xấu)**: Quy mô trung bình hoặc quy mô nhỏ có yếu tố nhạy cảm môi trường. Bắt buộc: Báo cáo ĐTM do UBND cấp tỉnh thẩm định. Thời hạn GPMT là **10 năm**.
   - **Nhóm III (Ít nguy cơ tác động xấu)**: Quy mô nhỏ, phát sinh chất thải phải xử lý đạt chuẩn. Miễn ĐTM; bắt buộc cấp Giấy phép Môi trường (thời hạn 10 năm) hoặc Đăng ký môi trường.
   - **Nhóm IV (Không có nguy cơ tác động xấu)**: Không phát sinh chất thải hoặc chỉ phát sinh chất thải sinh hoạt nhỏ (< 300 kg/ngày). Miễn lập ĐTM, miễn Giấy phép Môi trường, miễn Đăng ký môi trường.
3. **Giấy phép Môi trường (GPMT) tích hợp (Điều 39 - Điều 49 Luật BVMT 2020)**:
   - Tích hợp 7 loại giấy phép thành phần cũ thành 1 văn bản duy nhất (xả nước thải, xả khí thải, xả thải vào công trình thủy lợi, quản lý chất thải nguy hại, nhập khẩu phế liệu,...).
   - Quy định trần hạn mức xả thải: Lưu lượng xả nước thải ($m^3/\text{ngày-đêm}$), lưu lượng xả khí thải ($m^3/\text{giờ}$), khối lượng chất thải nguy hại phát sinh (tấn/năm).
4. **Kiểm kê Khí nhà kính (GHG) & Bù trừ Tín chỉ Carbon (Nghị định số 06/2022/NĐ-CP)**:
   - Áp dụng kiểm kê bắt buộc đối với cơ sở phát thải từ **$3,000\text{ tấn } CO_2e/\text{năm}$ trở lên** hoặc tiêu thụ năng lượng $\ge 1,000\text{ TOE}$.
   - Kiểm kê toàn diện: Scope 1 (đốt nhiên liệu trực tiếp), Scope 2 (tiêu thụ điện lưới - Hệ số phát thải lưới $EF \approx 0.7221\text{ tCO}_2e/\text{MWh}$), Scope 3 (chuỗi cung ứng gián tiếp).
   - Cơ chế hạn ngạch phát thải (Cap-and-Trade) và bù trừ tín chỉ carbon ($1\text{ credit} = 1\text{ tCO}_2e$).
5. **Trách nhiệm mở rộng của nhà sản xuất (EPR) (Điều 54, 55 Luật BVMT 2020 & Nghị định 08/2022/NĐ-CP)**:
   - Tỷ lệ tái chế bắt buộc: Bao bì giấy ($20\%$), Bao bì nhựa PET/HDPE ($22\%$), Lon nhôm ($22\%$), Pin/ắc quy ($12\%$), Dầu nhớt ($7\%$), Săm lốp ($5\%$), Điện tử ($9\%$).
   - Nếu không tự tái chế, doanh nghiệp bắt buộc đóng góp tài chính vào **Quỹ Bảo vệ môi trường Việt Nam (VEPF)** theo định mức chi phí tái chế $Fs$ (VND/kg).
6. **Quan trắc môi trường tự động, liên tục & Giám sát QCVN**:
   - Đối chiếu ngưỡng kỹ thuật quốc gia: QCVN 40:2011/BTNMT (Nước thải công nghiệp: pH $6.0 - 9.0$, COD $\le 75\text{ mg/L}$, TSS $\le 50\text{ mg/L}$, Nhiệt độ $\le 40^\circ\text{C}$).
   - QCVN 19:2009/BTNMT (Khí thải công nghiệp: Bụi $\le 200\text{ mg/Nm}^3$, $SO_2 \le 500\text{ mg/Nm}^3$, $NO_x \le 850\text{ mg/Nm}^3$, $CO \le 1,000\text{ mg/Nm}^3$).
7. **Lưu trữ SQLite WAL**: Bảng `project_impacts`, `environmental_licenses`, `ghg_audits`, `epr_declarations`, `monitoring_audits` tại `.mekong/environment.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan telemetry môi trường, phân loại ĐTM, GPMT, KNK và trách nhiệm EPR
mekong environment

# Phân loại mức độ tác động môi trường của dự án (Nhóm I, II, III, IV) theo Điều 28
mekong environment classify "Nhà máy Thép Xanh Mekong" "Tập đoàn Luyện kim Mekong" 500000000000 --sector STEEL_METALLURGY --location "Bà Rịa - Vũng Tàu" --sensitive --capacity 500000 --unit "tấn/năm"

# Cấp Giấy phép Môi trường (GPMT) tích hợp theo Điều 39-49 Luật BVMT 2020
mekong environment license "Nhà máy Sản xuất Linh kiện Điện tử Mekong" "0109988334" "KCN VSIP 1, Bình Dương" --group GROUP_II --wastewater 800 --exhaust 25000 --hazardous-waste 15

# Kiểm kê phát thải khí nhà kính (GHG) Scope 1/2/3 và tính bù trừ tín chỉ carbon (Nghị định 06/2022)
mekong environment ghg "Tổ hợp Hóa chất Mekong" --year 2026 --scope1 2500 --electricity 4000000 --scope3 400 --quota 5000 --offset-credits 300

# Kê khai trách nhiệm mở rộng nhà sản xuất (EPR) và tính toán nộp quỹ VEPF (Nghị định 08/2022)
mekong environment epr "Công ty CP Nước giải khát Mekong" "0301122334" --product PACKAGING_PLASTIC_PET --volume 500000 --recycled 50000

# Giám sát số liệu trạm quan trắc tự động liên tục đối chiếu với QCVN 40 và QCVN 19
mekong environment monitor "Trạm Xử lý Nước thải KCN Mekong" --type WASTEWATER --ph 7.4 --cod 55 --tss 35 --temp 31

# Tra cứu danh mục hồ sơ môi trường
mekong environment list --type projects
mekong environment list --type licenses
mekong environment list --type ghg
mekong environment list --type epr
mekong environment list --type monitors

# Xuất báo cáo trạng thái hệ thống định dạng JSON
mekong environment status --json
```

---

## MCP Tools Integration

| Tool Name | Engine Method | Mục Tiêu & Mô Tả Nghiệp Vụ |
|---|---|---|
| `mekong_environment_classify` | `classify_project_impact` | Phân loại dự án đầu tư theo 4 nhóm tác động môi trường và xác định thẩm quyền phê duyệt ĐTM/GPMT. |
| `mekong_environment_license` | `issue_environmental_license` | Cấp Giấy phép Môi trường (GPMT) tích hợp và thiết lập hạn mức xả nước thải, khí thải, chất thải nguy hại. |
| `mekong_environment_ghg` | `audit_ghg_emissions` | Kiểm kê phát thải khí nhà kính Scope 1/2/3, đánh giá hạn ngạch phát thải và bù trừ tín chỉ carbon. |
| `mekong_environment_epr` | `calculate_epr_obligations` | Tính toán tỷ lệ tái chế bắt buộc (EPR) và số tiền đóng góp Quỹ Bảo vệ Môi trường Việt Nam (VEPF). |
| `mekong_environment_monitor` | `audit_monitoring_telemetry` | Kiểm toán số liệu quan trắc tự động liên tục nước thải/khí thải đối chiếu với QCVN 40 và QCVN 19. |
| `mekong_environment_list` | `list_*` | Tra cứu danh mục dự án ĐTM, Giấy phép Môi trường, kiểm kê KNK, khai báo EPR và nhật ký quan trắc. |
| `mekong_environment_status` | `get_status` | Báo cáo telemetry tổng hợp bảo vệ môi trường, kiểm soát ô nhiễm, thị trường carbon và quỹ VEPF. |

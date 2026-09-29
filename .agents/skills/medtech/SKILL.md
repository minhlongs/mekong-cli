---
name: medtech
description: Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trial Compliance.
---

# 🩺 MedTech — Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials

Autonomous operations engine for Vietnamese medical device risk classification (Classes A, B, C, D), market authorization (Số lưu hành), price declarations under Decree 98/2021/NĐ-CP & Decree 07/2023/NĐ-CP, healthcare facility operating licenses under the Law on Medical Examination and Treatment 2023 (Law 15/2023/QH15) & Decree 96/2023/NĐ-CP, and clinical trial ethics evaluation under Circular 29/2023/TT-BYT.

## Statutory Legal Framework

1. **Nghị định 98/2021/NĐ-CP & Nghị định 07/2023/NĐ-CP về Quản lý Trang thiết bị y tế**:
   - **Phân loại 4 nhóm rủi ro (Risk Classes)** theo Thông tư 05/2022/TT-BYT:
     * **Loại A** (Rủi ro rất thấp): Bông băng, gạc y tế, nhiệt kế cơ học, găng tay khám bệnh $\rightarrow$ Công bố tiêu chuẩn áp dụng tại Sở Y tế. Hiệu lực vô thời hạn.
     * **Loại B** (Rủi ro trung bình thấp): Máy đo huyết áp điện tử, kim tiêm, máy siêu âm cơ bản $\rightarrow$ Công bố tiêu chuẩn áp dụng tại Sở Y tế. Hiệu lực vô thời hạn.
     * **Loại C** (Rủi ro trung bình cao): Máy thở, máy X-quang, dao mổ điện cao tần, máy lọc thận $\rightarrow$ Đăng ký cấp số lưu hành tại Bộ Y tế (Cục Cơ sở hạ tầng & Thiết bị y tế). Hiệu lực 5 năm.
     * **Loại D** (Rủi ro cao / cấy ghép lâu dài): Stent nong mạch vành, van tim nhân tạo, máy tạo nhịp tim cấy ghép, khớp háng nhân tạo $\rightarrow$ Đăng ký cấp số lưu hành tại Bộ Y tế. Hiệu lực 5 năm.
   - **Fast-Track Miễn Trừ Thử Nghiệm Lâm Sàng (CFS Tham Chiếu Quốc Tế)**:
     * Miễn thử nghiệm lâm sàng nếu đã được cấp Giấy chứng nhận lưu hành tự do (CFS) từ 1 trong 5 cơ quan tham chiếu quốc tế:
       - **US FDA** (Hoa Kỳ)
       - **CE Mark** (Liên minh Châu Âu - EU)
       - **PMDA** (Nhật Bản)
       - **TGA** (Úc)
       - **Health Canada** (Canada)

2. **Kê Khai Giá & Khống Chế Biên Lợi Nhuận Trang Thiết Bị Y Tế (Nghị định 07/2023/NĐ-CP)**:
   - Doanh nghiệp sản xuất/nhập khẩu bắt buộc kê khai giá bán lẻ, giá bán buôn trên Cổng thông tin điện tử Bộ Y tế.
   - Kiểm soát biên độ lợi nhuận bán buôn định mức $\text{Markup} = \frac{P_{\text{wholesale}} - P_{\text{CIF}}}{P_{\text{CIF}}} \times 100\% \le 35\%$.
   - Minh bạch giá trúng thầu mua sắm công lập theo Luật Đấu thầu 2023.

3. **Cấp Giấy Phép Hoạt Động Cơ Sở Khám Bệnh, Chữa Bệnh (Luật 15/2023/QH15 & Nghị định 96/2023/NĐ-CP)**:
   - **Bệnh viện đa khoa (`GENERAL_HOSPITAL`)**: Quy mô tối thiểu 30 giường bệnh, diện tích sàn tối thiểu $50\text{ m}^2/\text{giường}$, đủ các khoa Nội, Ngoại, Sản, Nhi, Cấp cứu, Chẩn đoán hình ảnh, Xét nghiệm. Bác sĩ phụ trách chuyên môn có chứng chỉ hành nghề (CCHN) tối thiểu 54 tháng.
   - **Bệnh viện chuyên khoa (`SPECIALIZED_HOSPITAL`)**: Tối thiểu 20 giường bệnh, $45\text{ m}^2/\text{giường}$.
   - **Phòng khám đa khoa (`POLYCLINIC`)**: Tối thiểu 2 phòng khám chuyên khoa, phòng cấp cứu, buồng tiểu phẫu, xét nghiệm, CĐHA. Bác sĩ phụ trách có CCHN $\ge 36\text{ tháng}$.
   - **Phòng khám chuyên khoa (`SPECIALIZED_CLINIC`)**: Bác sĩ phụ trách có CCHN phù hợp chuyên khoa $\ge 36\text{ tháng}$.

4. **Thử Nghiệm Lâm Sàng Trang Thiết Bị Y Tế (Thông tư 29/2023/TT-BYT)**:
   - Đề cương nghiên cứu phải được Hội đồng Đạo đức trong nghiên cứu y sinh học (IRB) quốc gia hoặc cơ sở thẩm định và phê duyệt.
   - 3 giai đoạn nghiên cứu: Đánh giá sơ bộ tính an toàn $\rightarrow$ Đánh giá hiệu quả lâm sàng nhóm đích $\rightarrow$ Thử nghiệm đa trung tâm đối chứng.

---

## CLI Usage

```bash
# Báo cáo tổng quan ngành thiết bị y tế & cơ sở khám chữa bệnh
mekong medtech status
mekong medtech status --json

# Phân loại rủi ro & đăng ký số lưu hành trang thiết bị y tế
mekong medtech device "Máy siêu âm màu Doppler 4D" --class CLASS_B --maker "GE Healthcare" --origin "USA" --importer "Công ty TNHH MedTech VN" --cfs FDA --json

# Kê khai giá trang thiết bị y tế & kiểm soát biên lợi nhuận
mekong medtech price DEV-12345678 "Máy siêu âm 4D" --cif 500000000 --wholesale 650000000 --retail 750000000 --json

# Thẩm định điều kiện cấp giấy phép hoạt động bệnh viện / phòng khám
mekong medtech facility "Bệnh viện Đa khoa Quốc tế Mekong" --type GENERAL_HOSPITAL --province "TP. Hồ Chí Minh" --beds 150 --area 8500 --cmo "PGS.TS. Lê Văn An" --months 72 --json

# Đăng ký đề cương thử nghiệm lâm sàng trang thiết bị y tế
mekong medtech trial DEV-12345678 "Thử nghiệm lâm sàng Stent phủ thuốc thế hệ mới" --phase 3 --pi "GS.TS. Nguyễn Hữu Dũng" --site "Bệnh viện Chợ Rẫy" --subjects 200 --irb --json

# Tra cứu dữ liệu thiết bị, giá kê khai, cơ sở y tế, thử nghiệm lâm sàng
mekong medtech list devices --limit 50 --json
mekong medtech list prices --json
mekong medtech list facilities --json
mekong medtech list trials --json
```

---

## MCP Tools

| MCP Tool | Description |
|---|---|
| `mekong_medtech_device` | Register medical device risk class (A/B/C/D), market authorization, and reference CFS exemption. |
| `mekong_medtech_price` | Declare medical device prices and monitor wholesale markup compliance ($\le 35\%$). |
| `mekong_medtech_facility` | Evaluate healthcare facility operating license conditions (beds, area/bed, CMO qualifications). |
| `mekong_medtech_trial` | Register clinical evaluation trial protocol and ethics IRB approval under Circular 29/2023/TT-BYT. |
| `mekong_medtech_list` | Query registered devices, price declarations, healthcare facilities, or clinical trials. |
| `mekong_medtech_status` | Retrieve aggregate Vietnamese MedTech & healthcare facility licensing telemetry. |

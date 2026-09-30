---
name: crop
description: Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Suite.
---

# mekong crop — Autonomous Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Trồng trọt 2018 (Luật số 31/2018/QH14)**:
   - Thống nhất quản lý giống cây trồng, phân bón, canh tác nông nghiệp, thu hoạch, bảo quản và truy xuất nguồn gốc nông sản.
   - Thẩm quyền quản lý chuyên ngành: **Cục Trồng trọt** và **Cục Bảo vệ thực vật** (Bộ Nông nghiệp và Phát triển nông thôn).
2. **Quy chuẩn Cấp Mã số vùng trồng (PUC - Planting Area Code)**:
   - Căn cứ Tiêu chuẩn cơ sở TCCS 774:2020/BVTV và các Nghị định thư xuất khẩu chính ngạch sang Trung Quốc (GACC), Hoa Kỳ (APHIS), EU, Nhật Bản:
     * Diện tích canh tác tập trung tối thiểu: $\ge 10\text{ ha}$ đối với sầu riêng, thanh long, xoài; $\ge 15\text{ ha}$ đối với chuối; $\ge 20\text{ ha}$ đối với lúa gạo xuất khẩu.
     * Bắt buộc có Nhật ký canh tác số (Digital Farming Log) ghi chép chi tiết thời điểm bón phân, tưới tiêu, phun thuốc BVTV và thu hoạch.
     * Tuân thủ quy trình kiểm soát sinh vật gây hại (ruồi đục quả, rệp sáp, nấm Phytophthora...).
3. **Luật Bảo vệ và Kiểm dịch thực vật 2013 (Luật số 41/2013/QH13)**:
   - Quản lý phòng chống dịch hại thực vật, kiểm dịch thực vật nhập khẩu, xuất khẩu và quá cảnh.
   - Cấp Giấy chứng nhận kiểm dịch thực vật (Phytosanitary Certificate) sau khi hoàn thành giám định kiểm dịch và xác nhận biện pháp xử lý kiểm dịch (xử lý hơi nước nóng VHT, xử lý nước nóng HWT, chiếu xạ Irradiation hoặc hun trùng Methyl Bromide).
4. **Thông tư số 21/2015/TT-BNNPTNT & Thông tư số 09/2023/TT-BNNPTNT (Quản lý thuốc BVTV)**:
   - Danh mục thuốc bảo vệ thực vật được phép sử dụng và cấm sử dụng tại Việt Nam:
     * **Cấm tuyệt đối**: Paraquat, Chlorpyrifos Ethyl, Glyphosate, 2,4-D, Carbofuran, Acephate, Trichlorfon...
     * Kiểm soát nghiêm ngặt thời gian cách ly (PHI - Pre-Harvest Interval) trước khi thu hoạch nhằm đảm bảo dư lượng không vượt ngưỡng MRL (Maximum Residue Limit).
5. **Điều kiện Buôn bán Thuốc BVTV (Điều 63 Luật BV&KDTV 2013 & NĐ 31/2023/NĐ-CP)**:
   - Người trực tiếp quản lý, buôn bán phải có chứng chỉ hành nghề hoặc bằng cấp chuyên ngành nông lâm nghiệp.
   - Kho chứa thuốc phải cách xa nguồn nước sinh hoạt, trường học, bệnh viện tối thiểu $\ge 50\text{m}$, có hệ thống thông gió và gờ ngăn chống rò rỉ hóa chất.
6. **Lưu trữ SQLite WAL**: Bảng `planting_area_code_audits`, `pesticide_compliance_checks`, `phytosanitary_certificates`, `pesticide_store_licenses` tại `.mekong/crop.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan mã số vùng trồng, kiểm tra thuốc BVTV và kiểm dịch thực vật
mekong crop

# Thẩm định điều kiện cấp Mã số vùng trồng (PUC) xuất khẩu (TCCS 774:2020/BVTV)
mekong crop puc "HTX Sầu riêng Krông Pắc" --crop DURIAN_EXPORT --province "Đắk Lắk" --hectares 15.0 --households 18 --log --pesticides --monitoring --market CHINA_GACC

# Kiểm tra tính hợp pháp của hoạt chất thuốc BVTV và thời gian cách ly PHI (Thông tư 09/2023)
mekong crop pesticide "Sầu riêng" --ingredient "AZOXYSTROBIN" --dosage 0.6 --days-applied 8 --harvest-in 3

# Thẩm định và cấp Giấy chứng nhận Kiểm dịch thực vật xuất khẩu (Phyto Certificate)
mekong crop phyto "EXP-DUR-2026-99" --commodity "Sầu riêng tươi cấp đông" --weight 24.5 --province "Tiền Giang" --dest "CHINA" --treatment "VAPOR_HEAT_TREATMENT" --puc-ok

# Thẩm tra điều kiện cấp Giấy chứng nhận đủ điều kiện buôn bán thuốc BVTV (Điều 63 Luật BV&KDTV)
mekong crop store "Đại lý Vật tư Nông nghiệp Hai Lúa" --owner "Nguyễn Văn Lúa" --province "Đồng Tháp" --cert --water-dist 65.0 --vent --pccc

# Tra cứu lịch sử mã vùng trồng, kiểm tra hoạt chất và chứng thư kiểm dịch
mekong crop list all --limit 20
```

---

## Native MCP Tools Parity

- `mekong_crop_puc`: Audit planting area code (PUC) eligibility for agricultural export (Law on Crop Production 2018 & TCCS 774:2020).
- `mekong_crop_pesticide`: Check pesticide active ingredient legality, dosage, and pre-harvest interval (PHI) (Circular 09/2023/TT-BNNPTNT).
- `mekong_crop_phyto`: Inspect consignment and issue Phytosanitary Certificate under Law on Plant Protection and Quarantine 2013.
- `mekong_crop_store`: Audit retail pesticide trading store licensing conditions (Article 63 Law on Plant Protection and Quarantine 2013).
- `mekong_crop_list`: Query stored planting area codes, pesticide compliance audits, phytosanitary certificates, or store licenses.
- `mekong_crop_status`: Retrieve national crop cultivation, planting area code, export phytosanitary, and pesticide safety metrics.

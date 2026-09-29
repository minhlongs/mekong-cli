---
name: forestry
description: Vietnamese Forestry Law 2017, VNTLAS Timber Legality, FSC & Forest Carbon Sinks.
---

# 🌲 Forestry — Vietnamese Forestry Law 2017, VNTLAS Timber Legality & Forest Carbon Sinks

Autonomous operations engine for Vietnamese sustainable forest management, VNTLAS timber legality verification (Decree 102/2020/NĐ-CP & VPA/FLEGT), FSC/PEFC certification, alternative afforestation mandates under Article 21 Law on Forestry 2017 (Decree 156/2018/NĐ-CP), Payment for Forest Environmental Services (PFES), World Bank ERPA carbon emission reductions (Decree 107/2022/NĐ-CP), and meteorological forest fire danger forecasting.

## Statutory Legal Framework

1. **Luật Lâm nghiệp 2017 (Luật số 16/2017/QH14) & Nghị định 156/2018/NĐ-CP, Nghị định 91/2024/NĐ-CP**:
   - Phân loại 3 loại rừng:
     - **Rừng đặc dụng** (`SPECIAL_USE`): Vườn quốc gia, khu bảo tồn thiên nhiên, khu bảo vệ cảnh quan, rừng nghiên cứu thực nghiệm khoa học.
     - **Rừng phòng hộ** (`PROTECTION`): Phòng hộ đầu nguồn, chắn gió, chắn cát bay, chắn sóng ven biển.
     - **Rừng sản xuất** (`PRODUCTION_NATURAL`, `PRODUCTION_PLANTATION`): Cung cấp gỗ và lâm sản, kết hợp bảo vệ môi trường sinh thái.
   - **Trồng rừng thay thế khi chuyển mục đích sử dụng rừng (Điều 21)**:
     - Rừng tự nhiên: Phải trồng rừng thay thế bằng tối thiểu **3 lần** diện tích rừng tự nhiên chuyển đổi.
     - Rừng trồng: Phải trồng rừng thay thế bằng tối thiểu **1 lần** diện tích rừng trồng chuyển đổi.
     - Nộp tiền vào Quỹ Bảo vệ và Phát triển Rừng (VNFF) nếu không tự tổ chức trồng rừng mới.

2. **Hệ Thống Bảo Đảm Gỗ Hợp Pháp Việt Nam (VNTLAS - Nghị định 102/2020/NĐ-CP)**:
   - Phân loại doanh nghiệp chế biến và xuất khẩu gỗ:
     - **Nhóm I** (`TIER_1`): Tuân thủ đầy đủ pháp luật; thủ tục hải quan và hồ sơ lâm sản được phân luồng Xanh (Green Channel).
     - **Nhóm II** (`TIER_2`): Doanh nghiệp mới thành lập hoặc chưa đáp ứng đủ tiêu chí; xác minh 100% hồ sơ lâm sản và kiểm tra thực tế.
   - Cấp Giấy phép FLEGT và CITES cho lô hàng gỗ xuất khẩu sang EU, Mỹ (Lacey Act), Nhật Bản (Clean Wood Act).
   - Đáp ứng Quy định Chống phá rừng của Liên minh Châu Âu (EUDR - Regulation (EU) 2023/1115).

3. **Chứng Chỉ Quản Lý Rừng Bền Vững (FSC, PEFC & VFCS - Quyết định 1288/QĐ-TTg)**:
   - Chứng chỉ FSC-FM / PEFC-FM: Quản lý rừng bền vững.
   - Chứng chỉ FSC-CoC / PEFC-CoC: Chuỗi hành trình sản phẩm từ rừng đến xưởng chế biến xuất khẩu.

4. **Chi Trả Dịch Vụ Môi Trường Rừng (PFES) & Tín Chỉ Carbon Rừng (Nghị định 156/2018 & 107/2022/NĐ-CP)**:
   - Định mức chi trả PFES (Điều 63 Nghị định 156/2018/NĐ-CP):
     - Thủy điện: $36\text{ VND/kWh}$ điện thương phẩm.
     - Cơ sở sản xuất nước sạch: $52\text{ VND/m}^3$ nước thương phẩm.
     - Cơ sở công nghiệp dùng nước: $50\text{ VND/m}^3$.
     - Du lịch sinh thái: $1.0\% - 2.0\%$ doanh thu.
   - Thỏa thuận Chi trả Giảm phát thải (ERPA) với Ngân hàng Thế giới (World Bank): Hấp thụ carbon rừng với đơn giá \$5.0 USD/tấn $CO_2e$.

5. **Dự Báo Nguy Cơ Cháy Rừng (Nghị định 156/2018/NĐ-CP)**:
   - Cấp I (Thấp) đến Cấp V (Cực kỳ nguy hiểm) theo chỉ số khí tượng (nhiệt độ, độ ẩm, số ngày khô hạn, vận tốc gió).

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan lâm nghiệp & dịch vụ môi trường rừng
mekong forestry
mekong forestry --json

# 2. Đăng ký khu rừng / lô rừng quản lý bền vững và chứng chỉ FSC/PEFC
mekong forestry plot "Lô Rừng Trồng Keo Đại Lộc" --type PRODUCTION_PLANTATION --province "Quảng Nam" --area 150 --canopy 65 --trees-per-ha 1600 --species "Acacia auriculiformis" --fsc --fsc-code "FSC-C123456"

# 3. Thẩm tra nguồn gốc gỗ VNTLAS & cấp phép FLEGT/CITES
mekong forestry timber "Công Ty CP Gỗ An Cường" --product FURNITURE --volume 120 --species "Teak / Keo" --province "Bình Dương" --tier TIER_1 --license "FLEGT-VN-2026-00892" --market EU

# 4. Tính toán diện tích trồng rừng thay thế & nộp Quỹ VNFF
mekong forestry afforestation "Dự án Hồ Chứa Nước Thủy Lợi" --forest-type PRODUCTION_NATURAL --area 25.0 --rate 95000000

# 5. Tính chi trả dịch vụ môi trường rừng (PFES) & tín chỉ carbon ERPA
mekong forestry pfes "Thủy điện Sông Tranh 2" --type HYDROPOWER --volume 250000000 --forest-area 12000 --sequestration 4.2 --erpa-price 5.0

# 6. Dự báo cấp nguy cơ cháy rừng theo chỉ số khí tượng
mekong forestry fire "PLT-ABCD1234" --temp 37.5 --humidity 38.0 --wind 24.0 --dry-days 14

# 7. Tra cứu danh mục
mekong forestry list plots
mekong forestry list timber
mekong forestry list afforestation
mekong forestry list pfes
mekong forestry list fire
mekong forestry status
```

---

## FastMCP & JSON-RPC 2.0 Tools

- `mekong_forestry_plot`: Register forest plot with canopy coverage, species, and FSC/PEFC certification.
- `mekong_forestry_timber`: Verify timber consignment legality under VNTLAS (Decree 102/2020) and issue export manifest.
- `mekong_forestry_afforestation`: Calculate mandatory alternative afforestation area or Vietnam Forest Protection Fund (VNFF) deposit.
- `mekong_forestry_pfes`: Compute PFES obligation (Decree 156/2018) and World Bank ERPA forest carbon sequestration revenue.
- `mekong_forestry_fire`: Assess forest fire danger level (Tier I to V) based on meteorological index.
- `mekong_forestry_list`: Query registered forest plots, timber consignments, alternative afforestations, PFES records, or fire danger assessments.
- `mekong_forestry_status`: Retrieve Vietnamese forestry, VNTLAS timber, PFES, and forest carbon telemetry.

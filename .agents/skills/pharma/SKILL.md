---
name: pharma
description: Vietnamese Pharmaceutical Logistics, Drug Law 2016 (Visa MA), National Drug Bank, GSP Cold Chain Storage & Hospital Price Margins.
---

# 💊 Pharma — Vietnamese Pharmaceutical Logistics, National Drug Bank & GXP Quality Assurance

Autonomous operations engine for Vietnamese pharmaceutical marketing authorizations (Visa MA), WHO/EU-GSP cold chain environmental auditing, GS1 2D DataMatrix batch traceability, emergency drug recall management, and hospital retail markup regulation.

## Statutory Legal Framework

1. **Luật Dược 2016 (Luật số 105/2016/QH13) & Nghị định 54/2017/NĐ-CP**:
   - Quản lý cấp phép lưu hành thuốc và nguyên liệu làm thuốc (Marketing Authorization - Visa MA):
     - Định dạng mã số: `VN-XXXXX-XX` (thuốc nhập khẩu), `VD-XXXXX-XX` hoặc `GC-XXXXX-XX` (thuốc sản xuất trong nước).
     - Phân loại danh mục:
       - `RX_PRESCRIPTION`: Thuốc kê đơn (bán theo đơn của bác sĩ).
       - `OTC_NON_PRESCRIPTION`: Thuốc không kê đơn (bán lẻ tự do tại nhà thuốc).
       - `SPECIAL_CONTROL_NARCOTIC`: Thuốc gây nghiện, hướng thần, tiền chất dùng làm thuốc (chế độ kiểm soát đặc biệt).
       - `VACCINE_BIOLOGICAL`: Vắc xin và sinh phẩm y tế.
     - Thời hạn hiệu lực giấy đăng ký lưu hành thuốc: **05 năm** (hoặc **03 năm** với hồ sơ gia hạn có điều kiện).

2. **Hệ thống Tiêu chuẩn Thực hành Tốt GSP & GDP (Thông tư 36/2018/TT-BYT & Thông tư 03/2018/TT-BYT)**:
   - Thẩm định điều kiện vi khí hậu môi trường kho dược phẩm và chuỗi cung ứng lạnh (Cold Chain):
     - Kho bảo quản thường (`STANDARD_ROOM`): Nhiệt độ $15^\circ\text{C} - 30^\circ\text{C}$, độ ẩm tương đối $\le 75\%$.
     - Kho mát (`COOL_STORAGE`): Nhiệt độ $8^\circ\text{C} - 15^\circ\text{C}$, độ ẩm $\le 70\%$.
     - Kho lạnh / Chuỗi lạnh Vắc xin (`COLD_CHAIN`): Nhiệt độ $2^\circ\text{C} - 8^\circ\text{C}$, độ ẩm $\le 65\%$.
     - Kho đông sâu (`DEEP_FREEZE`): Nhiệt độ $-80^\circ\text{C}$ đến $-10^\circ\text{C}$.
   - Đo kiểm và tự động cảnh báo nhiệt độ vượt ngưỡng (Temperature Excursion Alert).

3. **Truy xuất Nguồn gốc GS1 2D DataMatrix & Thu hồi Thuốc (Quyết định 412/QĐ-BYT)**:
   - Chuẩn mã hóa 2D DataMatrix ngành y tế:
     - `(01)`: Mã toàn cầu phân định thương phẩm GTIN-14.
     - `(17)`: Hạn dùng định dạng YYMMDD.
     - `(10)`: Số lô sản xuất (Batch / Lot Number).
     - `(21)`: Mã định danh duy nhất của từng hộp thuốc (Serial Number S/N).
   - Cơ chế điều hành cảnh báo thu hồi thuốc theo quy định Bộ Y tế:
     - `LEVEL_1`: Thu hồi Cấp độ 1 (Nguy cơ tử vong hoặc tổn hại nghiêm trọng) $\to$ Hoàn thành trong vòng **24 giờ**.
     - `LEVEL_2`: Thu hồi Cấp độ 2 (Nguy cơ không nghiêm trọng) $\to$ Hoàn thành trong vòng **48 giờ**.
     - `LEVEL_3`: Thu hồi Cấp độ 3 (Sai sót nhãn mác/hình thức) $\to$ Hoàn thành trong vòng **72 giờ**.

4. **Kê khai & Niêm yết Giá thuốc (Điều 107 Luật Dược 2016 & Điều 136 Nghị định 54/2017/NĐ-CP)**:
   - Kê khai giá bán buôn dự kiến với Cục Quản lý Dược (DAV).
   - Khống chế thặng số bán lẻ tối đa của cơ sở bán lẻ thuốc trong khuôn viên cơ sở khám chữa bệnh:
     - Giá mua vào $\le 1.000\text{ VND}$: Thặng số tối đa **15.0%**.
     - Giá mua vào $1.000 - 5.000\text{ VND}$: Thặng số tối đa **10.0%**.
     - Giá mua vào $5.000 - 100.000\text{ VND}$: Thặng số tối đa **7.0%**.
     - Giá mua vào $100.000 - 1.000.000\text{ VND}$: Thặng số tối đa **5.0%**.
     - Giá mua vào $> 1.000.000\text{ VND}$: Thặng số tối đa **2.0%**.

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan ngành dược & thực hành tốt GSP
mekong pharma
mekong pharma --json

# 2. Đăng ký & tra cứu giấy phép lưu hành thuốc (Visa MA)
mekong pharma drug "VN-22019-19" "Augmentin 1g" "Amoxicillin + Clavulanic Acid" "1000mg" "Viên nén bao phim" --class RX_PRESCRIPTION --mfg "Glaxo Wellcome Production" --country "France" --tenure 5
mekong pharma drug "VD-35124-21" "Hapacol 650" "Paracetamol" "650mg" "Viên nén" --class OTC_NON_PRESCRIPTION --mfg "DHG Pharma" --country "Vietnam" --json

# 3. Giám sát điều kiện kho bảo quản thuốc GSP & chuỗi cung ứng lạnh
mekong pharma gsp "WH-COLD-01" "Kho Lạnh Vắc Xin Trung Tâm" --condition COLD_CHAIN --temp 4.2 --humidity 52.0 --sensor "LOG-TEMP-88"
mekong pharma gsp "WH-ROOM-02" "Kho Tổng Dược Phẩm Cần Thơ" --condition STANDARD_ROOM --temp 24.5 --humidity 68.0 --json

# 4. Truy xuất nguồn gốc lô thuốc theo chuẩn GS1 DataMatrix & quản lý thu hồi
mekong pharma batch "B2609-01" "VD-35124-21" "Hapacol 650" --gtin "08935000000018" --serial "SN9876543210" --mfg-date "2026-02-01" --exp-date "2029-02-01" --qty 50000
mekong pharma batch "B2508-BAD" "VN-99999-20" "Kém Chất Lượng" --recall LEVEL_1 --json

# 5. Kê khai giá thuốc & kiểm định thặng số bán lẻ bệnh viện
mekong pharma price "VD-35124-21" "Hapacol 650" 1200 1300 --declared-by "DHG Pharma"
mekong pharma price "VN-88888-22" "Biệt Dược Gốc Tiêm" 500000 520000 --declared-by "Novartis" --json

# 6. Truy vấn danh mục giấy phép lưu hành, kho GSP, lô thuốc hoặc giá
mekong pharma list drugs
mekong pharma list gsp --json
mekong pharma list batches
mekong pharma list prices --json

# 7. Báo cáo đo kiểm hoạt động dược phẩm
mekong pharma status
mekong pharma status --json
```

---

## FastMCP & JSON-RPC Tools

- `mekong_pharma_drug(visa_number, drug_name, active_ingredient, strength, dosage_form, classification, manufacturer_name, country_of_origin, tenure_years)`
- `mekong_pharma_gsp(warehouse_id, warehouse_name, storage_condition, recorded_temp_c, recorded_humidity_pct, sensor_id)`
- `mekong_pharma_batch(batch_number, visa_number, drug_name, gtin_14, serial_number, manufacturing_date, expiry_date, quantity_units, recall_action)`
- `mekong_pharma_price(visa_number, drug_name, wholesale_price_vnd, hospital_retail_price_vnd, declared_by, classification)`
- `mekong_pharma_list(item_type, limit)`
- `mekong_pharma_status()`

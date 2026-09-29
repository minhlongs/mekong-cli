---
name: petrol
description: Vietnamese Petroleum Regulations, Decree 80/2023 Weekly Price Adjustments, National Fuel Reserves & Dispenser Pump E-Invoicing.
---

# ⛽ Petrol — Vietnamese Petroleum Regulations, Price Stabilization & National Fuel Reserves

Autonomous operations engine for Vietnamese downstream petroleum regulation, weekly retail price adjustments (MOPS Platts Singapore formula), statutory national fuel reserve audits, Euro 4/5 laboratory emission standards, and dispenser pump e-invoicing compliance under Official Telegram 1284/CĐ-TTg.

## Statutory Legal Framework

1. **Nghị định 80/2023/NĐ-CP & Nghị định 95/2021/NĐ-CP (Điều hành Kinh doanh Xăng Dầu)**:
   - Cơ chế điều hành giá xăng dầu định kỳ **thứ Năm hàng tuần** (chu kỳ 7 ngày) do Liên Bộ Công Thương - Tài chính chủ trì.
   - Công thức xác định Giá cơ sở xăng dầu (Base Retail Price Formula):
     - Giá CIF nhập khẩu bình quân quy đổi từ Platts Singapore (MOPS USD/bbl).
     - Thuế nhập khẩu ưu đãi (MFN / FTA: Xăng 10%, Dầu 0% - 7%).
     - Thuế Tiêu thụ đặc biệt (TTĐB): Xăng khoáng RON 95 10%, Xăng sinh học E5 RON 92 8%.
     - Thuế Bảo vệ Môi trường (BVMT theo Nghị quyết UBTVQH): Xăng 2.000 VND/lít, Dầu Diesel 1.000 VND/lít, Dầu hỏa 600 VND/lít.
     - Chi phí kinh doanh định mức (1.050 - 1.250 VND/lít) & Lợi nhuận định mức (300 VND/lít).
     - Thuế Giá trị gia tăng (VAT 10%).
     - Quỹ Bình ổn giá xăng dầu (Quỹ BOG): Trích lập và chi sử dụng để điều hòa biến động giá.
     - Phân vùng địa bàn bán lẻ: Vùng 1 (cảng biển/trung tâm) và Vùng 2 (vùng sâu xa: cho phép tăng tối đa +2% so với giá Vùng 1).

2. **Dự trữ Lưu thông Xăng dầu Bắt buộc (Điều 31 Nghị định 83/2014/NĐ-CP & Quyết định 242/QĐ-TTg)**:
   - Đảm bảo an ninh năng lượng quốc gia với các hạn mức tồn kho tối thiểu:
     - Thương nhân đầu mối kinh doanh xuất khẩu, nhập khẩu (Petrolimex, PVOIL, Saigon Petro...): Tối thiểu **20 ngày** cung ứng.
     - Thương nhân phân phối xăng dầu: Tối thiểu **05 ngày** cung ứng.
     - Nhà máy lọc dầu nội địa (Dung Quất, Nghi Sơn): Dự trữ sản xuất tối thiểu **30 ngày**.

3. **Quy chuẩn Kỹ thuật Quốc gia Xăng & Dầu Đi-ê-zen (QCVN 01:2015/BKHCN & Quyết định 49/2011/QĐ-TTg)**:
   - Tiêu chuẩn khí thải Mức 4 (Euro 4) và Mức 5 (Euro 5):
     - Hàm lượng lưu huỳnh (Sulfur): $\le 10\text{ ppm}$ (Euro 5), $\le 50\text{ ppm}$ (Euro 4), $\le 150\text{ ppm}$ (Euro 3).
     - Hàm lượng chì (Pb): Không được phát hiện ($\le 0.005\text{ g/l}$).

4. **Hóa đơn Điện tử Từng lần Bán lẻ Xăng dầu (Công điện 1284/CĐ-TTg & Nghị định 123/2020/NĐ-CP)**:
   - 100% cột bơm xăng dầu phải phát hành hóa đơn điện tử từng lần bơm và truyền dữ liệu thời gian thực hoặc cuối ngày về cơ quan thuế.

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan ngành xăng dầu & dự trữ năng lượng
mekong petrol
mekong petrol --json

# 2. Tính toán giá cơ sở & giá bán lẻ trần xăng dầu chu kỳ thứ Năm
mekong petrol price RON95_III --platts 92.50 --duty 10.0 --bog-deduct 0 --bog-expend 0

# 3. Thẩm định hạn mức dự trữ lưu thông xăng dầu bắt buộc
mekong petrol reserve "Petrolimex Sài Gòn" --type KEY_IMPORTER --capacity 120000 --stock 85000 --daily 3500

# 4. Kiểm định chất lượng nhiên liệu & cấp khí thải Euro 4/5
mekong petrol quality "ST-001" "Cửa hàng Xăng dầu Số 1" --product RON95_III --sulfur 35.0 --lead 0.0

# 5. Giám sát hóa đơn điện tử cột bơm theo Công điện 1284/CĐ-TTg
mekong petrol pump "ST-001" --pumps 8 --tx 1500 --volume 12000 --revenue 285000000 --invoices 1500

# 6. Truy vấn dữ liệu & danh mục
mekong petrol list prices
mekong petrol list reserves
mekong petrol list quality
mekong petrol list pump
mekong petrol list --type prices --json

# 7. Trạng thái hệ thống telemetry
mekong petrol status --json
```

---

## MCP Tools Integration

- `mekong_petrol_price(product_code, mops_platts_usd_per_barrel, import_duty_pct, bog_fund_deduction_vnd, bog_fund_expenditure_vnd, cycle_date)`
- `mekong_petrol_reserve(enterprise_name, enterprise_type, storage_capacity_m3, current_stock_m3, daily_consumption_m3)`
- `mekong_petrol_quality(gas_station_id, gas_station_name, product_code, sulfur_content_ppm, lead_content_g_l)`
- `mekong_petrol_pump(station_id, pump_count, daily_transactions, daily_volume_liters, daily_revenue_vnd, e_invoices_issued)`
- `mekong_petrol_list(item_type, limit)`
- `mekong_petrol_status()`

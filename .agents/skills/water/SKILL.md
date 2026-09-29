---
name: water
description: Vietnamese Clean Water Supply, Urban Drainage, Wastewater & Tariff Regulations.
---

# 💧 Water — Vietnamese Clean Water Supply, Drainage, Wastewater & Tariff Regulations

Autonomous operations engine for Vietnamese public clean water utilities, drinking water quality testing under QCVN 01-1:2018/BYT, progressive tiered water consumption tariffs under Circular 44/2021/TT-BTC, Non-Revenue Water (NRW) leakage audits (Decision 2147/QĐ-TTg), urban drainage fees under Decree 80/2014/NĐ-CP, and industrial wastewater discharge compliance under QCVN 40:2011/BTNMT.

## Statutory Legal Framework

1. **Luật Tài nguyên nước 2023 (Luật số 28/2023/QH15) & Nghị định 117/2007/NĐ-CP, Nghị định 124/2011/NĐ-CP**:
   - Quy định về sản xuất, cung cấp và tiêu thụ nước sạch tại các đô thị, khu công nghiệp và nông thôn.
   - Thỏa thuận thực hiện dịch vụ cấp nước và kế hoạch bảo đảm an toàn cấp nước (Water Safety Plan - WSP theo Thông tư 08/2012/TT-BXD).
   - Kiểm soát tỷ lệ thất thoát nước sạch (Non-Revenue Water - NRW) phấn đấu đạt mục tiêu quốc gia $\le 15\%$ theo Quyết định 2147/QĐ-TTg.

2. **Biểu Khung Giá Nước Sinh Hoạt & Phí Thoát Nước (Thông tư 44/2021/TT-BTC & Nghị định 80/2014/NĐ-CP)**:
   - Biểu giá nước sinh hoạt hộ gia đình 4 bậc thang lũy tiến:
     - **Bậc 1** ($\le 10\text{ m}^3/\text{tháng}$): $8,500\text{ VND/m}^3$ (bảo đảm an sinh xã hội).
     - **Bậc 2** ($> 10 - 20\text{ m}^3/\text{tháng}$): $10,500\text{ VND/m}^3$.
     - **Bậc 3** ($> 20 - 30\text{ m}^3/\text{tháng}$): $13,000\text{ VND/m}^3$.
     - **Bậc 4** ($> 30\text{ m}^3/\text{tháng}$): $16,000\text{ VND/m}^3$.
   - Các nhóm khách hàng khác:
     - Cơ quan hành chính, trường học, bệnh viện (`ADMINISTRATIVE`): $11,500\text{ VND/m}^3$.
     - Đơn vị sự nghiệp công lập, phục vụ công cộng (`PUBLIC_SERVICE`): $12,000\text{ VND/m}^3$.
     - Sản xuất vật chất, nhà máy KCN (`MANUFACTURING`): $14,000\text{ VND/m}^3$.
     - Kinh doanh dịch vụ, nhà hàng, khách sạn (`COMMERCIAL`): $22,000\text{ VND/m}^3$.
   - Phí dịch vụ thoát nước và xử lý nước thải: Tối thiểu $10\%$ giá bán nước sạch theo Nghị định 80/2014/NĐ-CP.
   - Thuế giá trị gia tăng (GTGT) nước sạch: $5\%$.

3. **Quy Chuẩn Kỹ Thuật Quốc Gia QCVN 01-1:2018/BYT về Chất Lượng Nước Sạch Sinh Hoạt**:
   - pH: $6.0 - 8.5$.
   - Độ đục (Turbidity): $\le 2.0\text{ NTU}$.
   - Clo dư tự do (Residual Chlorine): $0.2 - 1.0\text{ mg/L}$.
   - Coliform tổng số: $< 3\text{ CFU}/100\text{ mL}$.
   - E. coli hoặc Coliform chịu nhiệt: $0\text{ CFU}/100\text{ mL}$.
   - Kim loại nặng (Asen $\le 0.01\text{ mg/L}$, Chì $\le 0.01\text{ mg/L}$, Sắt $\le 0.3\text{ mg/L}$).

4. **Nước Thải Công Nghiệp & Tiêu Chuẩn Xả Thải QCVN 40:2011/BTNMT**:
   - **Cột A** (xả vào nguồn nước dùng cho sinh hoạt): BOD5 $\le 30\text{ mg/L}$, COD $\le 75\text{ mg/L}$, TSS $\le 50\text{ mg/L}$, Amoni $\le 5\text{ mg/L}$, pH $6.0 - 9.0$.
   - **Cột B** (xả vào nguồn nước không dùng cho sinh hoạt): BOD5 $\le 50\text{ mg/L}$, COD $\le 150\text{ mg/L}$, TSS $\le 100\text{ mg/L}$, Amoni $\le 10\text{ mg/L}$, pH $5.5 - 9.0$.
   - Bắt buộc lắp đặt hệ thống quan trắc nước thải tự động liên tục truyền dữ liệu về Sở TN&MT địa phương theo Nghị định 08/2022/NĐ-CP.

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan ngành nước & xử lý nước thải
mekong water
mekong water --json

# 2. Đăng ký nhà máy xử lý và cung cấp nước sạch
mekong water plant "Nhà máy Nước Thủ Đức" --capacity 750000 --source "Sông Đồng Nai" --province "TP. Hồ Chí Minh" --tech "Lắng Lamen + Khử trùng Clo" --operator "SAWACO"

# 3. Đánh giá chất lượng nước sinh hoạt theo QCVN 01-1:2018/BYT
mekong water test "PLT-ABCD1234" --location "Vòi cấp nước trạm bơm 2" --ph 7.2 --turbidity 0.85 --chlorine 0.5 --coliform 0 --ecoli 0 --metal-pass

# 4. Tính hóa đơn tiền nước bậc thang, phí thoát nước và thuế GTGT
mekong water bill "KH-098877" "Hộ Gia Đình Nguyễn Văn A" 28.5 --category DOMESTIC --month "2026-03"

# 5. Kiểm toán thất thoát nước sạch (Non-Revenue Water)
mekong water nrw "PLT-ABCD1234" --produced 12000000 --billed 10560000 --period "2026-Q1" --target 15.0

# 6. Kiểm định xả thải nước thải công nghiệp theo QCVN 40:2011/BTNMT
mekong water discharge "Nhà máy Dệt Nhuộm X" --park "KCN VSIP II" --flow 1200 --column COLUMN_A --bod5 24.5 --cod 62.0 --tss 38.0 --nh4 3.5 --ph 7.4

# 7. Tra cứu danh mục
mekong water list plants
mekong water list tests
mekong water list bills
mekong water list nrw
mekong water list discharges
mekong water status
```

---

## FastMCP & JSON-RPC 2.0 Tools

- `mekong_water_plant`: Register water treatment plant with capacity, source, and technology specs under Law on Water Resources 2023.
- `mekong_water_test`: Audit drinking water sample parameters against national technical regulation QCVN 01-1:2018/BYT.
- `mekong_water_bill`: Compute monthly clean water bill, progressive tiered tariffs, drainage fees, and 5% VAT under Circular 44/2021.
- `mekong_water_nrw`: Audit Non-Revenue Water (NRW) percentage against national performance benchmark (<= 15%).
- `mekong_water_discharge`: Inspect industrial wastewater effluent parameters against QCVN 40:2011/BTNMT (Column A or B).
- `mekong_water_list`: Query registered water plants, quality tests, tariff bills, NRW audits, or wastewater discharges.
- `mekong_water_status`: Retrieve Vietnamese clean water supply, quality, tariff billing, and wastewater telemetry.

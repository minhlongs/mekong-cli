---
name: aviation
description: Vietnamese Civil Aviation Law 2014, Circular 53/2019 aeronautical tariffs, IATA e-AWB chargeable weight, and Dangerous Goods DGR.
---

# ✈️ Aviation — Vietnamese Civil Aviation, Air Cargo Freight & Ground Handling

Autonomous civil aviation management engine implementing statutory aeronautical tariffs (Circular 53/2019/TT-BGTVT), airport terminal slot allocation, IATA Cargo-XML volumetric chargeable weight calculations, and Dangerous Goods (IATA DGR / ICAO Annex 18) compliance for Vietnam's commercial airport network.

---

## ⚖️ Căn cứ Pháp lý & Khung Tiêu chuẩn

1. **Luật Hàng không dân dụng Việt Nam 2006 (sửa đổi, bổ sung 2014 - Luật số 61/2014/QH13)**:
   - Quản lý hoạt động bay, vận chuyển hàng không dân dụng, phân bổ slot giờ cất hạ cánh.
2. **Nghị định 05/2021/NĐ-CP**:
   - Quản lý, khai thác hệ thống cảng hàng không, sân bay thương mại tại Việt Nam (Nội Bài - HAN, Tân Sơn Nhất - SGN, Đà Nẵng - DAD, Cam Ranh - CXR, Phú Quốc - PQC, Cát Bi - HPH, Vân Đồn - VDO, v.v.).
3. **Thông tư 53/2019/TT-BGTVT & Thông tư 36/2021/TT-BGTVT**:
   - Biểu giá dịch vụ cất cánh, hạ cánh tàu bay (Landing fees) theo tấn MTOW.
   - Phí đậu sân đỗ tàu bay (Aircraft parking fees) theo giờ và bậc tải trọng.
   - Phí soi chiếu an ninh hàng không và phí phục vụ mặt đất (Apron ground handling / ramp services).
4. **Quy chuẩn Vận tải Hàng không Quốc tế (IATA Cargo-XML, e-AWB & ICAO Technical Instructions)**:
   - Công thức tính Trọng lượng tính cước (Chargeable Weight): $1\text{ CBM} = 166.67\text{ kg}$ (IATA volumetric factor 1:6000: $\text{Length} \times \text{Width} \times \text{Height (cm)} / 6,000$).
   - Quy chuẩn vận chuyển Hàng nguy hiểm (IATA DGR 9 classes): Kiểm tra lệnh cấm trên tàu bay chở khách (PAX FORBIDDEN) vs Tàu bay chỉ chở hàng (CAO).
   - Bảo quản lạnh hàng hóa nhạy cảm nhiệt độ (IATA Time-Temperature-Sensitive Cargo - CRT $+15^\circ\text{C} \dots +25^\circ\text{C}$, Cool $+2^\circ\text{C} \dots +8^\circ\text{C}$, Frozen $-20^\circ\text{C}$).

---

## 💻 CLI Commands

### 1. Bảng điều khiển tổng quan
```bash
mekong aviation
mekong aviation --json
```

### 2. Đăng ký lịch trình chuyến bay & phân bổ sân đỗ (Flight Scheduling)
```bash
mekong aviation flight VN123 A350-900 HAN SGN --mtow 280 --parking 2.5 --dom
mekong aviation flight KE381F B777F ICN HAN --mtow 347 --parking 4.0 --intl --json
```

### 3. Tính toán Trọng lượng tính cước e-AWB (Chargeable Weight)
```bash
mekong aviation cargo "738-12345678" HAN FRA 50 1200 12.5 --type GENERAL
mekong aviation cargo "988-87654321" SGN NRT 20 450 4.2 --type PHARMA --temp 2_8C --json
```

### 4. Tính toán phí cảng hàng không & phục vụ mặt đất (Thông tư 53/2019)
```bash
mekong aviation tariff VN123 HAN 280 --parking 2.5 --cargo 15 --intl
mekong aviation tariff VJ456 SGN 89 --parking 1.5 --cargo 5 --dom --json
```

### 5. Thẩm định hàng nguy hiểm IATA DGR & kiểm tra lệnh cấm tàu bay khách
```bash
mekong aviation dg UN3480 "Lithium ion batteries" CLASS_9 --pg II --qty 12 --aircraft PAX_AND_CARGO
mekong aviation dg UN1993 "Flammable liquid n.o.s." CLASS_3 --pg II --qty 50 --json
```

### 6. Danh mục & Chỉ số điều hành
```bash
mekong aviation list --type flights --limit 20
mekong aviation list --type cargo --json
mekong aviation list --type dg
mekong aviation status --json
```

---

## 🔌 Dual MCP Tools

- `mekong_aviation_flight`: Register commercial flight movement and assign airport apron slot.
- `mekong_aviation_cargo`: Calculate IATA volumetric chargeable weight and determine density rating.
- `mekong_aviation_tariff`: Compute statutory landing, parking, security, and apron ramp service fees (Circular 53/2019).
- `mekong_aviation_dg`: Evaluate Dangerous Goods declaration under IATA DGR and enforce passenger aircraft prohibitions.
- `mekong_aviation_list`: Query registered flight schedules, air cargo shipments, or Dangerous Goods declarations.
- `mekong_aviation_status`: Retrieve Vietnamese civil aviation network metrics and air freight telemetry.

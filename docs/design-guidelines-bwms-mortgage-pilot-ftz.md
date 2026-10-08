# Design Guidelines & Terminal Wireframes: BWMS, Ship Mortgage, Pilotage & Seaport FTZ Suite (Phases 279-282)

## Design Tokens & Visual Hierarchy
- **Primary Color**: `#0284c7` (Ocean Cyan / Maritime & Pilotage Control)
- **Warning / Alert**: `#f59e0b` (Amber - FTZ 20-Day Transshipment Warning / Marginal Freeboard Ladder Safety)
- **Error / Detention**: `#ef4444` (Crimson - D-2 Microbe Limit Exceeded / Mortgage Default Notice Due / E-Seal Tamper Breach)
- **Success / Clear**: `#10b981` (Emerald - D-2 Compliant Discharge / Mortgage Fully Satisfied / Pilotage Cleared / E-Seal Intact)
- **Neutral Dark**: `#0f172a` (Slate 900 Background)
- **Border / Divider**: `#334155` (Slate 700 Accent)

---

## Wireframe 1: Phase 279 BWMS D-2 Compliance & TRO Neutralization Cockpit
```
================================================================================
ĐÁNH GIÁ XẢ NƯỚC DẰN TÀU (BWMS) & CHUẨN D-2 / D-1 (IMO BWM CONVENTION)
================================================================================
Tên tàu / IMO:                 MV MEKONG DISCOVERY / 9876543
Công nghệ xử lý BWMS:          Khử trùng điện phân (Electro-chlorination / EC)
Lưu lượng bơm xả (m³/h):       1,200 m³/h (Tổng thể tích xả: 6,000 m³)
--------------------------------------------------------------------------------
KIỂM TRA CHỈ TIÊU SINH HỌC & ĐỘ TỒN LƯU HÓA CHẤT:
- Nồng độ chất oxy hóa tồn dư (TRO thô): 3.50 mg/L Cl₂
- Tác nhân trung hòa sử dụng:           Natri Bisulfit (NaHSO₃, Tỷ lệ: 1.465)
- Suất liều lượng chất trung hòa:       6.78 kg/h (Hệ số an toàn: 1.10)
- Nồng độ TRO sau trung hòa tại van xả: 0.04 mg/L Cl₂ (Quy định: <= 0.10 mg/L)
--------------------------------------------------------------------------------
KẾT QUẢ PHÂN TÍCH CHỈ TIÊU SINH VẬT (QUY CHUẨN D-2):
- Sinh vật >= 50 µm (Zooplankton):      2 / m³ (Giới hạn: < 10 / m³) -> ĐẠT
- Sinh vật 10 - 50 µm (Phytoplankton):   4 / mL (Giới hạn: < 10 / mL) -> ĐẠT
- Vi khuẩn chỉ thị E. coli:             45 cfu/100mL (Giới hạn: < 250 cfu) -> ĐẠT
- Vi khuẩn Vibrio cholerae:             0 cfu/100mL (Giới hạn: < 1 cfu) -> ĐẠT
--------------------------------------------------------------------------------
KẾT LUẬN & CHỨNG CHỈ XẢ NƯỚC:            ĐỦ ĐIỀU KIỆN XẢ CẢNG (D-2 COMPLIANT)
Mã xác thực chữ ký số kiểm dịch:        BWMS-2026-OK-884A9F21B
================================================================================
```

---

## Wireframe 2: Phase 280 Ship Mortgage Enforcement & Escrow Distribution Cockpit
```
================================================================================
XỬ LÝ THẾ CHẤP TÀU BIỂN & PHÂN BỔ NGUỒN TIỀN THU HỒI (BỘ LUẬT HHVN 2015)
================================================================================
Tên tàu xử lý tài sản bảo đảm: MV MEKONG VOYAGER (Sổ đăng ký tàu biển VN #1092)
Hình thức xử lý:               Bán đấu giá theo thủ tục thi hành án / Tòa án
Tổng số tiền thu hồi (VND):    80,000,000,000 VND
--------------------------------------------------------------------------------
THÔNG BÁO VÀ THỜI HẠN PHÁP LÝ (ĐIỀU 34 BỘ LUẬT HHVN):
- Ngày ban hành thông báo xử lý: 2026-09-15
- Ngày bắt đầu tiến hành xử lý:  2026-10-05 (20 ngày >= 15 ngày quy định) -> HỢP LỆ
--------------------------------------------------------------------------------
THỨ TỰ PHÂN BỔ THÁC NƯỚC (WATERFALL PRIORITY):
1. Chi phí cưỡng chế, thẩm định & đấu giá: 3,000,000,000 VND (100% chi trả)
2. Quyền cầm giữ hàng hải luật định (Đ.37):12,000,000,000 VND (100% chi trả)
3. Ngân hàng A (Thế chấp thứ nhất #Reg01):  50,000,000,000 VND (100% chi trả)
4. Ngân hàng B (Thế chấp thứ hai #Reg02):   15,000,000,000 VND (Được trả: 15,000,000,000 VND)
5. Chủ nợ thông thường không bảo đảm:       0 VND (Hết số dư phân bổ)
6. Số dư hoàn lại cho chủ tàu:             0 VND
--------------------------------------------------------------------------------
TỔNG KẾT NGHĨA VỤ NỢ BẢO ĐẢM:           THẾ CHẤP ĐÃ ĐƯỢC XÓA ĐĂNG KÝ
================================================================================
```

---

## Wireframe 3: Phase 281 Maritime Pilotage Dues & Pilot Ladder Cockpit
```
================================================================================
ĐIỀU ĐỘ HOA TIÊU HÀNG HẢI & TÍNH CƯỚC HOA TIÊU (THÔNG TƯ 39/2023/TT-BGTVT)
================================================================================
Tên tàu / Hô hiệu:             MV MEKONG NAVIGATOR / 3WNK
Dung tích toàn phần (GT):      18,500 GT
Mạn khô thực tế (Freeboard):   10.20 m (Quy định SOLAS V/23: > 9.0m)
--------------------------------------------------------------------------------
KIỂM TRA AN TOÀN THANG HOA TIÊU (SOLAS REG. V/23 & RES. A.1045):
- Bố trí thang hoa tiêu:       THANG KẾT HỢP (Combination Ladder) BẮT BUỘC
- Độ dốc cầu thang mạn:        40° (Quy chuẩn an toàn: <= 45°) -> ĐẠT
- Chiều cao leo thang hoa tiêu:6.50 m (Quy chuẩn an toàn: <= 9.0m) -> ĐẠT
--------------------------------------------------------------------------------
CHI TIẾT TÍNH GIÁ CƯỚC HOA TIÊU (VÙNG HOA TIÊU KHU VỰC I):
- Quãng rộng dẫn tàu:          22.5 hải lý (NM)
- Giá cước cơ bản:             $1,850.00 USD
- Phụ thu hoa tiêu ban đêm:    +$740.00 USD (+40% khung giờ 19:30)
- Phí chờ đợi do thời tiết:    +$40.00 USD (2.0 giờ chờ @ $20/giờ)
--------------------------------------------------------------------------------
TỔNG CƯỚC HOA TIÊU PHẢI THU:   $2,630.00 USD (Quy đổi: 65,750,000 VND)
================================================================================
```

---

## Wireframe 4: Phase 282 Seaport FTZ & E-Seal Tracking Cockpit
```
================================================================================
GIÁM SÁT HÀNG TRUNG CHUYỂN QUỐC TẾ & NIÊM PHONG E-SEAL (LUẬT HẢI QUAN 2014)
================================================================================
Số tờ khai trung chuyển / Vận đơn: OTL-2026-TC98124 / B/L CMDU9128471
Cảng dỡ / Cảng xếp tiếp chuyển:    Cảng Cái Mép -> Cảng Cát Lái
Ngày hạ bãi cảng biển:             2026-09-18 (Thời gian lưu bãi: 20 ngày)
--------------------------------------------------------------------------------
KIỂM SOÁT THỜI HẠN LƯU GIỮ TRUNG CHUYỂN (NGHỊ ĐỊNH 08/2015/NĐ-CP):
- Hạn mức lưu bãi luật định:       30 ngày (Còn lại: 10 ngày)
- Tình trạng thời hạn:             CẢNH BÁO MỨC 1 (>= 20 ngày lưu bãi)
- Gia hạn thời hạn:                Chưa yêu cầu (Cho phép gia hạn tối đa 30 ngày)
--------------------------------------------------------------------------------
GIÁM SÁT ĐỊNH VỊ NIÊM PHONG ĐIỆN TỬ (SMART E-SEAL TELEMETRY):
- Mã định danh E-seal:             ES-VN-2026-99382
- Trạng thái công tắc cảm biến:    NGUYÊN VẸN (Không phát hiện cắt dây/cạy mở)
- Tọa độ hiện tại:                 10.5621° N, 107.0182° E
- Độ lệch hành lang cho phép:      120 m (Ngưỡng an toàn tuyến đường: <= 500 m)
--------------------------------------------------------------------------------
KẾT LUẬN GIÁM SÁT HẢI QUAN:        HỢP LỆ - DUY TRÌ HÀNH TRÌNH VẬN CHUYỂN
Mã SHA-256 xác thực E-seal:        E7A9C5D1F8430B...8849E2B
================================================================================
```

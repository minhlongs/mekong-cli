# Design Guidelines & Terminal Wireframes: Maritime Casualty, e-C/O, Tugboat Tariffs & SOLAS VGM Suite (Phases 271-274)

## Design Tokens & Visual Hierarchy
- **Primary Color**: `#0284c7` (Ocean Cyan / Maritime Authority)
- **Warning / Alert**: `#f59e0b` (Amber - Detention / Deviation / Tolls)
- **Error / Casualty**: `#ef4444` (Crimson - Very Serious Marine Casualty / Overload Rejection)
- **Success / Compliant**: `#10b981` (Emerald - Origin Qualified / VGM Certified)
- **Neutral Dark**: `#0f172a` (Slate 900 Background)
- **Border / Divider**: `#334155` (Slate 700 Accent)

---

## Wireframe 1: Phase 271 Maritime Casualty Formal Inquiry Cockpit
```
================================================================================
BÁO CÁO PHÂN LOẠI & ĐIỀU TRA TAI NẠN HÀNG HẢI (CIRCULAR 34/2015/TT-BGTVT)
================================================================================
Tên tàu / Số IMO:              MV MEKONG PIONEER / 9876543
Thời điểm xảy ra tai nạn:      2026-10-07 14:30 UTC
Vị trí sự cố:                  Phao số 0 luồng Vũng Tàu - Thị Vải
Tính chất sự cố:               Va chạm luồng hẹp (Collision in restricted channel)
--------------------------------------------------------------------------------
PHÂN CẤP TAI NẠN (IMO CODE):   VERY SERIOUS MARINE CASUALTY (VSMC)
Mức độ thiệt hại nhân mạng:    0 tử vong, 1 bị thương nặng
Thiệt hại kết cấu vỏ tàu:      Thủng hầm hàng số 2, ngập nước cục bộ
Nguy cơ ô nhiễm dầu:           Có rò rỉ vết dầu nhẹ (nhóm MARPOL Annex I)
--------------------------------------------------------------------------------
YÊU CẦU PHÁP LÝ & BÁO CÁO:
- Thời hạn báo cáo khẩn cấp:   CÒN 18 GIỜ (Phải nộp Cảng vụ trước 24h)
- Nộp Bản khai tai nạn:        Trước 48 giờ sau khi tàu cập cầu an toàn
- Thành lập Tổ điều tra:       BẮT BUỘC (Quyết định của Cục Hàng hải VN)
- Thời hạn kết luận điều tra:  Tối đa 90 ngày (Tai nạn đặc biệt nghiêm trọng)
================================================================================
```

---

## Wireframe 2: Phase 272 Electronic C/O & Rules of Origin Cockpit
```
================================================================================
THẨM ĐỊNH XUẤT XỨ HÀNG HÓA & CẤP e-C/O (NGHỊ ĐỊNH 31/2018/NĐ-CP)
================================================================================
Mã hồ sơ điện tử:              ECO-2026-VN-887711
Hiệp định thương mại (FTA):    EVFTA (Mẫu EUR.1)
Mã HS thành phẩm:              8471.30 (Máy tính xách tay)
Giá xuất xưởng (FOB):          $850.00 USD / chiếc
--------------------------------------------------------------------------------
TIÊU CHÍ XUẤT XỨ ÁP DỤNG:
- Chuyển đổi mã số hàng (CTC): ĐẠT TIÊU CHÍ (CTH: 8473 -> 8471)
- Hàm lượng giá trị khu vực:   RVC (Build-down) = 52.4% (Ngưỡng yêu cầu: >= 45.0%)
  + Trị giá nguyên liệu nội khối (VOM):  $445.40 USD
  + Trị giá nguyên liệu nhập khẩu (VNM): $404.60 USD
- Quy tắc De Minimis (10%):    ĐẠT (Tỷ lệ không chuyển đổi: 4.8% <= 10.0%)
--------------------------------------------------------------------------------
KẾT LUẬN CẤP CHỨNG NHẬN:       HỢP LỆ ĐỦ ĐIỀU KIỆN CẤP e-C/O
Thuế suất ưu đãi nhập khẩu:    0.0% (Thuế MFN thông thường: 10.0%)
================================================================================
```

---

## Wireframe 3: Phase 273 Seaport Tugboat Towage Tariffs Cockpit
```
================================================================================
TÍNH CƯỚC DỊCH VỤ LAI DẮT CẢNG BIỂN (THÔNG TƯ 39/2023/TT-BGTVT)
================================================================================
Tàu thực hiện lai dắt:         MV OCEAN GLORY (Dung tích: 45,000 GT, LOA: 225m)
Khu vực cảng:                  KHU VỰC III (Cảng Cái Mép - Thị Vải)
Hành trình:                    QUỐC TẾ (Đơn vị tính: USD)
Số lượng tàu lai hỗ trợ:       02 tàu lai (4,000 HP mỗi tàu)
Thời gian thực hiện lai dắt:   2.5 giờ (Cập cầu ban đêm: 23:00 - 01:30)
--------------------------------------------------------------------------------
CHI TIẾT GIÁ CƯỚC LAI DẮT:
- Cước cơ sở (2 tàu x 2.5h):   $2,800.00 USD
- Phụ phí ban đêm (+30%):      +$840.00 USD
- Phụ phí chở hàng nguy hiểm:  +$0.00 USD (Hàng bách hóa thông thường)
- Phụ phí điều kiện dòng xiết: +$0.00 USD
--------------------------------------------------------------------------------
TỔNG CỘNG CƯỚC LAI DẮT:        $3,640.00 USD
================================================================================
```

---

## Wireframe 4: Phase 274 SOLAS VGM Container Verification Cockpit
```
================================================================================
KIỂM TRA XÁC NHẬN KHỐI LƯỢNG CONTAINER (SOLAS VGM - QUY ĐỊNH VI/2)
================================================================================
Mã số Container:               MSKU9081234 (Kích cỡ: 40ft High Cube)
Trọng lượng vỏ rỗng (Tare):    3,850 kg
Trọng lượng CSC Max (R_max):   32,500 kg
Khối lượng VGM khai báo:       28,450 kg (Phương pháp cân 1 - Weighbridge)
--------------------------------------------------------------------------------
KẾT QUẢ CÂN THỰC TẾ TẠI CỔNG CẢNG (TERMINAL IN-GATE WEIGHING):
- Khối lượng cân tại trạm:     28,720 kg
- Sai lệch khối lượng thực tế: +270 kg (+0.95%)
- Ngưỡng dung sai cho phép:    ±5.0% hoặc ±500 kg (ĐẠT DUNG SAI AN TOÀN)
- Kiểm tra vượt tải trọng CSC: ĐẠT (28,720 kg < 32,500 kg)
--------------------------------------------------------------------------------
QUYẾT ĐỊNH XẾP HÀNG:           CHẤP THUẬN XẾP TÀU (VGM VERIFIED & CLEARED)
Phí cân dịch vụ tại cảng:      250,000 VND (Đã thu qua e-Port)
================================================================================
```

# Design Guidelines & Terminal Wireframes: Fuel Switchover, Maritime Liens, Berth Planning & Customs VASSCM Suite (Phases 275-278)

## Design Tokens & Visual Hierarchy
- **Primary Color**: `#0284c7` (Ocean Cyan / Maritime Dispatch)
- **Warning / Alert**: `#f59e0b` (Amber - Yellow Channel / Dynamic UKC Marginal Margin / Thermal Gradient Warning)
- **Error / Detention**: `#ef4444` (Crimson - Red Channel / VASSCM Gate Hold / Extinct Liens / Viscosity Violation)
- **Success / Clear**: `#10b981` (Emerald - Green Channel Release / Safe UKC / Compliant Switchover)
- **Neutral Dark**: `#0f172a` (Slate 900 Background)
- **Border / Divider**: `#334155` (Slate 700 Accent)

---

## Wireframe 1: Phase 275 MARPOL Annex VI Fuel Switchover Cockpit
```
================================================================================
TÍNH TOÁN CHUYỂN ĐỔI NHIÊN LIỆU MARPOL ANNEX VI (MEPC.1/CIRC.864)
================================================================================
Tên tàu / IMO:                 MV MEKONG CHALLENGER / 9912345
Khu vực kiểm soát (ECA):       Vùng kiểm soát khí thải ECA (Giới hạn: 0.10% S)
Nhiên liệu ban đầu:            VLSFO 0.50% S (Nhiệt độ: 125°C, Độ nhớt: 15.0 cSt)
Nhiên liệu thay thế:           ULSFO/MGO 0.08% S (Nhiệt độ: 35°C, Độ nhớt: 2.8 cSt)
--------------------------------------------------------------------------------
THÔNG SỐ HỆ THỐNG VÀ TIÊU THỤ:
- Dung tích hệ thống đường ống: 4.20 m³
- Suất tiêu thụ nhiên liệu máy:  1.40 m³/h (Tại vận tốc hành trình: 14.5 hải lý/h)
- Khoảng cách đến ranh giới ECA: 48.0 hải lý
--------------------------------------------------------------------------------
KẾT QUẢ TÍNH TOÁN QUÁ TRÌNH CHUYỂN ĐỔI:
- Thời gian hòa trộn pha loãng:  3.13 giờ (188 phút)
- Tốc độ hạ nhiệt độ tối đa:     1.50 °C/phút (Ngưỡng an toàn CIMAC: <= 2.0 °C/phút)
- Thời gian ổn định nhiệt độ:    1.00 giờ (60 phút)
- Khoảng cách cần chuyển đổi:    45.4 hải lý
- Độ nhớt tại đầu vào bơm cao áp:2.45 cSt (Đạt chuẩn ISO 8217: >= 2.0 cSt)
--------------------------------------------------------------------------------
KẾT LUẬN & CHỈ ĐẠO HÀNH HẢI:     ĐỦ ĐIỀU KIỆN - BẮT ĐẦU CHUYỂN ĐỔI NGAY
Khoảng cách an toàn dự phòng:   +2.6 hải lý trước khi vượt qua ranh giới ECA
================================================================================
```

---

## Wireframe 2: Phase 276 Maritime Lien Priority Waterfall & Auction Distribution Cockpit
```
================================================================================
PHÂN BỔ TIỀN BÁN ĐẤU GIÁ TÀU THEO QUYỀN CẦM GIỮ HÀNG HẢI (BỘ LUẬT HHVN 2015)
================================================================================
Tên tàu bán đấu giá:           MV MEKONG FREIGHTER (Tòa án nhân dân Hải Phòng)
Tổng số tiền bán đấu giá:      50,000,000,000 VND
Chi phí cưỡng chế & bán đấu giá:2,000,000,000 VND (Khấu trừ ưu tiên số 1)
Số tiền thực tế phân bổ:       48,000,000,000 VND
--------------------------------------------------------------------------------
THỨ TỰ PHÂN BỔ CÁC KHOẢN KHIẾU NẠI THEO ĐIỀU 37 & 41 BỘ LUẬT HÀNG HẢI:
[Cấp 1] Lương & hồi hương thuyền viên: 8,000,000,000 VND (100% - Chi trả đủ)
[Cấp 2] Bồi thường tính mạng, sức khỏe: 3,000,000,000 VND (100% - Chi trả đủ)
[Cấp 3] Cứu hộ hàng hải & Tổn thất chung:
  - Cứu hộ lần 2 (Mới nhất, ngày 15/08): 6,000,000,000 VND (100% - Ưu tiên trước)
  - Cứu hộ lần 1 (Cũ hơn, ngày 02/05):   4,000,000,000 VND (100% - Chi trả đủ)
[Cấp 4] Phí cảng biển, hoa tiêu, an toàn:5,000,000,000 VND (100% - Chi trả đủ)
[Cấp 5] Bồi thường thiệt hại va chạm:    8,000,000,000 VND (100% - Chi trả đủ)
--------------------------------------------------------------------------------
THẾ CHẤP TÀU BIỂN & NỢ THƯỜNG:
- Thế chấp Ngân hàng Maritime Bank:    14,000,000,000 VND (Chi trả đủ)
- Khiếu nại thương mại không có bảo đảm: 0 VND (Số dư còn lại: 0 VND)
- Khiếu nại hết thời hiệu (> 1 năm):     3,500,000,000 VND (BÁC BỎ - HẾT HIỆU LỰC)
================================================================================
```

---

## Wireframe 3: Phase 277 Seaport Berth Allocation, Tidal UKC & BOR Cockpit
```
================================================================================
KẾ HOẠCH ĐIỀU ĐỘ CẦU BẾN & TÍNH TOÁN D-UKC THEO THỦY TRIỀU (NGHỊ ĐỊNH 58/2017)
================================================================================
Cầu cảng chỉ định:             Cầu số 3 - Cảng Quốc tế Cái Mép (CMIT)
Chiều dài cầu khả dụng:        400.0 m
Tàu cập cầu:                   MV MEKONG TITAN (LOA: 366.0 m, Mớn nước: 15.2 m)
Chiều dài slot an toàn yêu cầu:381.0 m (LOA + 15.0 m khoảng đệm) -> ĐẠT
--------------------------------------------------------------------------------
PHÂN TÍCH TĨNH KHÔNG DƯỚI LỐN (DYNAMIC UKC) THEO CỬA SỔ THỦY TRIỀU:
- Độ sâu luồng chuẩn hải đồ:   14.00 m
- Độ cao triều đỉnh (High Water):+3.40 m (Tổng độ sâu nước: 17.40 m)
- Độ chìm do tốc độ (Squat):   -0.45 m (Tốc độ luồng 7.0 kts, Barass confined)
- Độ chìm do nước ngọt:        -0.12 m (Tỷ trọng nước: 1.020 kg/l)
- Độ dự phòng dao động sóng:   -0.30 m
- D-UKC thực tế tại đỉnh triều:  1.33 m (Ngưỡng an toàn tối thiểu: 1.52 m -> 10% mớn)
--------------------------------------------------------------------------------
CỬA SỔ TRIỀU CHO PHÉP HÀNH HẢI:14:15 - 17:45 UTC (Thời lượng: 3 giờ 30 phút)
Hệ số sử dụng cầu bến (BOR):    61.5% (Dưới ngưỡng ùn tắc PIANC 65.0%) -> AN TOÀN
================================================================================
```

---

## Wireframe 4: Phase 278 Customs Risk Channeling & Seaport VASSCM Clearance Cockpit
```
================================================================================
HỆ THỐNG GIÁM SÁT HẢI QUAN TỰ ĐỘNG TẠI CẢNG BIỂN - VASSCM (QUYẾT ĐỊNH 2185/TCHQ)
================================================================================
Số tờ khai hải quan:           104567891234
Mã doanh nghiệp (MST):         0109988776 (Xếp hạng tuân thủ: Mức 1 - Ưu tiên AEO)
Mặt hàng / Mã HS:              8542.31 (Mạch tích hợp bộ xử lý)
Cảng dỡ hàng / Cổng kiểm soát: Cảng Tân Cảng Cát Lái - Cổng E
--------------------------------------------------------------------------------
KẾT QUẢ PHÂN LUỒNG TỰ ĐỘNG:    LUỒNG XANH (GREEN CHANNEL - MÃ 1)
- Điểm đánh giá rủi ro (R-score):0.18 (Ngưỡng Luồng Xanh: < 0.35)
- Miễn kiểm tra hồ sơ giấy:     ĐẠT
- Miễn kiểm tra thực tế hàng:   ĐẠT
- Thời gian thông quan (SLA):   1.8 giây (Đạt chuẩn < 5 giây)
--------------------------------------------------------------------------------
ĐỐI SOÁT 3 BÊN TẠI CỔNG RA (VASSCM GATE-OUT 3-WAY MATCH):
[1] Tờ khai thông quan:        HỢP LỆ (Trạng thái: Đã thông quan)
[2] Lệnh giao hàng điện tử:    HỢP LỆ (e-D/O: Hãng tàu Maersk phát hành)
[3] Số chì (Seal Container):   TRÙNG KHỚP (Seal số: MSK-889977)
--------------------------------------------------------------------------------
KẾT LUẬN GIÁM SÁT CỔNG:        CHO PHÉP XE QUA CỔNG (IN PHIẾU XUẤT CẢNG ĐIỆN TỬ)
Mã băm xác thực VASSCM:        a8f7c9e012...3f8a (SHA-256)
================================================================================
```

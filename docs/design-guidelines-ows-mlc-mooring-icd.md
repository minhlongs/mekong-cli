# Design Guidelines & Giao diện CLI Terminal: Phases 283–286

Phạm vi:
- Phase 283: Giám sát OWS & Van ngắt tự động 15 ppm
- Phase 284: Bảng lương & Bảo lãnh hồi hương MLC 2006
- Phase 285: Biểu cước buộc cởi dây tàu Thông tư 39/2023
- Phase 286: Giám sát tờ khai vận chuyển độc lập OLA về cảng cạn ICD

---

## 1. Nguyên tắc Trực quan
- **Bảng mã màu & Đường viền Terminal**: Sử dụng ký tự định dạng 80 cột tiêu chuẩn (`===`, `---`).
- **Trạng thái tuân thủ**:
  - `ĐẠT CHUẨN / COMPLIANT / HỢP LỆ`
  - `NGẮT XẢ / TỰ ĐỘNG HỒI LƯU / CẢNH BÁO / KHÔNG HỢP LỆ`
- **Số liệu tài chính**: Định dạng hàng nghìn phân cách phẩy, hiển thị rõ cả tiền tệ USD và VNĐ tương đương.

---

## 2. Wireframe Mẫu CLI Terminal

### Phase 283: OWS 15 ppm & Nhật ký dầu
```text
================================================================================
THIẾT BỊ PHÂN LY DẦU NƯỚC (OWS) 15 PPM & NHẬT KÝ DẦU (MARPOL ANNEX I)
================================================================================
Tàu: MV MEKONG ODYSSEY | IMO: 9918234
Vị trí xả: 10.4520° N, 107.1240° E | Cự ly bờ: 25.4 NM
Vận tốc tàu: 12.5 knots | Trạng thái hành trình: ĐANG HÀNH TRÌNH
Nồng độ dầu đo được (15 ppm Bilge Alarm): 8.4 ppm
Trạng thái van xả 3 ngả: MỞ QUA MẠN (DISCHARGING OVERBOARD)
Quy chuẩn xả: ĐẠT CHUẨN (Hàm lượng dầu < 15 ppm)
Mục nhật ký dầu ORB Part I: Code D (Item 15.2 - Overboard discharge via OWS)
Mã xác thực điện tử: 3A91FC88921B7C1045DA19EF
================================================================================
```

### Phase 284: Bảng lương & Ký quỹ hồi hương MLC 2006
```text
================================================================================
TÍNH LƯƠNG THUYỀN VIÊN & BẢO LÃNH HỒI HƯƠNG (MLC 2006 STANDARD A2.2 & A2.5)
================================================================================
Thuyền viên: NGUYEN VAN A | Chức danh: Thủy thủ AB
Lương cơ bản hàng tháng: $750.00 USD
Giờ làm thêm thực tế: 65 giờ (Giờ khoán: 48h, Giờ phát sinh vượt: 17h)
Đơn giá làm thêm (1.25x): $4.51 USD/h
Tiền làm thêm phát sinh: $76.67 USD
Nghỉ phép tích lũy (2.5 ngày/tháng): $62.50 USD
Trợ cấp chức danh & trách nhiệm: $120.00 USD
TỔNG LƯƠNG THỰC LĨNH: $1,009.17 USD (25,229,250 VND)
Trạng thái bảo lãnh hồi hương: ĐÃ KÝ QUỸ TẠI BẢO HIỂM P&I ($15,000 USD)
Số tháng lương dự phòng bỏ rơi (Standard A2.5.2): 4 THÁNG ($4,036.68 USD)
Mã bảo lãnh SEA: MLC-VN-2026-9812-OK
================================================================================
```

### Phase 285: Cước buộc cởi dây tàu Thông tư 39/2023
```text
================================================================================
CƯỚC BUỘC CỞI DÂY TÀU BIỂN & AN TOÀN DÂY MEG4 (THÔNG TƯ 39/2023/TT-BGTVT)
================================================================================
Tàu: MV MEKONG PRIDE | Dung tích: 35,000 GT | Vùng cảng: CẢNG BIỂN KHU VỰC I
Loại dịch vụ: BUỘC DÂY CẬP CẦU (MOORING)
Cước cơ bản theo GT: $210.00 USD
Phụ thu ca đêm (+40% từ 18:00): +$84.00 USD
Phí thời gian chờ do tàu (>30 min): +$30.00 USD
TỔNG CƯỚC BUỘC DÂY: $324.00 USD (8,100,000 VND)
Kiểm tra an toàn dây neo (OCIMF MEG4):
- Tải làm việc an toàn (SWL): 55.0 Tấn | Tải đứt tối thiểu (MBL): 95.0 Tấn
- Tỷ lệ tải SWL/MBL: 57.9% (ĐẠT CHUẨN AN TOÀN <= 60%)
- Cảnh báo vùng văng đứt (Snap-Back Zone): ĐÃ CẢNH BÁO BỐ TRÍ AN TOÀN
Mã biên lai dịch vụ: MOOR-2026-TT39-781A
================================================================================
```

### Phase 286: Giám sát vận chuyển ICD & Tờ khai OLA
```text
================================================================================
GIÁM SÁT VẬN CHUYỂN ĐỘC LẬP OLA & CẢNG CẠN ICD (LUẬT HẢI QUAN 2014)
================================================================================
Tờ khai vận chuyển: OLA-2026-TC89102 | Container: TEMU9918231
Cảng xuất phát: Cảng Quốc tế Cái Mép (VNCME) -> Cảng đích: ICD Sóng Thần (VNSTH)
Cự ly vận chuyển: 68.5 km | Thời gian cho phép: 18.0 giờ
Thời gian thực tế vận chuyển: 4.5 giờ | Trạng thái hành trình: ĐÚNG HẠN
Trạng thái niêm phong Hải quan: NGUYÊN VẸN (SEAL INTACT)
Bảo lãnh tiền thuế vận chuyển: 320,000,000 VND (THƯ BẢO LÃNH NGÂN HÀNG HỢP LỆ)
Xác nhận thông quan đến đích: ĐỦ ĐIỀU KIỆN HOÀN TẤT VẬN CHUYỂN OLA
Mã xác thực giám sát: 9F810CDE92014BAE7812AC49
================================================================================
```

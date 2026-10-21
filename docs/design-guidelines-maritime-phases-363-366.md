# Hướng dẫn Thiết kế Giao diện & Trực quan hóa Dữ liệu: Maritime Phases 363–366

## 1. Màu sắc & Chỉ báo Trạng thái (Design Tokens)
- **Cảnh báo Nguy cấp (Critical Alert)**: Đỏ (#EF4444) — Gia tốc rơi tự do > 15g, lỗi cắt phao HRU ngoài dải 1.5-4.0m, tần số sụt < 57.0Hz gây blackout, phanh tời kéo < 80% MBL, bùn nhiễm độc TBT > 0.001 mg/kg.
- **Cảnh báo Suy giảm (Warning/Degraded)**: Vàng Hổ phách (#F59E0B) — Tải máy phát > 85% MCR chuẩn bị sa thải phụ tải cấp 1, bùn cần xử lý đóng rắn trước khi san lấp, góc cắm nước 45°-50° hoặc 65°-70°.
- **Tuân thủ Hoàn toàn (Compliant/Normal)**: Xanh Lục (#10B981) — Góc vào nước xuồng 50°-65°, cân bằng tải isochronous an toàn, phanh tời >= 80% MBL, đạt chuẩn san lấp bờ QCVN 43 Class 1.
- **Giao diện Giám sát Hàng hải (Maritime Dark Mode)**: Xanh Biển Sâu (#0B192C), Nền tối (#0F172A), Viền thẻ (#1E293B).

## 2. Bố cục Thông tin (Layout)
- **Lifeboat Launch HUD**: Đồng hồ đo gia tốc trọng trường g-load (tối đa 15g), góc nghiêng bệ phóng ray (50°-65°), và độ sâu cảm biến áp suất thủy tĩnh HRU (1.5 - 4.0 m).
- **PMS Switchboard Cockpit**: Bảng phân bổ tải P (kW) và Q (kVAR) giữa các tổ máy phát điện Diesel (DG), chỉ số tần số (Hz) & điện áp (V), danh mục sa thải phụ tải 3 cấp.
- **Sediment Beneficiation Matrix**: Bảng nồng độ kim loại nặng, TBT, PAH so sánh QCVN 43:2017 Class 1/2 và chỉ số cường độ nén UCS (>= 50 kPa) phục vụ san lấp lấn biển.
- **OVID Tug Vetting Dashboard**: Thông số lực kéo tĩnh kiểm định (Bollard Pull), tỷ lệ giữ của phanh tời so với MBL (>= 80%), và ma trận năng lực thuyền viên STCW III/3.

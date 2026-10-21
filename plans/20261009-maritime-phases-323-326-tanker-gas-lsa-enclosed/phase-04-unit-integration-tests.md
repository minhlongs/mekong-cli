# Phase 04: Bộ kiểm thử Đơn vị & Tích hợp 100% Zero-Mock

## 1. Mục tiêu
- Xây dựng file kiểm thử `tests/test_maritime_tanker_gas_lsa_enclosed_suite.py` bao phủ toàn diện 4 phân hệ kỹ thuật hàng hải.
- Không sử dụng mock/giả lập, kiểm tra các trường hợp giá trị chuẩn, giá trị biên (boundary conditions) và các trường hợp vi phạm an toàn dẫn đến từ chối.

## 2. Các nhóm Test Cases bắt buộc
1. **Test Phase 323 (COW & Chemical Prewash)**:
   - COW đạt chuẩn an toàn (O2 <= 8%, áp suất >= 100 mmWG, áp suất rửa >= 7 bar, stripping khô).
   - COW bị từ chối do O2 > 8% (nguy cơ cháy nổ IGS).
   - COW bị từ chối do áp suất hầm hàng < 100 mmWG hoặc cặn đọng vượt ngưỡng.
   - Prewash hóa chất Cat X bắt buộc rửa và xả bờ nồng độ <= 1000 ppm.
   - Vi phạm xả cặn Cat X (nồng độ > 1000 ppm hoặc tồn dư > 75 lít).
   - Xả nước rửa ra biển: Đạt chuẩn (vận tốc >= 7 kts, cách bờ >= 12 NM, sâu >= 25 m) vs Bị từ chối do gần bờ hoặc tàu dừng.
2. **Test Phase 324 (LNG BOG & CTMS)**:
   - Tính toán BOG tự nhiên và tỷ lệ BOR %/ngày chính xác theo công thức nhiệt xâm nhập.
   - Cảnh báo kích hoạt GCU (Gas Combustion Unit) khi tốc độ bốc khí vượt quá khả năng xử lý.
   - Tính toán chuyển giao năng lượng CTMS: Thể tích trừ hơi hoàn lưu, quy đổi sang MT và MMBtu chuẩn xác.
3. **Test Phase 325 (Lifeboat FPD & Release Safety)**:
   - Cơ cấu móc nhả đạt chuẩn: FPD MBL >= 6.0 lần tải trọng móc, cam wear <= 2.0 mm, cảm biến thủy tĩnh kích hoạt.
   - Từ chối nhả do FPD Safety Factor < 6.0 (vi phạm MSC.1/Circ.1327).
   - Cảnh báo rủi ro tự bật móc nguy hiểm khi độ mòn cam > 2.0 mm.
   - Khóa liên động Off-load ngăn chặn nhả khi xuồng chưa nổi trên nước.
   - Cơ chế khẩn cấp On-load yêu cầu override 2 tầng.
4. **Test Phase 326 (Enclosed Space Entry Permit)**:
   - Đủ điều kiện cấp phép: 4-Gas đạt chuẩn (O2 20.8-22%, LEL <= 1%, H2S <= 5 ppm, CO <= 25 ppm, thông gió >= 3 air changes, bích mù cách ly, cảnh giới sẵn sàng).
   - Từ chối cấp phép do thiếu oxy (< 20.8%) hoặc dư oxy (> 22.0%).
   - Từ chối cấp phép do khí cháy LEL > 1% hoặc khí độc H2S > 5 ppm.
   - Từ chối cấp phép do thiếu thông gió hoặc chưa lắp bích mù.
5. **Test Facade & SHA-256 Audit Hashes**:
   - Xác minh toàn bộ kết quả trả về có chuỗi SHA-256 hợp lệ, độ dài 64 ký tự hex.
   - Xác minh Facade re-export đầy đủ và tương thích 100%.

## 3. Checklist Thực hiện
- [x] Viết `tests/test_maritime_tanker_gas_lsa_enclosed_suite.py`.
- [x] Chạy `pytest tests/test_maritime_tanker_gas_lsa_enclosed_suite.py -v`.
- [x] Đảm bảo 100% tests Passed (21/21 tests passed).

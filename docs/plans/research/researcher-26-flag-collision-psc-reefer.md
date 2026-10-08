# Nghiên Cứu Yêu Cầu Kỹ Thuật & Pháp Lý: Phases 259-262

## 1. Tổng Quan & Căn Cứ Pháp Lý (Phases 259-262)

Bốn trụ cột nghiệp vụ quản lý đội tàu, an toàn hàng hải quốc tế và dịch vụ logistics cảng container chuyên dụng:

1. **Phase 259: Đăng Ký Tàu Thuê Mua Trần (Bareboat Charter Registry) & Treo Quốc Tịch Tạm Thời**
   - **Văn bản pháp luật:** Bộ luật Hàng hải VN 2015 (Điều 18-36), Nghị định 171/2016/NĐ-CP & Nghị định 86/2020/NĐ-CP, Công ước UNCLOS 1982 Điều 91 (Mối liên hệ thực chất - Genuine Link).
   - **Nghiệp vụ:** Đăng ký tàu biển mang cờ Việt Nam theo hình thức thuê tàu trần (Bareboat-in) với điều kiện cờ gốc bị tạm đình chỉ (Temporary Flag Suspension Certificate); hoặc tàu Việt Nam cho nước ngoài thuê trần (Bareboat-out) tạm đình chỉ cờ Việt Nam.
   - **Quy tắc:** Cấm đăng ký 2 quốc tịch đồng thời; thời hạn đăng ký bằng thời hạn hợp đồng thuê trần; tỷ lệ thuyền viên Việt Nam đáp ứng Thông tư 20/2023/TT-BGTVT.

2. **Phase 260: Phân Chia Trách Nhiệm Đâm Va Hàng Hải & Điều Khoản Both-to-Blame Collision**
   - **Văn bản pháp luật:** Bộ luật Hàng hải VN 2015 (Điều 268-281), Công ước Brussels 1910 về đâm va, COLREGs 1972, Điều khoản Both-to-Blame Collision Clause (BIMCO / US COGSA).
   - **Nghiệp vụ:** Phân chia tỷ lệ lỗi đâm va (Apportionment of Fault, e.g. 60/40, 70/30, hoặc 50/50 nếu không xác định được); Thanh toán chéo thiệt hại thân tàu (Cross-liabilities mechanism); Trách nhiệm liên đới vô hạn đối với thiệt hại về tính mạng, thương tật thuyền viên/hành khách; Quyền đòi bồi hoàn của chủ tàu chở hàng từ chủ hàng theo vận đơn khi tàu không chở hàng bị kiện đòi 100% thiệt hại hàng hóa.

3. **Phase 261: Kiểm Tra Nhà Nước Cảng Biển (PSC Tokyo MOU) & Chiến Dịch CIC**
   - **Văn bản pháp luật:** Tokyo MOU on Port State Control, IMO Res. A.1155(32) Procedures for PSC, Thông tư 27/2017/TT-BGTVT.
   - **Nghiệp vụ:** Hồ sơ rủi ro tàu biển (Ship Risk Profile - SRP): Low Risk Ship (LRS), Standard Risk Ship (SRS), High Risk Ship (HRS) dựa trên Hiệu suất cờ (White/Grey/Black list), Tổ chức đăng kiểm (High/Medium/Low RO), Hiệu suất công ty quản lý tàu, và lịch sử khiếm khuyết/lưu giữ 36 tháng qua.
   - **Chiến dịch tập trung (CIC):** Fire Safety Systems, MLC Crew Wages, Ballast Water. Mã hành động kiểm tra (Action Codes: Code 30 - Detainable, Code 17 - Rectify before departure, Code 16 - Rectify within 14 days).

4. **Phase 262: Điện Container Lạnh Cảng Biển (Reefer Monitoring & Energy Tariff)**
   - **Văn bản pháp luật:** Thông tư 39/2023/TT-BGTVT, Thông tư 12/2024/TT-BGTVT, Quyết định biểu giá điện EVN.
   - **Nghiệp vụ:** Giám sát container lạnh 24/7 (nhiệt độ cài đặt Setpoint: Chilled +2°C to +4°C, Frozen -18°C to -25°C, Ultra-low -60°C).
   - **Tính toán:** Điện năng tiêu thụ thực tế (kW/h) theo nhiệt độ môi trường nhiệt đới (32°C-38°C), chu kỳ đóng ngắt máy nén (Compressor Duty Cycle: 40% Chilled, 75% Frozen), phụ phí cắm điện/rút điện cảng biển, và cảnh báo sai lệch nhiệt độ quá giới hạn (Excursion > ±2.0°C) dẫn đến rủi ro hư hỏng hàng hóa.

## 2. Thách Thức Kỹ Thuật & Giải Pháp Thiết Kế
- **Thuần thư viện chuẩn Python (Zero-dependency):** Dùng `dataclasses`, `enum`, `typing`, `math`, `json`, `datetime`.
- **Độ chính xác tài chính & hàng hải:** Công thức chéo đâm va (Both-to-Blame cross-liabilities) tính chính xác đến cent USD; bảng điểm rủi ro Tokyo MOU SRP quy chuẩn theo hệ số trọng số nguyên tắc quốc tế; điện năng tiêu thụ container lạnh mô hình hóa nhiệt động học công suất tải thực tế.

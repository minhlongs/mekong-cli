---
name: cinema
description: Vietnamese Cinema, Film Production, Age Classification & Censorship Suite.
---

# mekong cinema — Autonomous Vietnamese Cinema, Film Production, Age Classification & Censorship Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Điện ảnh 2022 (Luật số 05/2022/QH15)** (có hiệu lực từ 01/01/2023):
   - Thống nhất quản lý nhà nước về hoạt động điện ảnh trên toàn quốc.
   - Thẩm quyền quản lý: **Bộ Văn hóa, Thể thao và Du lịch (Bộ VHTTDL)** và **Cục Điện ảnh**.
   - Điều 9 (Hành vi nghiêm cấm): Xuyên tạc lịch sử dân tộc, phủ nhận thành tựu cách mạng; xúc phạm danh nhân, anh hùng dân tộc; vi phạm chủ quyền quốc gia, toàn vẹn lãnh thổ (đặc biệt là bản đồ có đường lưỡi bò chín đoạn phi pháp); truyền bá văn hóa phẩm đồi trụy, tệ nạn xã hội.
   - Điều 19 (Phổ biến phim trên không gian mạng - OTT VOD): Doanh nghiệp phổ biến phim trên mạng phải tự phân loại phim theo quy định của Bộ VHTTDL; hiển thị cảnh báo phân loại độ tuổi; dừng phổ biến và gỡ bỏ phim vi phạm trong thời hạn **24 giờ** kể từ khi nhận được yêu cầu từ cơ quan có thẩm quyền.
2. **Thông tư số 05/2023/TT-BVHTTDL (Tiêu chí phân loại phim & hiển thị cảnh báo)**:
   - Quy định **06 mức phân loại độ tuổi quốc gia**:
     * **P**: Phim được phép phổ biến đến người xem ở mọi độ tuổi.
     * **K**: Phim được phép phổ biến đến người xem dưới 13 tuổi với điều kiện xem cùng cha, mẹ hoặc người giám hộ.
     * **T13** (13+): Phim được phép phổ biến đến người xem từ đủ 13 tuổi trở lên.
     * **T16** (16+): Phim được phép phổ biến đến người xem từ đủ 16 tuổi trở lên.
     * **T18** (18+): Phim được phép phổ biến đến người xem từ đủ 18 tuổi trở lên.
     * **C**: Phim không được phép phổ biến (Bị cấm chiếu).
   - Đánh giá trên 07 tiêu chí: Chủ đề; Bạo lực; Khỏa thân, tình dục; Ma túy, chất kích thích; Kinh dị; Ngôn từ tục tĩu; Hành vi nguy hiểm dễ bắt chước.
   - Quy chuẩn hiển thị cảnh báo: Biểu tượng chữ phân loại (P, K, T13, T16, T18) hiển thị liên tục hoặc tối thiểu 03 giây ở đầu phim; hiển thị thông điệp cảnh báo nội dung nhạy cảm.
3. **Nghị định số 131/2022/NĐ-CP (Quy định chi tiết Luật Điện ảnh)**:
   - Điều 9: Hạn ngạch tỷ lệ suất chiếu phim Việt Nam tại các rạp chiếu phim đạt tối thiểu **10%** tổng số suất chiếu trong năm.
   - Bắt buộc ưu tiên bố trí suất chiếu phim Việt Nam trong khung giờ vàng (**18:00 - 22:00**).
   - Tỷ lệ thời lượng phát sóng phim Việt Nam trên các kênh truyền hình trong nước đạt tối thiểu **30%** tổng thời lượng phát sóng phim.
4. **Nghị định số 38/2021/NĐ-CP & Nghị định số 128/2022/NĐ-CP**:
   - Xử phạt 40.000.000 - 50.000.000 VND đối với hành vi phổ biến phim không đúng mức phân loại độ tuổi hoặc không hiển thị cảnh báo.
   - Xử phạt 80.000.000 - 100.000.000 VND và tịch thu tang vật đối với hành vi phổ biến phim vi phạm chủ quyền quốc gia hoặc phim bị cấm (Mức C).
5. **Lưu trữ SQLite WAL**: Bảng `film_classifications`, `film_censorship_permits`, `cinema_screen_quotas`, `ott_film_compliance`, `ott_film_takedowns` tại `.mekong/cinema.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động điện ảnh, phân loại độ tuổi phim và tỷ lệ suất chiếu tại rạp
mekong cinema

# Thẩm định và phân loại độ tuổi phim theo Thông tư 05/2023/TT-BVHTTDL
mekong cinema classify "Đất Rừng Phương Nam" --violence 2 --nudity 0 --horror 1 --profanity 1

# Thẩm định phát hiện phim vi phạm chủ quyền lãnh thổ (đường lưỡi bò)
mekong cinema classify "Barbie / Uncharted" --sovereign-violation

# Cấp Giấy phép phổ biến phim (GPHPP) cho phim chiếu rạp
mekong cinema permit "Mai" --producer "CJ HK Entertainment" --rating T18 --duration 131 --country "Việt Nam"

# Kiểm toán hạn ngạch tỷ lệ suất chiếu phim Việt Nam tại rạp (NĐ 131/2022)
mekong cinema quota "CGV Landmark 81" --total 600 --vn 80 --prime-total 180 --prime-vn 30

# Hậu kiểm tuân thủ phổ biến phim trên không gian mạng OTT VOD (Netflix, VieON)
mekong cinema ott Netflix --film-id "MOV-NF-9901" --title "Thế Giới Hậu Tận Thế" --rating T16 --warning

# Giám sát quy trình gỡ bỏ phim vi phạm trên không gian mạng trong 24 giờ
mekong cinema takedown Netflix --film-id "MOV-NF-9901" --reason "Hình ảnh bản đồ vi phạm chủ quyền lãnh thổ"

# Tra cứu danh mục hồ sơ điện ảnh
mekong cinema list classifications
mekong cinema list permits
mekong cinema list quotas
mekong cinema list ott

# Báo cáo telemetry chỉ số quản lý điện ảnh quốc gia
mekong cinema status
```

---

## MCP Tools Integration

- `mekong_cinema_classify`: Đánh giá 7 tiêu chí nội dung và xác định mức phân loại độ tuổi phim (P, K, T13, T16, T18, C) theo Thông tư 05/2023/TT-BVHTTDL.
- `mekong_cinema_permit`: Cấp Giấy phép phổ biến phim (GPHPP) chính thức của Cục Điện ảnh.
- `mekong_cinema_quota`: Kiểm toán tỷ lệ suất chiếu phim Việt Nam tại các cụm rạp chiếu phim (>= 10%) và khung giờ vàng.
- `mekong_cinema_ott`: Hậu kiểm tuân thủ hiển thị cảnh báo phân loại độ tuổi và rà soát chủ quyền phim chiếu mạng OTT VOD.
- `mekong_cinema_takedown`: Giám sát thời hạn gỡ bỏ phim vi phạm trên không gian mạng trong vòng 24 giờ (Điều 19 Luật Điện ảnh).
- `mekong_cinema_list`: Tra cứu danh mục hồ sơ thẩm định phân loại phim, giấy phép phổ biến hoặc hạn ngạch rạp.
- `mekong_cinema_status`: Báo cáo telemetry tổng hợp hoạt động thẩm định, phân loại và cấp phép điện ảnh quốc gia.

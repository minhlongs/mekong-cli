---
name: press
description: Vietnamese Press, Mass Media, Online Journalism & OTT Broadcasting Suite.
---

# /press — Vietnamese Press, Media & OTT Broadcasting Suite

Quản lý và giám sát tuân thủ hoạt động báo chí, xuất bản trực tuyến, trang thông tin điện tử tổng hợp (ICP), dịch vụ phát thanh, truyền hình theo yêu cầu (OTT VOD) và quy trình cải chính theo Luật Báo chí 2016.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Luật Báo chí 2016** (Luật số 103/2016/QH13, có hiệu lực từ ngày 01/01/2017).
2. **Nghị định số 119/2020/NĐ-CP & Nghị định số 14/2022/NĐ-CP** quy định xử phạt vi phạm hành chính trong hoạt động báo chí, hoạt động xuất bản.
3. **Nghị định số 71/2022/NĐ-CP** sửa đổi, bổ sung một số điều của Nghị định số 06/2016/NĐ-CP về quản lý, cung cấp và sử dụng dịch vụ phát thanh, truyền hình (OTT TV, VOD).
4. **Nghị định số 72/2013/NĐ-CP & Nghị định số 27/2018/NĐ-CP** về quản lý, cung cấp, sử dụng dịch vụ Internet và thông tin trên mạng (Giấy phép ICP).
5. **Thông tư & Hướng dẫn của Bộ Thông tin và Truyền thông (Bộ TT&TT)** về tiêu chuẩn phóng viên, thẻ nhà báo và bản quyền báo chí.

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Thẩm định Điều kiện Thẻ Nhà báo & Chức danh Báo chí (Điều 24–27 Luật 103/2016/QH13)
- Thẩm tra hồ sơ cấp Thẻ nhà báo: Tốt nghiệp đại học chuyên ngành báo chí (hoặc đại học khác có chứng chỉ nghiệp vụ), thời gian công tác liên tục $\ge 2$ năm, không bị kỷ luật trong 12 tháng.
- Thẩm định tiêu chuẩn bổ nhiệm Tổng biên tập/Phó Tổng biên tập: Bắt buộc có bằng lý luận chính trị cao cấp, kinh nghiệm công tác báo chí $\ge 5$ năm.
- Thẩm định văn phòng đại diện và trưởng đại diện báo chí tại địa phương.

### 2. Kiểm toán Trang Thông tin Điện tử Tổng hợp (ICP) & Chống "Báo hóa" (Nghị định 72 & 27)
- Kiểm tra điều kiện máy chủ đặt tại Việt Nam, thỏa thuận bản quyền trích dẫn nguồn tin bằng văn bản với cơ quan báo chí.
- Giám sát trích dẫn nguyên văn nguồn tin (ghi rõ tác giả, tên báo, ngày giờ xuất bản).
- Chống "báo hóa" trang thông tin điện tử: Tỷ lệ tin tự sản xuất $\le 10\%$ (chỉ thông tin nội bộ), nghiêm cấm tự ý cử phóng viên tác nghiệp điều tra; SLA gỡ bài vi phạm $\le 3\text{ giờ}$.

### 3. Cấp phép & Kiểm duyệt Dịch vụ Phát thanh, Truyền hình OTT & VOD (Nghị định 71/2022/NĐ-CP)
- Cấp phép dịch vụ phát thanh, truyền hình trả tiền trên mạng Internet (SVOD, TVOD, AVOD, OTT TV).
- Bắt buộc triển khai hệ thống phân loại và cảnh báo độ tuổi nội dung (P, K, T13, T16, T18, C) theo tiêu chuẩn điện ảnh.
- Kiểm duyệt nội dung bởi Ban biên tập có chứng chỉ nghiệp vụ; truyền dẫn đầy đủ các kênh truyền hình thiết yếu quốc gia; đảm bảo 100% bản quyền sở hữu trí tuệ.

### 4. Quy trình Cải chính & Xin lỗi Công khai (Điều 42 Luật 103/2016/QH13)
- Cơ chế ban hành cải chính, xin lỗi công khai khi đăng phát thông tin sai sự thật, xúc phạm danh dự tổ chức/cá nhân.
- Thời hạn luật định: Báo điện tử phải cải chính ngay hoặc chậm nhất trong 24 giờ kể từ khi nhận được yêu cầu/kết luận; duy trì vị trí nổi bật tại trang chủ tối thiểu 07 ngày.
- Đảm bảo quyền phản hồi ý kiến của cơ quan, tổ chức, cá nhân bị phản ánh (Điều 43).

### 5. National Press Telemetry & Status
- Báo cáo tổng thể cơ quan báo chí, thẻ nhà báo, trang thông tin điện tử ICP, dịch vụ OTT VOD được cấp phép và các vụ việc cải chính thông tin.

---

## Hướng dẫn Sử dụng CLI (`mekong press`)

```bash
# Xem báo cáo tổng quan telemetry báo chí & truyền thông quốc gia
mekong press

# Thẩm tra hồ sơ cấp Thẻ nhà báo
mekong press credential "Nguyễn Văn Tuấn" --type PRESS_CARD --agency "Báo Nhân Dân" --degree BACHELOR_JOURNALISM --exp 3.5 --clean

# Thẩm tra bổ nhiệm Tổng biên tập
mekong press credential "Lê Hồng Sơn" --type EDITOR_IN_CHIEF --agency "Tạp chí Kinh tế Sài Gòn" --degree MASTER_JOURNALISM --exp 8.0 --clean --political

# Thẩm định trang thông tin điện tử tổng hợp (ICP)
mekong press icp "vnfinance.vn" "Công ty CP Truyền thông Sao Nam" --server-vn --agreement --attribution --self-ratio 5.0 --sla 3

# Thẩm định cấp phép truyền hình OTT & VOD
mekong press ott "MekongFlix" "Công ty TNHH Dịch vụ Số Phương Nam" --type SVOD --age-rating --editorial --essential --copyright

# Giám sát quy trình cải chính và xin lỗi công khai
mekong press correct "Báo Điện tử Tri Thức Mới" "Bài viết phản ánh sai về chất lượng nước giải khát" "2026-09-15" --medium ONLINE --violation "THÔNG TIN SAI SỰ THẬT" --hours 12 --retention 7 --apology --reply

# Tra cứu danh mục hồ sơ đã lưu trữ
mekong press list all --limit 20
```

---

## Công cụ MCP (FastMCP & JSON-RPC 2.0 Parity)

- `mekong_press_credential`: Verify press card, editor-in-chief, or rep office head eligibility (Articles 24-27).
- `mekong_press_icp`: Audit general info website, copyright attribution, and anti-journalization compliance (Decrees 72 & 27).
- `mekong_press_ott`: License and audit OTT Internet TV, radio and VOD services under Decree 71/2022/ND-CP.
- `mekong_press_correct`: Record and verify statutory press correction and public apology within 24h (Article 42).
- `mekong_press_list`: Query stored credentials, ICP audits, OTT licenses, or correction notices.
- `mekong_press_status`: Aggregate national press, mass media, ICP & OTT broadcasting telemetry.

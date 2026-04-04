---
description: Quy trình gen poster, soạn thông báo cho BOOKnBEYOND book club
---

# Book Club — Gen Poster / Soạn Thông Báo

Mỗi khi user yêu cầu gen poster, soạn thông báo, hoặc bất kỳ nội dung nào liên quan đến book club, PHẢI thực hiện các bước sau **TRƯỚC KHI** làm bất cứ gì:

## Bước 1: Đọc config.json (nguồn dữ liệu chính)

// turbo
Đọc file `Sách/book-club/data/config.json` để lấy thông tin mới nhất:
- `currentBook`: sách đang đọc, số chương, ngày bắt đầu/kết thúc
- `schedule`: lịch chia sẻ tuần, MC, người chia sẻ và chương tương ứng
- `members`: danh sách thành viên, điểm, streak
- `meetLink`, `meetTime`: link và giờ họp
- `registerFormLink`: link đăng ký chương
- `voteFormLink`: link vote sách
- `zaloGroupLink`: link nhóm Zalo
- `driveLink`: link Google Drive tài liệu

## Bước 2: Mở link đăng ký chương để cập nhật tình trạng đăng ký

**Link đăng ký chương:** `https://docs.google.com/spreadsheets/d/18JVy2EqdRsJDf_tzDfsqX-jE5I6gos8sWBVzcK06tRU/edit?pli=1&gid=0#gid=0`

Dùng `read_url_content` hoặc `browser_subagent` để đọc Google Sheets trên và xác định:
- Ai đã đăng ký chương nào (cập nhật so với config.json)
- Chương nào còn trống chưa ai đăng ký
- Ghi chú đặc biệt nếu có

> **QUAN TRỌNG:** Dữ liệu trên Sheets là nguồn truth mới nhất, ưu tiên hơn config.json nếu có khác biệt.

## Bước 3: Xác định tuần hiện tại

Dựa vào ngày hiện tại và `schedule` trong config.json:
- Tìm tuần tiếp theo (ngày >= hôm nay)
- Xác định MC, người chia sẻ, nội dung chương
- Tính countdown đến buổi họp

## Bước 4: Gen poster / Soạn thông báo

Dựa trên dữ liệu đã thu thập ở bước 1-3, tiến hành tạo nội dung:

### Nếu gen POSTER:
- Sử dụng brand guidelines tại `Sách/book-club/brand-guidelines.md`
- Tham khảo poster mẫu tại `Sách/book-club/poster-week2.html`
- Bao gồm: tên sách, bìa sách, tuần, MC, người chia sẻ, chương, giờ họp, QR Meet

### Nếu soạn THÔNG BÁO:
- Format ngắn gọn, dễ đọc trên Zalo/mobile
- Bao gồm: thời gian, link Meet, MC tuần, danh sách chia sẻ, link đăng ký chương (nếu còn slot trống)
- Gắn link đăng ký chương nếu cần thêm người đăng ký

## Các link quan trọng (quick reference)

| Mục | Link |
|-----|------|
| Google Meet | https://meet.google.com/onb-gepu-owa |
| Đăng ký chương | https://docs.google.com/spreadsheets/d/18JVy2EqdRsJDf_tzDfsqX-jE5I6gos8sWBVzcK06tRU/edit?pli=1&gid=0#gid=0 |
| Vote sách | https://docs.google.com/forms/d/e/1FAIpQLSfBXm5uto3jFNqRw85xJDSFraRV1Z3JOs_lgh6dOPyV0uswrg/viewform?usp=sf_link |
| Google Drive | https://drive.google.com/drive/folders/1Y8xC8wfZTJ-mP5MGx4JolxpXzt4cut_h?usp=sharing |
| Zalo nhóm | https://zalo.me/g/ukcaaq228 |
| Giờ họp | Chủ Nhật, 05:15 – 07:15 |

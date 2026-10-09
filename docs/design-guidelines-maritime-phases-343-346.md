# Design Guidelines: Maritime Phases 343–346

## 1. Định hướng Thiết kế & Trải nghiệm Người dùng (CLI & API)
- **Chuẩn hiển thị JSON**: Mọi lệnh CLI hỗ trợ định dạng xuất dữ liệu JSON có cấu trúc khi thực thi tự động.
- **Bí danh Tiếng Việt Trực quan**: Hỗ trợ 8 bí danh tiếng Việt cho thuyền trưởng, hoa tiêu, máy trưởng và đại lý viên:
  - `ecdis`, `haidodientu` (ECDIS Passage Plan & Luồng hẹp)
  - `mfmbunker`, `dodaucoriolis` (Đo dầu MFM Coriolis)
  - `noihoint`, `hoanoihotau` (Hóa nghiệm nước nồi hơi tàu biển)
  - `portagency`, `quyettoancangg` (Quyết toán đại lý cảng biển PDA/FDA)

## 2. Mã băm Xác thực & Toàn vẹn Dữ liệu
- Mọi kết quả đánh giá kỹ thuật và quyết toán đại lý sinh mã `audit_digest` SHA-256 chống chỉnh sửa biên bản.
- Giữ thông điệp cảnh báo rõ ràng, phân cấp theo mức độ `CRITICAL`, `WARNING`, `INFO`.

# 👋 Đóng Góp Cho Hệ Sinh Thái RaaS (Contributing Guide)

Cảm ơn bạn đã lựa chọn tham gia vào tiến trình xây dựng **Mekong CLI** - Hệ điều hành Revenue-as-a-Service (RaaS) đầu tiên dựa trên tư duy Binh Pháp.

Tài liệu này hướng dẫn bạn cách đóng góp code, tài liệu và ý tưởng theo đúng tiêu chuẩn chất lượng của dự án.

## 🏯 Quy Tắc Vàng (The Binh Phap Constitution)

Dự án này vận hành dựa trên **Hiến Pháp Mekong-CLI** (`CLAUDE.md`). Mọi đóng góp phải tuân thủ:
1. **DIEU 55**: Ngôn ngữ phản hồi, báo cáo và commit bắt buộc là **Tiếng Việt**.
2. **DIEU 49**: Quy tắc **GREEN PRODUCTION**. Không merge code nếu chưa verify production hoạt động.
3. **PEV Pattern**: Mọi tính năng phải đi qua chu kỳ **Plan → Execute → Verify**.

## 🛠 Thiết Lập Môi Trường Phát Triển

Dự án là một Monorepo sử dụng `pnpm` và kiến trúc Hybrid (Python/Node.js).

### Yêu Cầu Hệ Thống
- Node.js >= 20
- Python >= 3.11
- pnpm >= 8

### Các Bước Cài Đặt
```bash
# 1. Clone repository
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli

# 2. Cài đặt toàn bộ dependencies
pnpm install
pip install -r requirements.txt

# 3. Khởi tạo môi trường
cp .env.example .env
# Cấu hình ANTHROPIC_BASE_URL trỏ về Antigravity Proxy (mặc định port 11436)
```

## 🔄 Quy Trình Đóng Góp

1. **Chọn hoặc Tạo Issue**: Đảm bảo công việc bạn sắp làm đã được thảo luận.
2. **Branching**: Tạo branch từ `main`. Format: `type/tên-ngắn-gọn` (vd: `feat/antigravity-failover`).
3. **Phát triển**:
   - Sử dụng lệnh `/cook` của CC CLI để triển khai.
   - Luôn cập nhật hoặc thêm mới test case trong `tests/`.
4. **Kiểm tra chất lượng (6 Gates)**:
   - Chạy `npm test` và `python3 -m pytest`.
   - Đảm bảo không còn `any` trong TypeScript và không còn `console.log`.
5. **Tạo Pull Request**:
   - Sử dụng template PR của dự án.
   - Gửi kèm screenshot hoặc log verify thành công.

## 🛡️ Cổng Chất Lượng Binh Pháp (Quality Gates)

Code của bạn chỉ được chấp nhận nếu vượt qua các cổng sau:

| Cổng | Yêu Cầu | Kiểm Tra |
|------|---------|----------|
| **始計 (始計)** | 0 nợ kỹ thuật | Không có `TODO`, `FIXME` trong code chính. |
| **作戰 (作戰)** | 100% Type Safety | `grep -r ": any" src` trả về 0 kết quả. |
| **軍形 (軍形)** | Bảo mật | Không có API Key hoặc Secret bị hardcode. |
| **虚実 (虚実)** | Tài liệu | Mọi thay đổi logic phải được cập nhật vào `/docs`. |

## 🤝 Code of Conduct

Chúng tôi tôn trọng sự khác biệt và thúc đẩy sự hợp tác chuyên nghiệp. Mọi hành vi thiếu tôn trọng hoặc quấy rối sẽ dẫn đến việc bị ban khỏi dự án ngay lập tức.

---

*"Binh quý thắng, bất quý cửu"* — Hãy đóng góp những giá trị thực chất và hiệu quả!

© 2026 Binh Phap Venture Studio.

# Báo Cáo Quét Bảo Mật Toàn Diện (Security Audit) - mekong-cli
**Ngày:** 2026-02-15
**Trạng thái:** NGUY CƠ CAO (Cần xử lý trước khi Open Source)

## 1. Kết quả tìm kiếm API Keys & Secrets cứng (Hardcoded)

Phát hiện nhiều thông tin nhạy cảm đang bị để cứng trong mã nguồn và các script:

### 🔴 Mức độ Nghiêm trọng (Critical) - Cần thu hồi và đổi ngay:
- **Gemini / Google AI API Keys:**
  - `AIzaSyBeFTNIvKtav1DoZKFACQVyrgNusRODfcg` (Tìm thấy trong `src/core/autonomous.py`, `scripts/verify_vertex.py`, `scripts/gemini_chat.py`, `apps/antigravity-gateway/wrangler.toml`)
  - `AIzaSyCzyAYh_D_wGJkdFqRLtVkuCZeTvsVMuh0` (Tìm thấy trong `.env.bak`, `apps/antigravity-gateway/wrangler.toml`)
  - `AIzaSyC79sMC-4fLacJDpDpGmFZKxvsvwZMC2IQ` (Tìm thấy trong `scripts/start-telegram-bot.sh`)
- **Anthropic / Antigravity Proxy Keys:**
  - `sk-6219c93290f14b32b047342ca8b0bea9` (Tìm thấy trong `scripts/tom-hum-persistent-dispatch.exp`, `scripts/qwen_bridge.py`, `apps/antigravity-gateway/wrangler.toml`, `apps/antigravity-gateway/cook.js`)
  - `sk-c397f4b713e6400e96c18e8c07ffeaef` (Tìm thấy trong `scripts/qwen_bridge.py`)
- **Telegram Bot Tokens:**
  - `8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I` (Tìm thấy trong `scripts/start-telegram-bot.sh`, `apps/openclaw-worker/openclaw-service.sh`, v.v.)
- **Cloudflare API Tokens:**
  - `ZGmz0rgZp4l8q8YYp8Qo9nDpu-rJbbg0QnxCkWVu` (Tìm thấy trong `apps/raas-gateway/update_secret.sh`, `apps/openclaw-worker/openclaw-service.sh`)

## 2. Kiểm tra file .env và cấu hình

- **.env:** File gốc hiện đang được gitignore đúng quy định.
- **.env.bak:** **RỦI RO CAO**. File này đang được Git theo dõi (tracked) và chứa API Key thực tế.
- **.env.example:** Chứa các giá trị mẫu, an toàn.

## 3. Rà soát file nội bộ (RULES_*.md)

- **RULES_DNA_FIRST_v30.md:** File này chứa chiến lược phân bổ nguồn lực nội bộ. Hiện đang được Git theo dõi mặc dù đã bị xóa trên đĩa (staged deletion). Cần xóa hoàn toàn khỏi lịch sử Git.
- **Tài liệu chiến lược:** Một số file trong `plans/` và `docs/` chứa thông tin doanh thu và đối thủ cạnh tranh (ví dụ: `plans/revenue-strategy-2026.md`). Cần di chuyển vào thư mục `internal/` đã được ignore.

## 4. Đánh giá rủi ro trước khi Open Source

Dự án **CHƯA SẴN SÀNG** để Open Source do các rủi ro sau:
1. **Lộ lọt thông tin xác thực:** Nếu push lên public, các key trên sẽ bị lợi dụng ngay lập tức (gây tốn kém chi phí hoặc chiếm quyền điều khiển bot/gateway).
2. **Lịch sử Git bị nhiễm độc:** Việc chỉ xóa key trong commit mới là không đủ, vì các key vẫn tồn tại trong lịch sử Git.
3. **Lộ cấu trúc hạ tầng:** Các script chứa đường dẫn tuyệt đối (`/Users/macbookprom1/...`) tiết lộ thông tin về môi trường phát triển.

## 5. Khuyến nghị hành động (Action Plan)

1. **Thu hồi (Revoke):** Ngay lập tức vô hiệu hóa tất cả các API keys và tokens liệt kê ở mục 1 trên các dashboard tương ứng (Google, Anthropic, Telegram, Cloudflare).
2. **Biến môi trường (Environment Variables):**
   - Chuyển tất cả hardcoded keys sang sử dụng `os.getenv` hoặc `process.env`.
   - Cập nhật `.env.example` với đầy đủ các biến cần thiết.
3. **Làm sạch lịch sử Git (Clean History):**
   - Sử dụng `git filter-repo` hoặc `BFG Repo-Cleaner` để xóa vĩnh viễn các chuỗi bí mật và file `.env.bak`, `RULES_*.md` khỏi toàn bộ lịch sử commit.
4. **Cấu hình lại scripts:** Thay thế các đường dẫn tuyệt đối bằng đường dẫn tương đối dựa trên gốc dự án.
5. **Di chuyển tài liệu nội bộ:** Đưa các file chiến lược kinh doanh vào thư mục được ignore hoàn toàn.

---
*Báo cáo được thực hiện bởi Antigravity Security Audit Tool.*

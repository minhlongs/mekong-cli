# Báo cáo Audit Cấu trúc & Quy tắc Nội bộ (Open-Source Readiness)

**Ngày thực hiện:** 2026-02-15
**Agent:** Code Reviewer
**Đối tượng:** mekong-cli repository

---

## 1. Kiểm tra Metadata & package.json

### Root package.json
- **Vấn đề:**
    - Hiện đang đặt `"private": true`. Đây là thiết lập đúng cho monorepo root, nhưng cần xác định rõ các package con nào sẽ được publish lên NPM.
    - URL repository trỏ về cá nhân: `https://github.com/longtho638-jpg/mekong-cli.git`. Cần chuyển sang tổ chức (org) chính thức.
    - Description chứa thuật ngữ nội bộ: "Binh Phap & ClaudeKit DNA".
- **Khuyến nghị:** Cập nhật thông tin `author`, `repository` và `bugs` URL về trang chính thức của dự án.

### Workspace Packages (@mekong/ scope)
- **Tình trạng:** Các package trong `packages/core/` (`shared`, `perception`, `vibe`, `vibe-agents`) đã sử dụng scope `@mekong/`.
- **Thiếu sót:**
    - Hầu hết các package đều ở version `0.0.1` hoặc `1.0.0` nhưng có script test rỗng (`echo 'No tests yet'`).
    - File `packages/core/shared/package.json` vẫn đang để `"private": true`, cần mở nếu muốn cộng đồng sử dụng như một thư viện.

### Apps Metadata
- **raas-gateway:** `author` được để là "Binh Phap Venture Studio". Cần thống nhất một danh tính author cho toàn bộ ecosystem.

---

## 2. Danh sách File Quy tắc Nội bộ & Cần gỡ bỏ/Redact

Dự án chứa nhiều file mang tính chất "quản trị nội bộ" hoặc sử dụng thuật ngữ quân sự (Binh Pháp) không phù hợp với tài liệu kỹ thuật phổ thông.

### File chứa thông tin nhạy cảm/Local paths
- **`apps/raas-gateway/wrangler.toml`**: Chứa `account_id` và `zone_id` thật của Cloudflare. **Nguy cơ bảo mật cao.**
- **`BINH_PHAP_M1_MASTER_STRATEGY.md`**: Chứa các chiến lược tối ưu riêng cho máy MacBook M1 của cá nhân (thermal management).
- **`scripts/tom-hum-cc.sh`** (và các script tương đương): Chứa các đường dẫn tuyệt đối như `/Users/macbookprom1/...`.

### File quy tắc (Internal Rules) cần gỡ bỏ hoặc viết lại
- **`BINH_PHAP_MASTER.md`**, **`36_KE.md`**, **`QUAN_LUAT.md`**: Sử dụng thuật ngữ quân sự nặng nề, khó hiểu cho người dùng mới.
- **`CLAUDE.md` (tại các thư mục con)**: Chứa các quy tắc điều hướng AI (agent rules) rất cụ thể cho môi trường local.
- **`PROXY_RULES.md`**: Chứa logic về Antigravity Proxy, vốn là một thành phần nội bộ chưa chắc đã đi kèm bản open-source.

---

## 3. Tính nhất quán của cấu trúc

- **Cấu trúc Apps:** Có sự pha trộn giữa "Core Infrastructure" (`openclaw-worker`, `raas-gateway`) và "Customer Projects" (`84tea`, `anima119`).
    - **Khuyến nghị:** Di chuyển các app thương mại (`84tea`, `anima119`, `sa-dec-flower-hunt`) sang một repo riêng hoặc đưa vào thư mục `examples/` để làm mẫu, thay vì để chung trong `apps/` của core engine.
- **Cấu trúc Packages:** Phân loại `core`, `integrations`, `tooling`, `business`, `ui` là rất tốt và chuyên nghiệp. Tuy nhiên, `packages/core/vibe-agents` đang chứa thư mục `node_modules` rác (nên được ignore).

---

## 4. Đánh giá Open-Source Standard Files

| File | Tình trạng | Đánh giá |
| :--- | :--- | :--- |
| **LICENSE** | Có (MIT) | Tốt. |
| **CONTRIBUTING.md** | Có | Cần sửa: Hiện đang nhắc đến "The 6 Gates" và các quy trình nội bộ của AgencyOS. |
| **CODE_OF_CONDUCT.md** | Có | Cần cập nhật email liên hệ (hiện là `security@agencyos.dev`). |
| **SECURITY.md** | Có | Cần cập nhật quy trình báo lỗi bảo mật. |
| **README.md** | Có | Cần viết lại: Tập trung vào tính năng kỹ thuật, bớt sử dụng codename (Tôm Hùm, Antigravity) mà không có định nghĩa rõ ràng. |

---

## 5. Hành động Đề xuất (Next Steps)

1. **Vệ sinh Git**: Sử dụng `git filter-repo` hoặc BFG để xóa bỏ vĩnh viễn các file chứa credentials (như `wrangler.toml` với ID thật) khỏi lịch sử git.
2. **Template- hóa cấu hình**: Chuyển các ID trong `wrangler.toml` và các biến môi trường trong script thành file `.env.example`.
3. **Chuyển đổi ngôn ngữ/thuật ngữ**:
    - Thay thế "Binh Pháp" bằng "Strategic Patterns" hoặc "Autonomous Protocols" trong tài liệu công khai.
    - Viết lại các ĐIỀU (Articles) trong hiến pháp thành "Guidelines".
4. **Tách biệt Core và Apps**: Chỉ giữ lại các app mang tính hạ tầng trong repo chính. Các app dự án khách hàng nên được gỡ bỏ để tránh vi phạm bảo mật dữ liệu khách hàng.
5. **Cập nhật Absolute Paths**: Thay thế toàn bộ đường dẫn `/Users/macbookprom1/...` bằng các biến môi trường hoặc đường dẫn tương đối dựa trên root dự án.

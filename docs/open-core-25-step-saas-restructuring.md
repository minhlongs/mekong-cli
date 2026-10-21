# 25 Bước Tái Cấu Trúc Dự Án Mã Nguồn Mở (Public GitHub) Nhưng Vẫn Thu Tiền SaaS
# 25-Step Open-Core Public GitHub Restructuring with SaaS Monetization

> **Bilingual Executive Blueprint (VN / EN)** — Cách mở mã nguồn công khai trên GitHub (MIT License) để thu hút cộng đồng Developer mà vẫn bảo vệ biên lợi nhuận SaaS / RaaS đám mây.

---

## Tổng Quan Chiến Lược / Strategic Overview

Mô hình **Open-Core (Lõi Mở - Đám Mây Thu Phí)** phân tách rõ ràng giữa:
- **Public GitHub (MIT Open-Source — Miễn phí):** Công cụ CLI chạy trên máy cá nhân (`mekong`), bộ công thức toán định lượng & kiểm soát an toàn (`src/core/`, `src/desk/`), và giao diện kết nối BYOK (tự nhập API key).
- **Cloud SaaS / Enterprise (Thu phí định kỳ & theo Credit MCU):** Hệ thống chạy tự động 24/7 không cần treo máy, quản lý đa tài khoản (Multi-tenant RBAC), cổng thanh toán tự động (PayOS / NOWPayments / Polar), lưu trữ khóa bảo mật tập trung, và báo cáo kiểm toán thuế TT78.

---

## 25 Bước Thực Thi (Chia Làm 5 Giai Đoạn) / The 25 Execution Steps

### Giai Đoạn 1 (Bước 1–5): Tách Mã Nguồn & Làm Sạch Bảo Mật (Codebase Split & Secret Hygiene)
1. **Bước 1 — Quét & Xóa Lịch Sử Lộ Key (`gitleaks` / `git-filter-repo`):** Kiểm tra toàn bộ lịch sử commit để đảm bảo không còn sót `.env`, API key hay mật khẩu DB trước khi chuyển repo sang Public.
2. **Bước 2 — Phân Ranh Giới Thư Mục Open-Core vs. SaaS:** Giữ `src/core/`, `src/cli/` ở nhánh MIT công khai; tách các phần quản trị khách hàng riêng (`apps/`, `app/`, `billing/`) ra khỏi kho mã nguồn công khai.
3. **Bước 3 — Khóa Chặn `.gitignore` & CI Guard:** Chặn tuyệt đối `.env*`, `*.pem`, `apps/`, `billing/`, và dữ liệu khách hàng không bao giờ được commit.
4. **Bước 4 — Chuẩn Hóa `.env.example` Không Chứa Bí Mật:** Cung cấp file mẫu dễ hiểu để người dùng mã nguồn mở tự điền key cá nhân (BYOK).
5. **Bước 5 — Chuẩn Hóa Giấy Phép MIT & SBOM:** Gắn header MIT License rõ ràng cho phần lõi mở, giúp lập trình viên yên tâm sử dụng và đóng góp ngôi sao (GitHub Stars).

### Giai Đoạn 2 (Bước 6–10): Kiến Trúc Plugin & Điểm Nối Đám Mây (Plugin Seams & Local-First Runtime)
6. **Bước 6 — Giao Diện Trừu Tượng Hóa (`CapabilityBus` & `PaymentProvider`):** Mã nguồn mở chỉ chứa giao diện chuẩn và bản chạy thử (mock/local), còn bản kết nối hạ tầng lớn nằm trên Cloud.
7. **Bước 7 — Chế Độ Tự Mang Khóa (BYOK - Bring Your Own Key):** Người dùng miễn phí tự trả tiền OpenRouter / sàn giao dịch trên máy họ; bạn không tốn chi phí server cho người dùng miễn phí.
8. **Bước 8 — Điểm Nối Từ Xa (`CloudBridge` / `WatcherBridge`):** Cài sẵn các cổng kết nối nhẹ trong CLI để khi người dùng gõ `mekong cloud sync`, CLI lập tức kết nối lên SaaS của bạn.
9. **Bước 9 — Hộp Cát Chạy Cục Bộ (`ExecRuntime Sandbox`):** Cho phép chạy đầy đủ tính năng cơ bản cho 1 người dùng trên máy cá nhân để tạo giá trị thật ngay lập tức.
10. **Bước 10 — Xuất Bản OpenAPI & SDK Chuẩn:** Tài liệu hóa rõ ràng API để các công ty khác tích hợp và trả phí theo lượt gọi (API Metering).

### Giai Đoạn 3 (Bước 11–15): Cổng Kiểm Soát Đám Mây & Thu Phí MCU (Cloud Control Plane & License Gate)
11. **Bước 11 — Cổng Xác Thực Bản Quyền (`license_gate.py`):** Mọi yêu cầu gọi lên máy chủ Cloud đều phải qua kiểm tra JWT hợp lệ (`HTTP 401` nếu thiếu).
12. **Bước 12 — Đồng Hồ Đếm Tín Dụng MCU (`MCUBilling` & `CreditStore`):** Trừ điểm MCU theo từng tác vụ AI hoặc lệnh giao dịch; trả về `HTTP 402 Payment Required` kèm link nạp tiền khi hết số dư.
13. **Bước 13 — Phân Tầng Giới Hạn Tốc Độ (`TIER_CONFIG`):** Áp dụng hạn mức từ `FREE` (10 req/phút) đến `PRO`, `ENTERPRISE`, `MASTER` (5,000 req/phút).
14. **Bước 14 — Hàng Đợi Đám Mây Hiệu Năng Cao (Redis Cluster & Cloudflare Workers):** Chạy các tác vụ nặng, quét chênh lệch giá (Arbitrage) và tạo video AI trên hạ tầng đám mây thu phí.
15. **Bước 15 — Két Bảo Mật Khóa Khách Hàng (Encrypted Vault):** Mã hóa khóa API của khách hàng trên bản SaaS để họ sử dụng qua trình duyệt và Telegram Bot `@Sophia_Bbot` mọi lúc.

### Giai Đoạn 4 (Bước 16–20): Tính Năng Doanh Nghiệp & Điểm Chốt Doanh Thu (Enterprise & Revenue Triggers)
16. **Bước 16 — Quản Lý Đa Khách Hàng & Phân Quyền (`subscriber-tenant-isolator.ts`):** Tính năng quản lý đội nhóm, phân quyền nhân viên chỉ mở ở gói trả phí (`STARTER` trở lên).
17. **Bước 17 — Nhật Ký Kiểm Toán & Tuân Thủ Thuế (TT78 / KYC Audit Logs):** Lưu trữ lịch sử giao dịch và hóa đơn điện tử phục vụ doanh nghiệp.
18. **Bước 18 — Chạy Tự Động 24/7 & Cảnh Báo Tức Thời (Hosted Daemon & Telegram Webhook):** Người dùng cá nhân ngại treo máy 24/7 sẽ trả tiền thuê bao hàng tháng để hệ thống chạy thay họ trên mây.
19. **Bước 19 — Chợ Chiến Lược & Chia Sẻ Doanh Thu (Strategy & Recipe Marketplace):** Thu phí hoa hồng khi người dùng đăng ký sử dụng các chiến lược AI/Trading cao cấp trên chợ.
20. **Bước 20 — Tự Động Kích Hoạt Qua Webhook Thanh Toán:** Kết nối PayOS (Việt Nam), NOWPayments (Crypto), và Polar để tự động nâng hạng tài khoản ngay khi nhận tiền.

### Giai Đoạn 5 (Bước 21–25): Vòng Lặp Tăng Trưởng Từ GitHub Sang SaaS (PLG Funnel & CI Governance)
21. **Bước 21 — Trải Nghiệm Khởi Chạy 60 Giây (`Quickstart`):** Giúp lập trình viên chạy thử thành công trên máy trong 1 phút đầu tiên để tăng tỷ lệ lan truyền trên GitHub.
22. **Bước 22 — Thông Báo Nâng Cấp Thông Minh Ngay Trong CLI:** Khi tác vụ vượt quá sức mạnh máy cá nhân hoặc hết hạn mức miễn phí, CLI hiển thị đường dẫn nâng cấp lên Cloud SaaS chỉ với 1 cú nhấp.
23. **Bước 23 — Cổng Kiểm Duyệt Tự Động Trước Khi Đẩy Code (Pre-Publish Readiness Gate):** Tự động kiểm tra không lộ file nhạy cảm, không vượt quá 200 dòng/file, và vượt qua 100% bài kiểm thử.
24. **Bước 24 — Bảng Xếp Hạng & Huy Hiệu Kiểm Chứng Công Khai:** Công bố kết quả kiểm thử (5,900+ bài test xanh) để xây dựng niềm tin tuyệt đối cho khách hàng trả phí.
25. **Bước 25 — Thỏa Thuận Đóng Góp (CLA) & Bảo Vệ Thương Hiệu:** Cho phép cộng đồng đóng góp tính năng mới vào bản mở trong khi công ty giữ toàn quyền thương mại hóa bản SaaS.

---
title: "Improve README.md: App Ecosystem, Contribution & Roadmap"
description: "Cập nhật README.md với 3 cải tiến chính: Hệ sinh thái ứng dụng, Hướng dẫn đóng góp chuẩn Binh Pháp và Lộ trình phát triển."
status: completed
priority: P2
effort: 1h
branch: main
tags: [documentation, readme, binh-phap]
created: 2026-02-15
---

# Kế Hoạch Cải Tiến README.md

## 1. Top 3 Cải Tiến Cần Thiết
Dựa trên phân tích hiện trạng, 3 cải tiến quan trọng nhất để nâng cao tính minh bạch và khả năng tiếp cận của dự án:

1.  **🌌 Hệ Sinh Thái Ứng Dụng (App Ecosystem)**
    *   **Vấn đề:** Người xem không biết mekong-cli quản lý những ứng dụng vệ tinh nào.
    *   **Giải pháp:** Thêm bảng liệt kê các module trong `apps/` kèm vai trò và Binh Pháp tương ứng.

2.  **🗺️ Lộ Trình Phát Triển (Roadmap)**
    *   **Vấn đề:** Thiếu tầm nhìn về hướng đi của dự án trong các quý tiếp theo.
    *   **Giải pháp:** Bổ sung section Roadmap với các cột mốc Q1/Q2 2026 và Tương lai.

3.  **🤝 Quy Trình Đóng Góp Chuẩn Binh Pháp (Contribution)**
    *   **Vấn đề:** Developer mới không rõ quy tắc Git, Commit và Quality Gates.
    *   **Giải pháp:** Tóm tắt quy trình đóng góp tuân thủ Hiến Pháp `CLAUDE.md`.

## 2. Chi Tiết Thực Thi

### 2.1. Section: Hệ Sinh Thái Ứng Dụng
Vị trí: Sau phần "Kiến Trúc".
Nội dung dự kiến:

| Ứng dụng | Vai trò | Binh Pháp |
|----------|---------|-----------|
| `sophia-ai-factory` | Video SaaS, Payments, AI Pipeline | 第五篇 兵勢 |
| `84tea` | Chuỗi F&B, Brand Guidelines | 第十一篇 九地 |
| `agencyos-web` | Dashboard & Admin Panel | 第六篇 虛實 |
| `openclaw-worker` | Tôm Hùm Daemon, Task Queue | 第九篇 行軍 |
| `apex-os` | Trading Platform, Agent Structure | 第十二篇 火攻 |
| `anima119` | E-commerce Đông Y | 第十三篇 用間 |
| `raas-gateway` | Cloud API Gateway | 第二篇 作戰 |

### 2.2. Section: Lộ Trình (Roadmap)
Vị trí: Sau phần "Tính Năng".
Nội dung (Tổng hợp từ context):
- **Q1 2026 (Foundation)**: Hoàn thiện Tôm Hùm Auto-CTO, Tối ưu hóa Antigravity Proxy, Ổn định Core Engine.
- **Q2 2026 (Expansion)**: Mở rộng Agent Teams (Parallel Execution), Tích hợp sâu Cloudflare Workers, RaaS Marketplace Beta.
- **Future (Vision)**: Plugin System toàn diện, Hỗ trợ Multi-Cloud Native.

### 2.3. Section: Đóng Góp (Contribution)
Vị trí: Trước phần "Tài Liệu".
Nội dung:
- **Nguyên tắc:** Tuân thủ tuyệt đối [CLAUDE.md](./CLAUDE.md).
- **Quy trình:**
  1. Checkout branch mới: `feat/` hoặc `fix/`.
  2. Implement & Verify: `mekong cook`.
  3. Commit chuẩn Conventional: `feat:`, `fix:`, `refactor:`.
  4. Push & Wait CI/CD Green.

## 3. Các Bước Thực Hiện (Todo)

- [x] **Scout**: Kiểm tra lại mô tả của từng app trong `apps/*/CLAUDE.md` (nếu có) để đảm bảo chính xác.
- [x] **Update**: Chỉnh sửa file `README.md` thêm 3 section mới.
- [x] **Review**: Kiểm tra hiển thị Markdown.

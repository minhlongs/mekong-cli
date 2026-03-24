# F&B CAFFE CONTAINER — Sa Đéc 🚀

> Hệ thống quản lý quán cafe container hiện đại — Đặt hàng online, thanh toán số, KDS realtime, Loyalty program

**Target:** 500 đơn/ngày | 50M VND/tháng

[![CI/CD](https://github.com/huuthongdongthap/sadec-marketing-hub/actions/workflows/deploy.yml/badge.svg)](https://github.com/huuthongdongthap/sadec-marketing-hub/actions/workflows/deploy.yml)

---

## 🎯 Tổng quan

**Container Caffe Sa Đéc** là mô hình quán cafe container kết hợp công nghệ 4.0:
- 📱 **Online Menu & Order** — Đặt hàng qua QR code, không cần chờ
- 💳 **Thanh Toán Số** — VNPay, MoMo, PayOS tích hợp đầy đủ
- 🖥️ **KDS (Kitchen Display System)** — Bếp nhận order realtime
- ⭐ **Loyalty Program** — Tích điểm đổi quà, tier system
- 📅 **Table Reservation** — Đặt bàn trước
- 🚚 **Delivery Tracking** — Theo dõi đơn giao hàng
- 📊 **Analytics Dashboard** — Báo cáo doanh thu realtime

> Forked từ VIBE CODING Café — thuộc hệ sinh thái **Mekong CLI / Sadec Marketing Hub**.

## 📋 Business Blueprint

Chi tiết kế hoạch kinh doanh 25 bước xem tại: `plans/company-blueprint/plan.md`

**Stage:** Zero→PSF
**ICP:** Khách hàng 18-35 tuổi tại Sa Đéc, Đồng Tháp
**Moat:** Concept container độc đáo + Loyalty program gamification

### Success Metrics

| Metric | Target |
|--------|--------|
| Daily Orders | 500 |
| Monthly Revenue | 50M VND |
| Avg Order Value | 45K VND |
| Loyalty Enrollment | 40% |
| Online Order % | 40% |
| Fulfillment Time | < 8 min |

## 💻 Open Source Arsenal (Tech Stack)
F&B CAFFE CONTAINER sử dụng 100% phần mềm mã nguồn mở để tối ưu hóa 90% chi phí SaaS.
Toàn bộ chi tiết hệ thống nằm ở file: [**TECH_STACK.md**](TECH_STACK.md)

12 Trụ cột cốt lõi:
1. **Odoo (POS/ERP/CRM)** - Quản trị toàn diện.
2. **Cal.com** - Đặt lịch phòng họp & sự kiện.
3. **OpenWISP** - Quản lý WiFi Marketing.
4. **pretix** - Bán vé Workshop/Sự kiện.
5. **TastyIgniter** - Hệ thống Online Ordering.
6. **Frigate & Home Assistant** - Camera AI và IoT.
*(Xem thêm 6 pillars khác trong TECH_STACK.md)*

## 🚀 Infrastructure
Thư mục `infrastructure/` chứa các cấu hình (Docker Compose) cơ bản để triển khai:
- [Docker Compose Bootstrap](infrastructure/docker-compose-bootstrap.yml): Cấu hình Odoo + PostgreSQL local.

## 📄 Project Brief
Hồ sơ thiết kế dự án (Concept, 2D/3D Layout, Ngân sách):
- Mở file: [project-brief.html](project-brief.html)

## 🔗 Mekong CLI Integration
Dự án này thuộc hệ sinh thái **Mekong CLI Framework** và được quản lý qua `mekong.config.yaml`.

```
mekong-cli/
└── apps/
    └── fnb-caffe-container/   ← Đường dẫn dự án
        ├── mekong.config.yaml  ← Config trỏ về Mekong CLI
        ├── index.html
        ├── styles.css
        ├── script.js
        ├── infrastructure/
        └── ...
```

---
*Tài liệu nội bộ — Mekong CLI Framework / Sadec Marketing Hub.*
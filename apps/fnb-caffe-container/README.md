# F&B CAFFE CONTAINER — Sa Đéc 🚀

> Hệ thống quản lý quán cafe container hiện đại — Đặt hàng online, thanh toán số, KDS realtime, Loyalty program

**Target:** 500 đơn/ngày | 50M VND/tháng

[![Build Passing](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/huuthongdongthap/sadec-marketing-hub/actions)
[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/huuthongdongthap/sadec-marketing-hub/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

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

## ✨ Features

- **QR Order** — Đặt hàng qua QR code tại bàn
- **Digital Payments** — VNPay, MoMo, PayOS integration
- **KDS Dashboard** — Kitchen display system realtime
- **Loyalty Program** — Points, rewards, tier system
- **Table Reservation** — Booking system
- **Delivery Tracking** — Order delivery status
- **Analytics** — Revenue dashboard & reports
- **Responsive Design** — Mobile-first UI

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Edge** | Cloudflare Workers |
| **Database** | Cloudflare D1 (SQLite) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Payments** | VNPay, MoMo, PayOS APIs |
| **Deployment** | Cloudflare Pages + Wrangler CLI |

## 🚀 Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

## 📁 Project Structure

```
fnb-caffe-container/
├── index.html          # Main landing page
├── menu.html           # Menu page
├── checkout.html       # Checkout page
├── dashboard/          # KDS & analytics dashboard
│   ├── index.html
│   └── dashboard.js
├── js/                 # Frontend JavaScript modules
│   ├── cart.js
│   ├── checkout.js
│   ├── menu.js
│   ├── kds-app.js
│   └── i18n.js
├── infrastructure/     # Docker Compose configs
├── tests/              # Test suite
└── worker/             # Cloudflare Worker (Edge API)
    └── src/
        └── index.js
```

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

---

*Tài liệu nội bộ — Mekong CLI Framework / Sadec Marketing Hub.*

---
title: "VIBE CODING Café — Full Tech Stack Deployment"
description: "Triển khai 12-pillar OSS infrastructure cho café + coworking Sa Đéc, target 10 tỷ VND/năm"
status: pending
priority: P1
effort: 3w
branch: master
tags: [vibe-coding-cafe, odoo, docker, iot, coworking, vietnam]
created: 2026-02-25
---

# VIBE CODING Café — Implementation Plan

**Location:** 91 Hùng Vương, P. Tân Phú Đông, TP. Sa Đéc, Đồng Tháp
**Goal:** 10 tỷ VND/năm từ 6 nguồn: Café, Coworking, Events, Meeting Rooms, Online, Ads
**Software Cost:** ~700k VND/tháng (100% OSS)

## Phases

| Phase | Title | Status | Effort |
|-------|-------|--------|--------|
| [01](./phase-01-core-infrastructure.md) | Core Infrastructure (Server + Docker + Nginx + SSL) | pending | 2d |
| [02](./phase-02-odoo-setup.md) | Odoo 17 POS + ERP + CRM + E-invoicing | pending | 4d |
| [03](./phase-03-booking-wifi-events.md) | Cal.com + OpenWISP + pretix | pending | 3d |
| [04](./phase-04-iot-signage-marketing.md) | Home Assistant + Frigate + Xibo + Marketing | pending | 4d |
| [05](./phase-05-payments-loyalty.md) | Payments + TastyIgniter + Open Loyalty | pending | 3d |

## Architecture Overview

```
Internet
   │
   ▼
[Nginx Reverse Proxy + SSL (Let's Encrypt)]
   │
   ├── odoo.vibecafe.vn:8069     → Odoo 17 (POS/ERP/CRM)
   ├── booking.vibecafe.vn:3000  → Cal.com v4
   ├── events.vibecafe.vn:8080   → pretix
   ├── order.vibecafe.vn:8082    → TastyIgniter
   ├── wifi.vibecafe.vn          → OpenWISP
   ├── cms.vibecafe.vn           → Xibo CMS
   ├── social.vibecafe.vn        → Mixpost + Mautic
   └── loyalty.vibecafe.vn       → Open Loyalty

[Raspberry Pi 4 — IoT Layer]
   ├── Home Assistant OS (port 8123)
   ├── Frigate NVR + Google Coral USB
   └── Xibo Player (menu boards)
```

## Hardware Requirements

| Component | Spec |
|-----------|------|
| Main Server | 4 CPU cores, 8GB RAM, 50GB SSD |
| RPi 4 (IoT) | 4GB RAM, 64GB SD, Google Coral USB |
| Access Points | UniFi/MikroTik (OpenWRT compatible) |
| Cameras | RTSP-compatible IP cams |

## Key Dependencies
- Phase 01 → PHẢI xong trước mọi phase khác
- Phase 02 → Core business (bắt đầu trước Phase 03/04/05)
- Phase 03/04/05 → Có thể song song sau Phase 02

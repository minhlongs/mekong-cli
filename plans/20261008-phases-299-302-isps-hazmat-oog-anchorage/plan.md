---
title: "Phases 299-302: ISPS, Hazmat, OOG & Anchorage"
description: "Implementation plan for Port Security, Hazardous Waste, OOG Stevedoring & Anchorage capacities."
status: pending
priority: P2
effort: 3d
branch: HEAD
tags: [maritime, security, hazmat, oog, anchorage]
created: 2026-10-08
---

# Overview Plan: Phases 299-302

**Mục tiêu:** Áp dụng thiết kế kiến trúc "Simplest Viable" (YAGNI, KISS, DRY) cho các nghiệp vụ cảng biển và hàng hải quan trọng, tập trung vào bảo mật ISPS, quản lý rác thải nguy hại Hazmat, phí hàng quá khổ OOG, và quản lý neo đậu theo GRT.

## Các Giai Đoạn (Phases)

### Phase 299: ISPS Security & DoS Tracking
- **Trạng thái:** Pending
- **Nội dung:** Quản lý cấp độ an ninh cảng (ISPS Security Level) và tracking chứng chỉ DoS (Declaration of Security).
- **Chi tiết:** [phase-299-isps-security.md](./phase-299-isps-security.md)

### Phase 300: Hazmat Waste Manifest & Port Clearance
- **Trạng thái:** Pending
- **Nội dung:** Quét biên bản rác thải nguy hại (HazmatWasteManifest) và chặn Cấp phép rời cảng (Port Clearance) nếu thiếu Disposal Receipt.
- **Chi tiết:** [phase-300-hazmat-waste.md](./phase-300-hazmat-waste.md)

### Phase 301: OOG Stevedoring & Overtime Multipliers
- **Trạng thái:** Pending
- **Nội dung:** Tính phí bốc dỡ hàng quá khổ (OOG) với việc tích hợp các hệ số nhân cơ bản (Multiplier) & chi phí làm ngoài giờ (overtime).
- **Chi tiết:** [phase-301-oog-stevedoring.md](./phase-301-oog-stevedoring.md)

### Phase 302: Anchorage Booking by GRT
- **Trạng thái:** Pending
- **Nội dung:** Booking slot ở khu neo đậu (phao neo) sử dụng thuật toán tổng dung tích (GRT - Gross Tonnage) dựa trên capacity bucket đơn giản.
- **Chi tiết:** [phase-302-anchorage-booking.md](./phase-302-anchorage-booking.md)

---
*Ghi chú:*
- Ưu tiên tối đa YAGNI, không xây dựng logic dư thừa ngoài đặc tả.
- DRy: Các hàm validation có thẻ sử dụng chung giữa các module nên được gom nhóm hợp lý.

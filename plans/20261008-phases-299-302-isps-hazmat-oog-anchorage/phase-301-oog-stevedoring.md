---
title: "Phase 301: OOG Stevedoring & Overtime"
description: "Calculate OOG handling fees applying multiplier and overtime."
---

# Phase 301: OOG Stevedoring & Overtime Multipliers

## Context links
- [Overview Plan](./plan.md)

## Requirements
- Tính phí bốc xếp cảng (Stevedoring) dành riêng cho Hàng quá khổ (OOG - Out Of Gauge).
- Áp dụng Hệ số nhân (Multiplier) tuỳ vào mức độ quá khổ (Ví dụ: Overheight = x1.5, Overwidth = x1.7, Multiple OOG = x2.0).
- Áp dụng phí Overtime nếu quá trình bốc dỡ vào khung giờ Night Shift, Weekend, Holiday (+20% đến +50%).

## Architecture
- Không thiết kế rule engine động phức tạp tránh phiền hà (YAGNI / KISS).
- Tạo base rate config/DB table nhỏ cho giá Standard. 
- Xây dựng một utility module `calculateOogStevedoringFee(base_rate, oog_type, time_of_operation)`.
- Áp dụng các multipliers theo thứ tự nhân dồn (hoặc cộng dồn theo Specs thực tế, mặc định chọn nhân dồn cơ bản để an toàn).

## Related Code Files
- `src/lib/tariffs/stevedoring-rates.ts` (Create/Modify - lưu công thức base)
- `src/app/api/billing/stevedoring/route.ts` (Modify - bổ sung logic OOG billing)
- `src/seed/db/schema/tariffs.ts` (Modify - Thêm config OOG_MULTIPLIER)

## Todo List
- [ ] Định nghĩa các hằng số hoặc schema cho OOG Multipliers và Overtime Multipliers.
- [ ] Viết hàm tính toán đơn giản, nhận parameter đầu vào trực tiếp (baseRate, oogEnum, timestamp/shiftType) trả ra TotalFee.
- [ ] Phối hợp vào Endpoint tính phí (Billing Endpoint) của Invoice Lượt cập.
- [ ] Viết unit tests các case: OOG ban ngày vào ngày thường, OOG vào ban đêm Cuối tuần (cộng dồn hệ số cao nhất).
- [ ] Đảm bảo đáp ứng đầy đủ DRY: không code lại phần parse datetime tính overtime của core sẵn có.

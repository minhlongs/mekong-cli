---
title: "Phase 302: Anchorage Booking by GRT"
description: "Booking slots at anchorage using total GRT capacity buckets algorithm."
---

# Phase 302: Anchorage Booking by GRT (Gross Tonnage)

## Context links
- [Overview Plan](./plan.md)

## Requirements
- Vùng phao neo đậu (Anchorage Area) thay vì tính số lượng slot cố định (v.d 10 slots), sẽ tính sức chứa sử dụng thuật toán tổng GRT tối đa.
- Tàu khi yêu cầu booking sẽ truyền vào GRT. 
- Hệ thống xét tổng GRT của tất cả các tàu đang/sẽ book chung khung thời gian. Nếu <= Max Capacity GRT của khu neo đậu = Chấp nhận. Nếu > Max = Báo hết chỗ (Waitlist).

## Architecture
- Logic đơn giản: `AnchorageArea` DB entity có trường `max_grt_capacity`.
- API booking sẽ quét mốc thời gian overlapping `(start_time, end_time)`, dùng SQL SUM(grt) các record Booking đã confirm để tính `current_allocated_grt`.
- Nếu `current_allocated_grt + incoming_grt <= max_grt_capacity`, cho phép lưu Booking.
- Khóa (Lock) cơ sở dữ liệu nếu có High Concurrency (dùng Transactions hoặc Optimistic Locking tuỳ DB) để tránh overbooking ảo. (KISS: transaction serializable mức thấp nếu tải ít).

## Related Code Files
- `src/seed/db/schema/anchorage-area.ts` (Modify - Add max_grt_capacity)
- `src/seed/db/schema/anchorage-booking.ts` (Modify/Create - slot booking table)
- `src/app/api/anchorage/booking/route.ts` (Create)
- `src/lib/maritime/capacity-bucket.ts` (Create - Thuật toán check overlap và bucket capacity)

## Todo List
- [ ] Thêm biến `max_grt_capacity` cho bảng khu neo phao.
- [ ] Viết hàm tính tổng GRT dựa theo overlapping time (intersection query).
- [ ] Xây dựng Booking Route xử lý transaction an toàn.
- [ ] Cập nhật bảng trả về cho Vessel Schedule Dashboard về tình trạng phao neo.
- [ ] Viết ít nhất 3 unit tests: Booking trống, Booking vừa đủ Capacity, Booking tràn (Overlap time và Non-overlap).

---
title: "Phase 299: ISPS Security & DoS Tracking"
description: "Implementation of ISPS Security Levels & Declaration of Security tracking."
---

# Phase 299: ISPS Security Level & DoS Tracking

## Context links
- [Overview Plan](./plan.md)

## Requirements
- Hỗ trợ lưu trữ và thay đổi cấp độ an ninh cảng (ISPS Security Level: 1, 2, 3).
- Cập nhật, tạo mới và tracking chứng chỉ DoS (Declaration of Security) cho từng lượt tàu cập cảng/neo đậu.
- Đảm bảo tàu không được thực hiện hoạt động nếu cấp độ ISPS không khớp hoặc chưa có DoS hợp lệ trong trường hợp Level 2/3.

## Architecture
- Sử dụng mô hình lưu trữ 1 Table/Collection cho Cấp độ an ninh cảng (PortFacilitySecurity).
- Bổ sung trường thông tin `dos_issued` (Boolean/Date) và `dos_file_reference` (String) trực tiếp trên `PortCall` hoặc `VesselVisit` record.
- **Simplest Viable:** Không tạo quá mức các object Security phức tạp, dùng Enum cho Port Level. 

## Related Code Files
- `src/seed/db/schema/isps-port-security.ts` (Create)
- `src/seed/db/schema/vessel-visit.ts` (Modify - Update DoS fields)
- `src/app/api/isps/route.ts` (Create - Update levels)
- `src/app/api/dos/route.ts` (Create - DoS issuance)
- `src/lib/isps/isps-validation.ts` (Create - Check DoS validity when Level >= 2)

## Todo List
- [ ] Định nghĩa Enum cho ISPS (LEVEL_1, LEVEL_2, LEVEL_3).
- [ ] Thêm các trường dữ liệu cho DoS tracking vào DB schema của lượt cập cảng.
- [ ] Viết API route thay đổi Cấp độ an ninh cảng.
- [ ] Viết hàm tính toán/quy định chặn hành động khai thác nếu thiếu chứng chỉ DoS hợp lệ.
- [ ] Cập nhật UI cơ bản để cập nhật thông tin chứng chỉ DoS.
- [ ] Viết unit tests đảm bảo security lock hoạt động mượt mà.

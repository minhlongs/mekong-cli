---
title: "Phase 300: Hazmat Waste Manifest & Port Clearance"
description: "Scan Hazardous Waste Manifests & block Port Clearance if Disposal Receipt is missing."
---

# Phase 300: Hazmat Waste Manifest & Port Clearance

## Context links
- [Overview Plan](./plan.md)

## Requirements
- Ghi nhận thông tin HazmatWasteManifest và số lượng rác nguy hại từ tàu.
- Bắt buộc phải có `DisposalReceipt` (biên lai xử lý) hợp lệ từ đơn vị nhận rác.
- Chặn lệnh Port Clearance (giấy phép rời cảng) nếu báo cáo có rác nguy hại xuống cảng nhưng chưa có Receipt.

## Architecture
- **Simplest Viable:** Thêm bảng `HazmatWasteManifest` nhẹ nhàng (`vessel_visit_id`, `type_of_waste`, `quantity`, `disposal_receipt_url`, `cleared`).
- Logic `Port Clearance`: hook rẽ nhánh kiểm tra tổng số record trong `HazmatWasteManifest` nơi `vessel_visit_id` tương ứng và `disposal_receipt_url` đang trống.
- **Data flow:** Tàu nhập cảnh -> Khai báo Hazmat (nếu có) -> Công ty môi trường cập nhật Receipt -> Lệnh xuất cảnh bị unlock.

## Related Code Files
- `src/seed/db/schema/hazmat-waste.ts` (Create - Waste Manifest schema)
- `src/app/api/port-clearance/route.ts` (Modify - Thêm điều kiện block)
- `src/app/api/hazmat/receipt/route.ts` (Create - API để update Disposal Receipt)

## Todo List
- [ ] Thiết kế schema `HazmatWasteManifest`.
- [ ] Tạo API lấy và lưu thông tin về lượng rác xả bờ.
- [ ] Xây dựng Endpoint upload/confirm mã số biên lai xử lý (disposal receipt reference).
- [ ] Chỉnh sửa logic cấp `Port Clearance`: Viết method query check `hasPendingHazmatWaste(visitId)`.
- [ ] Viết Tests để verify rằng: Có rác + Thiếu receipt = FAIL xuất cảnh. Quá trình thu dọn ok = PASS.

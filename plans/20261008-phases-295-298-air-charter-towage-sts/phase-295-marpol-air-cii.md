---
title: "Phase 295: MARPOL Air CII & ECA"
description: "Tracker hạng CII Rating A-E và BunkerSulphurLog cho vùng ECA"
status: pending
priority: P1
effort: 1d
branch: main
tags: [maritime, marpol, cii, eca]
created: 2026-10-07
---

## Context Links
- [Overview Plan](./plan.md)

## Overview
- **Priority**: P1
- **Status**: Pending
- **Description**: Phát triển phân hệ theo dõi chỉ số cường độ carbon (CII) xếp hạng A-E và cảnh báo Kế hoạch Quản lý Năng lượng Tàu (SEEMP) cùng nhật ký lưu huỳnh nhiên liệu (Bunker Sulphur Log) cho vùng ECA.

## Key Insights
- Chỉ số CII tính bằng gCO2/dwt.nm, đánh giá hằng năm. Cảnh báo nếu hạng E (1 năm) hoặc D (3 năm liên tiếp).
- Nhiên liệu ECA yêu cầu nồng độ lưu huỳnh (Sulphur) không vượt quá 0.1% m/m.

## Requirements
- Tính toán cấp CII dựa trên tiêu thụ nhiên liệu.
- Cảnh báo SEEMP khi vi phạm chuẩn (Rating D 3 năm, hoặc E).
- Ghi nhận và kiểm tra BunkerSulphurLog, đảm bảo hàm lượng lưu huỳnh <= 0.1% khi ở ECA.

## Architecture
- `CiiRatingTracker`: Khởi tạo từ BaseEngine hoặc Calculator, xử lý logic CO2.
- `BunkerSulphurLog`: DTO / Data schema kèm logic validation ECA compliance.

## Related Code Files
- Tạo: `src/engines/maritime/marpol_air_engine.py` (hoặc `.ts` tuỳ setup)
- Tạo: `tests/maritime/test_marpol_air.py`

## Implementation Steps
1. Khởi tạo class `CiiRatingTracker`.
2. Viết logic tính CII và xếp hạng A-B-C-D-E dựa theo threshold chuẩn.
3. Thêm hàm kiểm tra cảnh báo SEEMP.
4. Xây dựng struct `BunkerSulphurLog` và logic check < 0.1%.
5. Cập nhật CLI commands để gọi engine này nếu cần.
6. Hoàn thiện Unit Tests.

## Todo List
- [ ] Implement `CiiRatingTracker` A-E logic.
- [ ] Implement SEEMP alert logic.
- [ ] Implement `BunkerSulphurLog` validation.
- [ ] Viết test `test_marpol_air.py`.

## Success Criteria
- Test runner báo xanh (green).
- Cảnh báo chuẩn xác với Rating D (3 năm) & E (1 năm).
- Bắt lỗi chính xác BunkerSulphur > 0.1% ở ECA.

## Risk Assessment
- Rủi ro ngoại lệ khi vessel nghỉ dài (Off-hire ảnh hưởng d.nm). Mitigation: Coi đó là YAGNI, chỉ tính dựa trên dữ liệu nhập.

## Security Considerations
- Không có dữ liệu mật.

## Next Steps
- Pass qua Phase 296.

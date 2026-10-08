---
title: "Phase 296: Charter Party Financials"
description: "Quản lý OffHireEvent cho Time CP và DemurrageCalculation cho Voyage CP"
status: pending
priority: P1
effort: 1d
branch: main
tags: [charter-party, financials, maritime]
created: 2026-10-07
---

## Context Links
- [Overview Plan](./plan.md)

## Overview
- **Priority**: P1
- **Status**: Pending
- **Description**: Module tính toán tài chính cho hợp đồng thuê tàu. Bao gồm trừ tiền thuê/hoàn rớt dầu với Time Charter Party và tính thưởng/phạt xếp dỡ (Demurrage) với Voyage CP.

## Key Insights
- Time CP Off-hire: Ngừng trả tiền thuê, tính số dư bunker consume bị rớt lại trong giai đoạn off-hire.
- Voyage CP: Thời gian cho phép (Laytime) vs Thời gian thực tế. Chênh lệch sẽ ra Demurrage hoặc Despatch.

## Requirements
- `OffHireEvent`: Lưu lại start_time, end_time, bunker_consumed, hire_rate.
- Công thức trừ Off-hire: `(end - start) * hire_rate + bunker_consumed * bunker_price`.
- `DemurrageCalculation`: `actual_time > laytime` -> (actual - laytime) * rate. 

## Architecture
- `TimeCharterEngine`: Xử lý Off-Hire.
- `VoyageCharterEngine`: Xử lý Laytime/Demurrage.

## Related Code Files
- Tạo: `src/engines/maritime/charter_party_engine.py`
- Tạo: `tests/maritime/test_charter_party.py`

## Implementation Steps
1. Xây dựng data model `OffHireEvent` và hàm tính tổng thiệt hại do Off-Hire dựa trên hire fee rate và bunker rớt.
2. Xây dựng logic `DemurrageCalculation` trừ Laytime để ra số tiền phạt.
3. Tạo báo cáo rút gọn (FinancialSummary).
4. Viết Unit Test.

## Todo List
- [ ] Implement `TimeCharterEngine.calculate_off_hire_deduction`.
- [ ] Implement `VoyageCharterEngine.calculate_demurrage`.
- [ ] Viết test `test_charter_party.py`.

## Success Criteria
- Kiểm thử logic Demurrage >= 0 (nếu < 0 thì là Despatch nếu áp dụng, tạm KISS chỉ tính phạt).
- Tính đúng số dư Refund Off-hour + Bunker.

## Risk Assessment
- Rủi ro làm phức tạp timezone handling: Mitigation: Dùng UNIX epoch time hoặc số giờ tuyệt đối (hours).

## Security Considerations
- Che giấu log API phi tập trung.

## Next Steps
- Triển khai Phase 297 Towage & Drydock.

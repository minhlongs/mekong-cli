---
title: "Phase 297: Towage & Drydock Tariffs"
description: "Phí lai dắt TT 39/2023 & RepairBudgetVariance cho lên đà"
status: pending
priority: P1
effort: 1d
branch: main
tags: [towage, drydock, tariffs, maritime]
created: 2026-10-07
---

## Context Links
- [Overview Plan](./plan.md)

## Overview
- **Priority**: P1
- **Status**: Pending
- **Description**: Module xử lý phí lai dắt dựa trên khung Thông tư 39/2023 (TT 39/2023) và công cụ tính sai lệch ngân sách sửa chữa trên đà (RepairBudgetVariance).

## Key Insights
- Khung giá lai dắt theo TT 39/2023 quy định theo GRT hoặc công suất (HP), chia theo giờ, vùng cảng.
- Ngân sách sửa chữa (Drydock): Thực tế (Actual) so với Kế hoạch (Planned) tạo ra Variance.

## Requirements
- Mapping fee lai dắt theo Thông tư mới nhất (TT 39/2023).
- Input: GRT/HP, thời gian lai dắt -> Output: Phí thu.
- Tính % budget variance khi drydock: `(Actual - Planned) / Planned * 100`.

## Architecture
- `TowageTariffEngine`: class xử lý giá cố định / custom giá lai dắt.
- `DrydockVarianceEngine`: class quản lý sửa chữa.

## Related Code Files
- Tạo: `src/engines/maritime/towage_drydock_engine.py`
- Tạo: `tests/maritime/test_towage_drydock.py`

## Implementation Steps
1. Xác định struct giá TT 39 (BaseRate + Hour * VariableRate).
2. Xây dựng logic `calculate_towage_fee(grt, hp, hours, tier)`.
3. Xây dựng module `RepairBudgetVariance` tính toán chênh lệch CapEx/OpEx lên đà làm sạch/sơn gầm.
4. Viết Unit Test (All tests green).

## Todo List
- [ ] Implement `TowageTariffEngine` TT39 rules.
- [ ] Implement `DrydockVarianceEngine`.
- [ ] Viết test `test_towage_drydock.py`.

## Success Criteria
- Sai số phí <= 0.01 cho float values.
- Trả về đúng variance percent dương/âm.

## Risk Assessment
- Các phụ phí ngày lễ, ngoài giờ: Theo YAGNI, chỉ xử lý base multiplier parameter.

## Security Considerations
- N/A

## Next Steps
- Triển khai STS Manifest.

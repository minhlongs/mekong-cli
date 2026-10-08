---
title: "Phase 298: STS & Customs Manifest"
description: "Vận hành Ship-to-Ship (STS) Permit & Split Manifest Hải quan"
status: pending
priority: P1
effort: 1d
branch: main
tags: [sts, customs, manifest, maritime]
created: 2026-10-07
---

## Context Links
- [Overview Plan](./plan.md)

## Overview
- **Priority**: P1
- **Status**: Pending
- **Description**: Module hỗ trợ Ship-to-Ship (STS) Permit clearance và tách/chia bản khai hàng hóa (SplitManifest) từ tàu mẹ sang tàu con, phù hợp luồng Hải quan VASSCM.

## Key Insights
- STS (Ship-to-Ship Transfer) đòi hỏi Permit từ Cảng vụ trước khi tiến hành bơm rót.
- Manifest của tàu mẹ (M) sẽ phải Split ra các tàu con (D1, D2) theo lượng Bill of Lading (CGO) chia tách.

## Requirements
- `StsPermit`: DTO / Entity quản lý Permit có hiệu lực (Approved/Pending/Rejected) và thời hạn.
- `SplitManifest`: Logic nhận 1 Tàu Mẹ MasterBL và list Khố lượng Tàu Con, kiểm tra: Tổng lượng chia <= Lượng gốc.

## Architecture
- `StsTransferEngine`: Xử lý phân bổ hàng hóa manifest.
- Tuân thủ OOP: `Manifest`, `SplitAllocation`.

## Related Code Files
- Tạo: `src/engines/maritime/sts_customs_engine.py`
- Tạo: `tests/maritime/test_sts_customs.py`

## Implementation Steps
1. Xây dựng logic quản lý trạng thái `StsPermit`.
2. Tạo hàm `split_manifest(mother_manifest, daughter_allocations)` ném ngoại lệ nếu phân bổ vượt over-allocation.
3. Validate đầu ra khớp 100% dung lượng MasterBL (hoặc có số dư trên tàu mẹ).
4. Viết Unit Test.

## Todo List
- [ ] Implement `StsPermit` struct + state validation.
- [ ] Implement `split_manifest` logic & balance checks.
- [ ] Viết test `test_sts_customs.py`.

## Success Criteria
- Split Manifest trả về các kiện BL con chính xác.
- Raise `ValueError` nếu số lượng chia tách lớn hơn tổng hàng hiện có.

## Risk Assessment
- Xử lý thiếu hụt (Loss during STS): Theo YAGNI, tạo thêm 1 trường "sts_loss" tự nhập tay vào allocation.

## Security Considerations
- N/A

## Next Steps
- Review plan toàn diện cả 4 phases trước khi tiến hành code implementation.

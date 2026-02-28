---
title: "Well AGI Master GO LIVE Plan"
description: "Kế hoạch chi tiết để đưa dự án Well Nexus lên môi trường production với chất lượng 10x, zero bug và build thành công."
status: in-progress
priority: P1
effort: 4h
branch: master
tags: [well, agi, golive, production]
created: 2026-02-28
---

# Well AGI Master GO LIVE Plan

## Tầm nhìn
Đưa dự án Well Nexus lên production với tiêu chuẩn cao nhất: không lỗi build, không lỗi test, không tech debt, và sẵn sàng phục vụ người dùng cuối.

## Hiện trạng (Findings)
- **Build**: Đang gặp lỗi `[vite:define] The service was stopped` tại `src/lib/supabase.ts`.
- **Tests**: 349/349 tests pass (Tuyệt vời).
- **Type Safety**: Tốt (0 `any`, 0 `@ts-ignore`).
- **Tech Debt**:
    - 17 `console.` calls cần được xử lý (chuyển sang logger hoặc xóa).
    - `eslint_report.json` có kích thước lớn, cần kiểm tra các lỗi lint.
- **i18n**: Đã pass validation.

## Các giai đoạn thực hiện

### [Phase 01: Sửa lỗi Build & Infra](./phase-01-fix-build-infra.md)
- **Mục tiêu**: Build project thành công mà không có lỗi esbuild/vite.
- **Tasks**:
    - [ ] Điều tra nguyên nhân lỗi `[vite:define]`.
    - [ ] Tối ưu hóa `vite.config.ts` nếu cần.
    - [ ] Kiểm tra tài nguyên hệ thống (M1 RAM/Thermal).

### [Phase 02: Cleanup Tech Debt & Linting](./phase-02-cleanup-tech-debt.md)
- **Mục tiêu**: Xóa bỏ hoàn toàn console.log và sửa các lỗi lint quan trọng.
- **Tasks**:
    - [ ] Xử lý 17 lỗi `console.` (chuyển sang `authLogger` hoặc xóa).
    - [ ] Phân tích `eslint_report.json` và fix các lỗi nghiêm trọng.
    - [ ] Đảm bảo 0 lỗi lint trước khi deploy.

### [Phase 03: Production Hardening](./phase-03-production-hardening.md)
- **Mục tiêu**: Tăng cường bảo mật và hiệu năng cho production.
- **Tasks**:
    - [ ] Kiểm tra CSP headers trong `vercel.json`.
    - [ ] Xác thực các biến môi trường cho production.
    - [ ] Chạy audit bảo mật (npm audit).

### [Phase 04: Verification & Shipping](./phase-04-verification-shipping.md)
- **Mục tiêu**: Verify toàn bộ và thực hiện git push.
- **Tasks**:
    - [ ] `npm run build` thành công.
    - [ ] `npm test` thành công.
    - [ ] `gh run list` kiểm tra CI/CD GREEN.
    - [ ] Smoke test production site.

## Thành phần tham gia
- **Planner Agent**: Quản lý kế hoạch.
- **Developer Agent**: Thực thi code fix.
- **Tester Agent**: Chạy test suite.
- **Reviewer Agent**: Audit chất lượng code.

## Rủi ro & Giảm thiểu
- **Lỗi esbuild không rõ nguyên nhân**: Có thể do xung đột version hoặc tài nguyên. Giải pháp: Thử cô lập file bị lỗi hoặc update esbuild.
- **Downtime khi deploy**: Sử dụng PR preview của Vercel để verify trước khi merge main.

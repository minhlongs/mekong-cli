---
title: "WellNexus Go Live Fixes & Optimization"
description: "Resolve remaining lint warnings, security vulnerabilities, and optimize test execution for production readiness."
status: pending
priority: P1
effort: 2h
branch: master
tags: [wellnexus, go-live, bugfix, security, quality]
created: 2026-02-28
---

# WellNexus Go Live Fixes & Optimization

Dự án WellNexus MVP đã sẵn sàng cho việc triển khai, với build thành công và 100% test pass khi chạy trong môi trường cô lập. Kế hoạch này tập trung vào việc dọn dẹp các cảnh báo lint cuối cùng, cập nhật bảo mật và đảm bảo quy trình CI/CD ổn định.

## Hiện trạng (Audit Results)
- **Build**: ✅ Thành công (Vite + TSC)
- **Tests**: ✅ 349/349 pass (Yêu cầu chạy với `--pool=forks` để tránh treo trên M1)
- **Type Safety**: ✅ 100% (0 `: any`)
- **Tech Debt**: ✅ Tốt (0 TODO/FIXME)
- **Security**: ⚠️ 4 lỗ hổng HIGH trong devDependencies (glob, rollup, minimatch)
- **Lint**: ⚠️ 15 warnings (Chủ yếu là accessibility và react-hooks)

## Các bước thực hiện

### Phase 1: Fix Lint Warnings & Accessibility (60m)
Mục tiêu: Đạt 0 cảnh báo lint để đảm bảo chất lượng code cao nhất trước khi ship.

1. **Fix React Hook warnings**:
   - `src/components/Copilot/CopilotMessageList.tsx`: Sửa lỗi closure ref trong useEffect cleanup.
2. **Fix Accessibility (jsx-a11y)**:
   - Thêm `role="button"` và `onKeyDown` cho các element div/span có sự kiện click tại:
     - `src/components/PremiumNavigation/DesktopNav.tsx`
     - `src/components/ProductCard.tsx`
     - `src/components/ui/Aura.tsx`
     - `src/components/ui/CommandPalette.tsx`
     - `src/components/ui/Modal.test.tsx` (cả trong file test)
     - `src/components/checkout/__tests__/qr-payment-modal.test.tsx`
3. **Fix Misc**:
   - `src/components/Sidebar.tsx`: Xóa "image/photo" thừa trong thuộc tính alt.
   - `src/hooks/useLogin.ts`: Thay thế non-null assertion (`!`) bằng kiểm tra null an toàn.

### Phase 2: Security & Dependencies (30m)
Mục tiêu: Giải quyết các lỗ hổng bảo mật được báo cáo bởi npm audit.

1. Cập nhật các package có lỗ hổng bảo mật:
   ```bash
   npm audit fix
   # Nếu cần thiết:
   npm install rollup@latest glob@latest minimatch@latest --save-dev
   ```
2. Kiểm tra lại với `npm audit --audit-level=high`.

### Phase 3: Test Optimization (15m)
Mục tiêu: Đảm bảo bộ test chạy ổn định trên mọi môi trường.

1. Cập nhật `package.json` để script test mặc định sử dụng `--pool=forks` hoặc giới hạn concurrency nếu phát hiện chạy trên M1.
2. Cập nhật `vitest.config.ts` để tối ưu hóa tài nguyên.

### Phase 4: Final Verification (15m)
Mục tiêu: Xác nhận dự án đạt trạng thái GREEN hoàn toàn.

1. Chạy `npm run lint` -> Kết quả 0 warning.
2. Chạy `npm run build` -> Build thành công.
3. Chạy `npm test` -> 100% pass.

## Success Criteria
- [ ] 0 Lint warnings
- [ ] 0 High/Critical security vulnerabilities
- [ ] 100% Test pass (349+ tests)
- [ ] Build thành công không có lỗi TypeScript

## Risk Assessment
- Việc cập nhật `glob` lên bản 11 (breaking change cho `sharp-cli`) có thể gây xung đột. Cần kiểm tra kỹ script xử lý ảnh nếu có.
- Một số chỉnh sửa accessibility có thể ảnh hưởng đến style CSS nếu không cẩn thận với `role="button"`.

## Next Steps
- Triển khai Phase 1 ngay lập tức.
- Sau khi hoàn thành, thực hiện commit với tag `final-push-go-live`.

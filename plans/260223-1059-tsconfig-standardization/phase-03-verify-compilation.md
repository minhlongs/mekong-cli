# Phase 3: Kiểm Tra Biên Dịch & Sửa Lỗi (Verification)

## Context Links
- Parent Plan: [plan.md](./plan.md)
- Dependency: Phase 1 & Phase 2 phải hoàn thành.

## Overview
- **Priority**: P1
- **Status**: pending
- **Description**: Chạy lệnh kiểm tra type check trên toàn bộ monorepo và các sub-apps để xác nhận không bị phá vỡ cấu trúc biên dịch.

## Key Insights
- Theo **Binh Pháp (作戰 - Waging War)**: Type safety là cốt lõi, không được phép có lỗi Type sau khi cập nhật cấu hình.
- Phải dùng lệnh `npx tsc --noEmit` hoặc tương đương cho từng workspace/app.

## Requirements
- Xác minh toàn bộ 8 apps không có lỗi cấu hình và type errors sinh ra từ việc chuẩn hoá.
- Sửa bất kỳ lỗi (Fixes) nào phát sinh (giới hạn sửa lỗi không vượt quá 5 files mỗi lần chạy).

## Architecture
- TypeScript Verification Pipeline.

## Related Code Files
- Files có thể phát sinh lỗi type (N/A cho đến khi chạy lệnh test).

## Implementation Steps
1. Chạy lệnh `npx tsc --noEmit` ở root (nếu có config root).
2. Chạy lệnh `npx tsc --noEmit` lần lượt vào từng thư mục của 8 apps:
   - `apps/84tea`
   - `apps/agencyos-landing`
   - `apps/agencyos-web`
   - `apps/anima119`
   - `apps/apex-os`
   - `apps/com-anh-duong-10x`
   - `apps/openclaw-worker`
   - `apps/sophia-proposal`
3. Ghi nhận lỗi type (nếu có).
4. Phân tích nguyên nhân (do `tsconfig.base.json` quá strict hay thiếu `lib`, `types`).
5. Thực hiện Fix lỗi (đảm bảo luật max 5 files).

## Todo List
- [ ] Verify `apps/84tea`
- [ ] Verify `apps/agencyos-landing`
- [ ] Verify `apps/agencyos-web`
- [ ] Verify `apps/anima119`
- [ ] Verify `apps/apex-os`
- [ ] Verify `apps/com-anh-duong-10x`
- [ ] Verify `apps/openclaw-worker`
- [ ] Verify `apps/sophia-proposal`
- [ ] Fix Errors (if any)

## Success Criteria
- Lệnh biên dịch tĩnh ở toàn bộ 8 apps đều cho kết quả thành công (0 errors).

## Risk Assessment
- Xung đột type thư viện có thể khiến hàng loạt file bị lỗi.
- Mitigation: Nếu phát hiện lỗi quy mô lớn, lùi lại điều chỉnh `tsconfig.base.json` cho lỏng bớt (ví dụ `strict` có thể tắt tạm nếu base code cũ chưa đạt chuẩn, tuỳ thuộc vào tình trạng hiện tại).

## Security Considerations
- Đảm bảo tính toàn vẹn của Type System.

## Next Steps
- Report "GREEN" cho quá trình chuẩn hoá.
- Tiến hành commit thông qua CC CLI `/check-and-commit`.

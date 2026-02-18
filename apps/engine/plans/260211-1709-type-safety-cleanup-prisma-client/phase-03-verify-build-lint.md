# Phase 03: Verify Build & Lint

**Overview**
- Priority: High
- Current Status: Pending
- Description: Kiểm tra toàn bộ dự án sau khi sửa lỗi Type Safety.

**Requirements**
- [ ] Chạy lệnh `npm run build` hoặc `tsc` để kiểm tra lỗi biên dịch.
- [ ] Chạy lint để đảm bảo code sạch.

**Implementation Steps**
1. Chạy `npx tsc --noEmit` tại thư mục `apps/engine`.
2. Sửa các lỗi phát sinh do việc thắt chặt kiểu dữ liệu.
3. Chạy `npm run lint` (nếu có).

**Todo List**
- [ ] Run tsc
- [ ] Fix regression errors
- [ ] Final verification

**Success Criteria**
- Build pass với 0 lỗi TypeScript liên quan đến các file đã sửa.

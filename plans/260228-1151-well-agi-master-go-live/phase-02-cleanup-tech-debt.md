# Phase 02: Cleanup Tech Debt & Linting

## Overview
- Priority: P2
- Status: Pending
- Description: Dọn dẹp codebase, xóa console.log và fix lỗi lint.

## Key Insights
- Hiện có 17 `console.` calls trong codebase.
- `eslint_report.json` quá lớn (2MB) cho thấy còn nhiều vấn đề về linting.

## Implementation Steps
1. Sử dụng grep để định vị chính xác 17 lỗi `console.log`.
2. Thay thế bằng `authLogger` hoặc xóa nếu không cần thiết.
3. Chạy `npm run lint` và fix các lỗi Auto-fixable trước.
4. Review các lỗi thủ công và xử lý.

## Todo List
- [ ] Xóa/Thay thế 17 console calls.
- [ ] Chạy `npm run lint -- --fix`.
- [ ] Verify `npm run lint` trả về 0 lỗi (hoặc chỉ còn warning không đáng kể).

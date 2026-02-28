# Phase 01: Sửa lỗi Build & Infra

## Overview
- Priority: P1
- Status: Pending
- Description: Giải quyết triệt để lỗi build `[vite:define] The service was stopped`.

## Key Insights
- Lỗi xuất hiện tại `src/lib/supabase.ts` khi chạy `vite build`.
- Có thể liên quan đến việc thay thế chuỗi (define) trong esbuild hoặc tài nguyên bộ nhớ bị thiếu.

## Implementation Steps
1. Thử chạy build lại với log verbose để xem chi tiết lỗi.
2. Kiểm tra xem có circular dependency nào liên quan đến `supabase.ts` không.
3. Thử move logic `import.meta.env` ra một file config riêng nếu lỗi vẫn tiếp diễn.
4. Đảm bảo các biến môi trường `VITE_SUPABASE_URL` và `VITE_SUPABASE_ANON_KEY` được định nghĩa đúng trong build environment.

## Todo List
- [ ] Chạy `npm run build` một lần nữa để confirm lỗi.
- [ ] Inspect `src/lib/supabase.ts` để tìm các pattern lạ.
- [ ] Thử gỡ bỏ `manualChunks` liên quan đến supabase trong `vite.config.ts` để debug.
- [ ] Fix lỗi và verify build pass.

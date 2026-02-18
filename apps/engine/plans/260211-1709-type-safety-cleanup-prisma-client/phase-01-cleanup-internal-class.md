# Phase 01: Cleanup Internal Class.ts

**Context Links**
- File: `/src/generated/client/internal/class.ts`

**Overview**
- Priority: High
- Current Status: Pending
- Description: Loại bỏ `@ts-nocheck` và cải thiện type safety cho các phương thức thực thi query thô (raw query).

**Key Insights**
- File `class.ts` hiện đang dùng `@ts-nocheck` ở dòng 5, che giấu nhiều lỗi tiềm ẩn.
- Các hàm `$executeRaw`, `$queryRaw` đang dùng `any[]` cho tham số `values`.

**Requirements**
- [ ] Gỡ bỏ `// @ts-nocheck`.
- [ ] Thay thế `any[]` bằng `unknown[]` hoặc các type cụ thể hơn từ runtime.
- [ ] Đảm bảo không làm hỏng tính tương thích với Prisma Runtime.

**Implementation Steps**
1. Read `/src/generated/client/internal/class.ts` để xác định chính xác các vị trí cần sửa.
2. Gỡ bỏ dòng `// @ts-nocheck`.
3. Sửa `...values: any[]` thành `...values: unknown[]` trong các hàm:
    - `$executeRaw`
    - `$executeRawUnsafe`
    - `$queryRaw`
    - `$queryRawUnsafe`
4. Kiểm tra xem có lỗi TS nào phát sinh sau khi gỡ `@ts-nocheck`.

**Todo List**
- [ ] Read file
- [ ] Remove @ts-nocheck
- [ ] Fix any types in raw methods
- [ ] Verify with `tsc`

**Success Criteria**
- File `class.ts` không còn `@ts-nocheck`.
- Không còn `any` trong các chữ ký hàm public.
- Build TS không báo lỗi nghiêm trọng tại file này.

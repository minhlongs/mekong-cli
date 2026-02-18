# Phase 02: Cleanup Prisma Namespace

**Context Links**
- File: `/src/generated/client/internal/prismaNamespace.ts`

**Overview**
- Priority: Medium
- Current Status: Pending
- Description: Loại bỏ các kiểu `any` trong các utility types của Prisma Namespace.

**Key Insights**
- `SelectAndInclude`, `SelectAndOmit` đang sử dụng `any` cho các field `select`, `include`, `omit`.
- `export type Union = any` cần được thay thế bằng một định nghĩa an toàn hơn hoặc `unknown`.

**Requirements**
- [ ] Thay thế `any` bằng `object | null` hoặc `Record<string, any>` (nếu cần linh hoạt nhưng vẫn giới hạn).
- [ ] Phân tích xem `Union` được dùng ở đâu để định nghĩa kiểu chính xác hơn.

**Implementation Steps**
1. Read `/src/generated/client/internal/prismaNamespace.ts`.
2. Sửa `SelectAndInclude`, `SelectAndOmit`.
3. Tìm kiếm các vị trí sử dụng `Union` để xác định kiểu thay thế.

**Todo List**
- [ ] Fix utility types
- [ ] Research and fix Union type

**Success Criteria**
- Không còn `any` trong các export types chính của namespace.

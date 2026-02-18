# Kế hoạch: Dọn dẹp TYPE_SAFETY cho Prisma Client Internal

- **Mục tiêu**: Loại bỏ `any`, gỡ bỏ `@ts-nocheck` (nếu an toàn) và thêm các type annotations chính xác trong các file internal của Prisma Client.
- **Trạng thái**: Đang thực hiện (In Progress)
- **Ngày bắt đầu**: 2026-02-11

## Các giai đoạn

1. [Giai đoạn 01: Sửa lỗi trong class.ts](./phase-01-cleanup-internal-class.md) - [Đang chờ]
2. [Giai đoạn 02: Sửa lỗi trong prismaNamespace.ts](./phase-02-cleanup-prisma-namespace.md) - [Đang chờ]
3. [Giai đoạn 03: Xác minh Build & Lint](./phase-03-verify-build-lint.md) - [Đang chờ]

## Phụ thuộc chính
- Thư viện `@prisma/client/runtime` để lấy các type chính xác cho các hàm raw query.

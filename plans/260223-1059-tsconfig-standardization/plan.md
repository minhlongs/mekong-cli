---
title: "Chuẩn hoá TSConfig Mekong CLI Monorepo"
description: "Tạo tsconfig.base.json tại root và cấu hình 8 apps kế thừa để chuẩn hoá TypeScript"
status: pending
priority: P1
effort: 2h
branch: master
tags: [typescript, config, monorepo, standardization]
created: 2026-02-23
---

# Kế Hoạch Chuẩn Hoá TSConfig (Mekong CLI Monorepo)

**Mục tiêu**: Đồng bộ hoá cấu hình TypeScript trên toàn bộ monorepo bằng cách tạo một `tsconfig.base.json` ở thư mục gốc và cho các apps kế thừa (extends) từ file này.
**Ràng buộc**: TỐI ĐA 5 file được sửa đổi mỗi mission.

## Danh sách Apps mục tiêu (8 Apps)
1. `apps/84tea`
2. `apps/agencyos-landing`
3. `apps/agencyos-web`
4. `apps/anima119`
5. `apps/apex-os`
6. `apps/com-anh-duong-10x`
7. `apps/openclaw-worker`
8. `apps/sophia-proposal`

## Các Giai Đoạn Triển Khai

| Giai đoạn | Trạng thái | Mô tả |
|-----------|------------|-------|
| [Phase 1: Setup Base & 4 Apps](./phase-01-setup-base-and-update-4-apps.md) | ✅ completed | Tạo `tsconfig.base.json` và cập nhật cấu hình cho 4 apps đầu tiên. (Sửa 5 file) |
| [Phase 2: Update Remaining 4 Apps](./phase-02-update-remaining-4-apps.md) | ⏳ pending | Cập nhật cấu hình kế thừa cho 4 apps còn lại. (Sửa 4 file) |
| [Phase 3: Verification](./phase-03-verify-compilation.md) | ⏳ pending | Chạy `npx tsc --noEmit` và xử lý các lỗi type (nếu có, tối đa 5 file). |

## Phụ thuộc
- Các rules trong Binh Pháp (`binh-phap-core.md`, `binh-phap-quality.md`).
- File `tsconfig.base.json` phải chứa các compiler options chung nhất.

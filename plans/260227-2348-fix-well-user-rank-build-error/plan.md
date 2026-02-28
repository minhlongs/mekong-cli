---
title: "Sửa lỗi build TS1361 liên quan đến UserRank trong apps/well"
description: "Chuyển đổi import type thành import value cho UserRank enum để fix lỗi build tsc."
status: pending
priority: P1
effort: 15m
branch: master
tags: [fix, build-error, typescript, enum]
created: 2026-02-27
---

# Kế hoạch sửa lỗi build UserRank (TheBeeAgent)

## Bối cảnh
File `src/agents/custom/TheBeeAgent.ts` đang import `UserRank` dưới dạng `type` nhưng lại sử dụng nó như một `value` (truy cập enum member). Điều này khiến trình biên dịch TypeScript báo lỗi TS1361 vì thông tin runtime của enum bị thiếu.

## Mục tiêu
- Sửa lỗi build tại `TheBeeAgent.ts`.
- Đảm bảo tính nhất quán của việc sử dụng `UserRank` trong toàn bộ `apps/well`.

## Các bước thực hiện

### Bước 1: Sửa import trong TheBeeAgent.ts
Thay đổi cách import `UserRank` từ:
```typescript
import type { UserRank } from '@/types';
```
Thành:
```typescript
import { UserRank } from '@/types';
```

### Bước 2: Kiểm tra các file khác
Dựa trên kết quả grep, cần kiểm tra nhanh các file sau để đảm bảo không mắc lỗi tương tự:
- `apps/well/src/utils/business/commission.ts`
- `apps/well/src/services/referral-service.ts`

### Bước 3: Xác minh (Verify)
Chạy lệnh build để xác nhận lỗi đã được khắc phục:
```bash
cd /Users/macbookprom1/mekong-cli/apps/well && npm run build
```

## Tiêu chí thành công
- Lệnh `npm run build` trong `apps/well` chạy thành công không có lỗi TS1361.
- Logic tính toán phần thưởng (reward) trong `TheBeeAgent` vẫn hoạt động chính xác.

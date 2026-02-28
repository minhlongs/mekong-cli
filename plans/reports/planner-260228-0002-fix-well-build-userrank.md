---
title: "Planner Report: Fix Well Build UserRank Error"
description: "Analysis and planning for TS1361 UserRank import error in Well project"
status: completed
priority: P1
effort: 30m
branch: master
tags: [typescript, build-error, enum-import]
created: 2026-02-28
---

# Planner Report: Fix Well Build UserRank Error

## Executive Summary
Đã phân tích lỗi TypeScript TS1361 trong project `apps/well` và lập kế hoạch sửa lỗi. Lỗi xảy ra do vấn đề import enum `UserRank` từ `@/types` trong file `TheBeeAgent.ts`.

## Error Details
- **File**: `apps/well/src/agents/custom/TheBeeAgent.ts`
- **Lines**: 104, 141, 145, 149
- **Error**: `'UserRank' cannot be used as a value because it was imported using 'import type'`

## Phân Tích Hiện Trạng

### ✅ Đã Xác Định:
1. **UserRank definition**: `export enum UserRank` trong `apps/well/src/types.ts` (lines 3-12)
2. **Current import**: `import { UserRank } from '@/types';` (line 3 trong TheBeeAgent.ts)
3. **Enum usage**: UserRank được sử dụng như enum values (CTV, DAI_SU, PHUONG_HOANG, etc.)

### ❌ Vấn Đề:
Mặc dù import statement đúng nhưng TypeScript vẫn báo lỗi, có thể do:
- Path resolution của `@/types` không chính xác
- Có import type khác trong codebase
- TypeScript config issue

## Kế Hoạch Sửa Lỗi

### Phase 1: Research (Đã Hoàn Thành)
- [x] Kiểm tra UserRank enum definition trong `types.ts`
- [x] Xác nhận import statement hiện tại
- [x] Kiểm tra tsconfig.json paths configuration

### Phase 2: Solution Implementation
**Approach 1: Sửa Import Statement (Recommended)**
```typescript
// Thay thế:
import { UserRank } from '@/types';

// Bằng:
import { UserRank } from '../../types';
```

**Approach 2: Kiểm tra Path Resolution**
- Verify `@/types` resolves to `src/types.ts` trong tsconfig.json

### Phase 3: Verification
- [ ] Run `npm run build` trong apps/well
- [ ] Verify no TypeScript errors
- [ ] Test UserRank enum functionality

## Risk Assessment
- **Risk**: Thấp - chỉ thay đổi import statement
- **Impact**: Không - không thay đổi logic business
- **Rollback**: Dễ dàng - revert import change

## Success Criteria
- ✅ Build passes without TS1361 errors
- ✅ UserRank enum accessible và usable
- ✅ No regression in functionality

## File Paths
- **Plan**: `/Users/macbookprom1/mekong-cli/plans/260228-0002-fix-well-build-userrank/plan.md`
- **Target File**: `/Users/macbookprom1/mekong-cli/apps/well/src/agents/custom/TheBeeAgent.ts`

## Recommendation
**Sử dụng Approach 1** - thay đổi import từ relative path để đảm bảo path resolution chính xác.

## Unresolved Questions
- Tại sao `@/types` không resolve đúng mặc dù tsconfig.json config đúng?
- Có file nào khác import UserRank không đúng cách?

---
**Next Step**: Delegate to developer để thực hiện import fix theo kế hoạch.
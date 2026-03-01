# Phase 01 — Stage & Commit

## Context
- Parent: [plan.md](plan.md)
- Branch: `master`

## Overview
- Priority: P1
- Status: pending
- Stage all changes và commit với message `chore: cleanup`

## Key Insights
- `.gitignore` đã cover `node_modules/`, `.env`, `dist/` → không cần sửa
- 28 modified + 15 untracked files cần stage
- `.mekong/` thư mục đang modified — cần xác nhận có nên commit hay đã gitignore

## Requirements
- `git add -A` stage tất cả changes
- `git commit -m 'chore: cleanup'` tạo commit
- Commit message theo convention đã dùng (match existing `chore: cleanup` pattern)

## Implementation Steps
1. Chạy `git add -A` để stage tất cả
2. Chạy `git status` review staged files
3. Chạy `git commit -m 'chore: cleanup'`

## Related Code Files
- Không sửa code — chỉ git operation

## Todo
- [ ] git add -A
- [ ] Review staged files
- [ ] git commit

## Success Criteria
- Commit thành công, không lỗi
- Tất cả modified/untracked files đã staged

## Risk Assessment
- `.mekong/` files — nếu đã gitignore thì safe, nếu chưa cần xem lại
- Untracked plan directories sẽ được add — đây là expected

## Security Considerations
- Verify không có API keys, secrets trong staged files
- `.env` files đã gitignore → safe

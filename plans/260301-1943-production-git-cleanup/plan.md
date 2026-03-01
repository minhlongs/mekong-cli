---
title: "Production Git Cleanup — mekong-cli"
description: "Stage all changes, commit chore cleanup, verify .gitignore coverage and clean tree"
status: pending
priority: P1
effort: 5m
branch: master
tags: [git, cleanup, production]
created: 2026-03-01
---

# Production Git Cleanup — mekong-cli

## Tóm tắt

Stage tất cả changes (modified + untracked), commit cleanup, verify .gitignore.

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Stage & Commit | pending | [phase-01](phase-01-stage-and-commit.md) |
| 2 | Verify Clean Tree | pending | [phase-02](phase-02-verify-clean-tree.md) |

## Phân tích hiện trạng

- **28 modified files** — runtime state, algo-trader refactor, openclaw data, sophia-proposal
- **15 untracked files** — algo-trader plans/modules, openclaw intel, root plans
- **.gitignore** — ĐÃ cover: `node_modules/`, `.env`, `dist/`, `.env.local`, `*.env`
- **Không có** `.env`/`dist`/`node_modules` nào bị git track

## Rủi ro

- Commit `git add -A` sẽ add tất cả untracked files → cần review trước khi commit
- Các file `.mekong/` đang modified nhưng `.mekong/` đã có trong .gitignore — kiểm tra lại

## Validation Log

### Session 1 — 2026-03-01
**Trigger:** Initial plan creation validation
**Questions asked:** 3

#### Questions & Answers

1. **[Assumptions]** Plan commit trên branch `master`, không phải `main`. Bạn muốn commit trên branch nào?
   - Options: master (Recommended) | main
   - **Answer:** master (Recommended)
   - **Rationale:** Commit trên branch hiện tại, đúng với git status

2. **[Risk]** `.mekong/` files đang modified. Thư mục có trong .gitignore nhưng files vẫn show modified — có thể đã tracked từ trước. Xử lý thế nào?
   - Options: Commit luôn (Recommended) | Untrack .mekong/ | Skip .mekong/
   - **Answer:** Commit luôn (Recommended)
   - **Rationale:** Stage và commit tất cả .mekong/ modified files cùng với các changes khác

3. **[Scope]** Commit message: user yêu cầu `chore: cleanup`. Thêm mô tả chi tiết hơn không?
   - Options: chore: cleanup (Recommended) | Chi tiết hơn
   - **Answer:** chore: cleanup (Recommended)
   - **Rationale:** Đơn giản, match pattern các commit gần đây

#### Confirmed Decisions
- Branch: master — commit trên branch hiện tại
- .mekong/ files: commit luôn — không untrack hay skip
- Commit message: `chore: cleanup` — giữ đơn giản

#### Action Items
- [ ] Không cần sửa plan — tất cả confirmed as-is

#### Impact on Phases
- Không thay đổi — plan giữ nguyên

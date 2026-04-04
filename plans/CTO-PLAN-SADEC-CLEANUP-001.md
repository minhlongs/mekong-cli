# CODING PLAN #001 — Sadec Root Cleanup & Standards Enforcement

> **Ngày tạo**: 2026-03-16
> **Priority**: P0 → P1
> **Agent assignment**: Claude Code (primary) + OpenClaw Workers (support)
> **Nguồn**: Bộ cải tiến "Claude cải tiến Mekong Marketing v1.0"

---

## Objective

Dọn dẹp root directory (25 file .md), áp dụng chuẩn từ CLAUDE.md mới, enforce quy tắc cấu trúc thư mục, và xử lý các P0 security issues.

## Context

- **CLAUDE.md mới** đã được deploy (479 dòng) — thay thế bản cũ 192 dòng
- **AGENTS-WORKFLOW.md** — quy trình phối hợp 3 tầng agent
- **project-rules.md** → `.claude/commands/` — quick reference templates
- **cleanup-root.sh** → `scripts/` — script tự động dọn dẹp
- Root hiện có **25 file .md** và **12 thư mục ẩn**

### Related files

```
CLAUDE.md                          ← Đã cập nhật (v mới)
AGENTS-WORKFLOW.md                 ← Đã cập nhật
.claude/commands/project-rules.md  ← Đã copy
scripts/cleanup-root.sh            ← Đã copy
```

---

## PHASE 1 — Chạy cleanup script (P0)

### Task 1.1 — Dry-run cleanup
- **Agent**: OpenClaw Worker
- **Action**: run command

```bash
cd /Users/mac/mekong-cli
bash scripts/cleanup-root.sh --dry-run
```

- **Expected**: Hiển thị danh sách files sẽ di chuyển, không thay đổi gì

### Task 1.2 — Thực thi cleanup
- **Agent**: OpenClaw Worker
- **Action**: run command

```bash
cd /Users/mac/mekong-cli
bash scripts/cleanup-root.sh
```

### Task 1.3 — Commit kết quả Phase 1
- **Agent**: OpenClaw Worker

```bash
git add -A
git commit -m "chore: organize root directory, move docs to subfolders"
```

---

## PHASE 2 — Dọn dẹp thủ công (P1)

Cleanup script chỉ cover RELEASE-NOTES, AUDIT, PERFORMANCE, TECH-DEBT, SPRINT patterns. Còn nhiều file khác cần di chuyển thủ công.

### Task 2.1 — Di chuyển IMPLEMENTATION-SPEC phiên bản cũ
- **Agent**: OpenClaw Worker
- **Files**: `IMPLEMENTATION-SPEC-v0.{1..8}.md` (8 files)
- **Action**: move to `docs/archive/`

```bash
mkdir -p docs/archive
git mv IMPLEMENTATION-SPEC-v0.*.md docs/archive/
```

### Task 2.2 — Di chuyển HUONG-DAN-SU-DUNG phiên bản cũ
- **Agent**: OpenClaw Worker
- **Files**: `HUONG-DAN-SU-DUNG-v0.{1..3}.md` (3 files)
- **Action**: move to `docs/archive/`

```bash
git mv HUONG-DAN-SU-DUNG-v0.*.md docs/archive/
```

### Task 2.3 — Di chuyển docs lẻ
- **Agent**: OpenClaw Worker
- **Files cần di chuyển**:

```bash
# Strategy/Philosophy docs → docs/
git mv HEARTBEAT-v0.2.md docs/
git mv HIEN-PHAP-ROIAAS.md docs/
git mv ROIAAS-ROADMAP.md docs/
git mv SOUL.md docs/

# Giữ ở root (chuẩn open-source): README.md, QUICKSTART.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, CLAUDE.md, AGENTS-WORKFLOW.md, HUONG-DAN-SU-DUNG.md
```

### Task 2.4 — Xóa file trùng ở root
- **Agent**: OpenClaw Worker

```bash
# cleanup-root.sh đã có bản trong scripts/
rm cleanup-root.sh

# project-rules.md đã có bản trong .claude/commands/
rm project-rules.md
```

### Task 2.5 — Commit kết quả Phase 2
- **Agent**: OpenClaw Worker

```bash
git add -A
git commit -m "chore: move legacy docs to archive, remove duplicate files"
```

---

## PHASE 3 — P0 Security Issues

### Task 3.1 — Quét demo credentials
- **Agent**: Claude Code
- **Action**: search & remove

```bash
grep -rn "demo\|password\|123456\|admin@" --include="*.html" --include="*.js" --include="*.md" . | grep -v node_modules | grep -v .git
```

- **Acceptance**: KHÔNG còn demo credentials trong production code

### Task 3.2 — Kiểm tra .gitignore
- **Agent**: Claude Code
- **Action**: verify entries

```bash
# Phải có trong .gitignore:
.coverage
coverage/
*.lcov
mekong-env.js
.env
.env.local
.DS_Store
node_modules/
dist/
*.tmp
*.log
```

### Task 3.3 — Commit kết quả Phase 3
- **Agent**: OpenClaw Worker

```bash
git add -A
git commit -m "security: remove demo credentials, harden .gitignore"
```

---

## Acceptance Criteria

- [ ] Root directory chỉ còn ≤ 10 file .md (chuẩn open-source)
- [ ] `docs/` có subfolders: releases, audits, performance, tech-debt, sprints, design, archive
- [ ] `scripts/cleanup-root.sh` tồn tại, `cleanup-root.sh` ở root KHÔNG tồn tại
- [ ] `.claude/commands/project-rules.md` tồn tại, `project-rules.md` ở root KHÔNG tồn tại
- [ ] `.gitignore` có đủ entries cho .coverage, mekong-env.js, .env
- [ ] KHÔNG còn demo credentials trong code
- [ ] `git status` sạch sau khi commit

## Constraints

- **DO NOT** xóa README.md, QUICKSTART.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
- **DO NOT** sửa nội dung CLAUDE.md (vừa deploy bản mới)
- **DO NOT** thay đổi cấu trúc `src/`, `mekong/`, `packages/`
- Sử dụng `git mv` thay vì `mv` để giữ git history

## Estimated Scope

- **Files affected**: ~30 files (di chuyển + xóa)
- **Complexity**: Low-Medium
- **Risk**: Low (chỉ di chuyển/dọn file, không sửa logic)
- **Thời gian ước tính**: 15-20 phút cho CTO dispatch

---

> **@CTO**: Plan này sẵn sàng dispatch. 3 phases có thể chạy tuần tự.
> Mỗi phase có commit riêng để dễ rollback nếu cần.

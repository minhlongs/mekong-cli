---
description: QA Gate — Full quality assurance pipeline trước production push
---
// turbo-all

# /qa-gate Workflow

> 善戰者先為不可勝 — Giỏi đánh: trước tiên bất khả bại

## Steps

1. **Build Check**:
   ```bash
   npm run build
   ```
2. **Test Suite**:
   ```bash
   npm test
   ```
3. **Codebase Review**:
   ```
   /review:codebase
   ```
4. **Lessons Check** — Đọc `apps/openclaw-worker/lessons.md` để tránh lặp lại lỗi cũ
5. **Commit nếu ALL GREEN**:
   ```
   /check-and-commit
   ```
6. **Nếu FAIL** → Auto-dispatch `/debug` và quay lại Step 1

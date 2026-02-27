---
description: Sprint — BMAD Sprint cycle tích hợp ClaudeKit execution
---

# /sprint Workflow

> 風林火山 — GIÓ→RỪNG→LỬA→NÚI theo từng phase

## Steps

1. **Sprint Planning** (⛰️NÚI):
   ```
   /bmad-bmm-sprint-planning
   ```
2. **Story Implementation** (🔥LỬA):
   Với mỗi story từ sprint:
   ```
   /bmad-bmm-dev-story → /cook <story_plan> --parallel --auto
   ```
3. **Code Review** (軍形):
   ```
   /bmad-bmm-code-review
   ```
4. **Test Gate** (先為不可勝):
   ```
   /test && npm run build
   ```
5. **Commit & Deploy** (火攻):
   ```
   /check-and-commit
   ```
6. **Retrospective** (知己知彼):
   ```
   /bmad-bmm-retrospective
   ```

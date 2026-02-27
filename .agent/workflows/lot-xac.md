---
description: Lột Xác — Metamorphosis workflow cho refactoring lớn
---

# /lột-xác Workflow (Metamorphosis)

> 能因敵變化而取勝者，謂之神 — Biến hóa theo tình thế mà thắng: gọi là THẦN

## Steps

1. **Scan hiện trạng** codebase:
   ```
   /review:codebase
   ```
2. **Phân tích kiến trúc** hiện tại:
   ```
   /bmad-bmm-create-architecture
   ```
3. **Tạo plan refactor**:
   ```
   /plan:parallel "Refactor <target> with <goal>" 5
   ```
4. **Execute theo Wave**:
   ```
   /cook <plan_dir> --parallel --auto
   ```
5. **Full QA Gate**:
   ```
   /test && /review:codebase && /check-and-commit
   ```
6. **Retrospective**:
   ```
   /bmad-bmm-retrospective
   ```

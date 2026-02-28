# Phase 1: Audit & Dedup Hiện Tại

**Priority:** HIGH | **Status:** Pending

## Mục tiêu
Kiểm tra 66 skills hiện tại, xác định duplicates, outdated, và gaps cần fill.

## Steps

1. **List installed skills** via ClawHub lockfile (nếu có):
   ```bash
   npx clawhub@latest list
   ```

2. **Cross-check** `.claude/skills/` dirs vs ClawHub registry:
   ```bash
   # Mỗi skill dir → clawhub inspect để check version
   for skill in $(ls .claude/skills/); do
     npx clawhub@latest inspect "$skill" --no-input 2>/dev/null | head -3
   done
   ```

3. **Identify gaps** — skills trong Awesome list nhưng chưa install

4. **Output:** File `audit-results.md` với bảng: Skill | Local Version | Registry Version | Status

## Success Criteria
- [x] Biết chính xác skills nào đã có
- [x] Biết chính xác skills nào cần update
- [x] Biết gaps cần fill

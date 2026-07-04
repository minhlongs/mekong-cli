---
title: "QUÂN DOANH — Binh Phap Military Camp Zones"
---

# Military Camp Zones

## QUÂN DOANH (Fortified — Read-Only)
Core engine. KHÔNG sửa khi chưa có `/binh-phap win`.
- `mekong/` — bootstrap, init, audit, hooks, constitution
- `.claude/hooks/` — hook executables
- `mekong/constitution/` — ZENOS.md, rules/
- `.ck.json` — CK init fingerprint
- `scripts/shell-init.sh` — boot entry

## DOANH TRẠI (Garrison — Read/Write)
Agent tự do edit.
- `.claude/commands/` — command definitions
- `.claude/skills/` — skill definitions
- `.claude/agents/` — agent definitions
- `workflows/` — pipeline definitions
- `docs/` — documentation

## KHO LƯƠNG (Supply — Generated/Temp)
Có thể xoá. Git-ignored.
- `build/`, `dist/`
- `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`
- `reports/`, `__pycache__/`

## HÀNH LANG (Corridor — Needs Cleanup)
Orphan dirs, cần dọn.
- `.agent/`, `.agents/`, `.antigravity/`, `.gemini/`
- `.opencode/`, `.cursorrules/`
- `.claude-backup/`, `.claude-skills/`
- Root report files (GO_LIVE, PHASE*, security, etc.)

## Boundary Rules
1. QUÂN DOANH files chỉ được sửa sau khi chạy `/binh-phap win` gate
2. DOANH TRẠI files có thể tự do edit
3. KHO LƯƠNG files không commit
4. HÀNH LANG files cần cleanup — không tạo mới

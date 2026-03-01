# 始計 Deep 10x Plan — A2UI Integration + Production Audit

> Ref: mm7j84ma | Date: 2026-03-01 | Binh Phap Ch.1 始計

## Mục tiêu

4 phase thực thi song song + tuần tự:

| Phase | Mô tả | Status |
|-------|--------|--------|
| 1 | Deep 10x Plan (THIS) | ✅ Complete |
| 2 | Ánh xạ google/A2UI → mekong-cli | 🔄 In Progress |
| 3 | Production Code Audit (lint, security, npm audit) | 🔄 In Progress |
| 4 | Verify + Commit | ⏳ Pending |

---

## Phase 2: Ánh xạ google/A2UI

### Mục tiêu
Tạo A2UI terminal renderer — first CLI renderer trong ecosystem.

### Deliverables
1. `src/a2ui/` — A2UI renderer module (Python, Rich/Textual)
   - `renderer.py` — Core renderer: JSON → Rich widgets
   - `components.py` — Component registry mapping
   - `__init__.py` — Public API
2. `.claude/skills/a2ui-renderer/SKILL.md` — ClaudeKit skill
3. `apps/openclaw-worker/tasks/HIGH_a2ui_integration.txt` — Archive processed

### Component Map
| A2UI Component | Rich/Textual Widget |
|---------------|---------------------|
| Text | `rich.text.Text` |
| Card | `rich.panel.Panel` |
| Row | `rich.columns.Columns` |
| Column | `rich.layout.Layout` |
| List | `rich.table.Table` |
| Button | `[bold cyan]▸ label[/]` (styled text) |
| TextField | `[dim]⎕ placeholder[/]` |
| CheckBox | `☐/☑ label` |
| Tabs | `rich.table.Table` (tab headers) |
| Image | `[Image: alt_text]` (placeholder) |
| Divider | `rich.rule.Rule` |
| Modal | `rich.panel.Panel` (highlighted) |
| Icon | emoji/unicode mapping |

### Kiến trúc
```
Agent LLM → JSON (A2UI surfaceUpdate) → mekong A2UIRenderer → Rich Console Output
```

---

## Phase 3: Production Code Audit

### Python Audit
1. `ruff check src/ --fix` — Auto-fix lint issues
2. `ruff format src/` — Format code
3. `grep -r "console\." src/ --include="*.py"` — Clean console calls
4. `grep -r ": any" src/ --include="*.py"` — Type safety check
5. `grep -r "TODO\|FIXME" src/` — Tech debt scan
6. `grep -r "@ts-ignore\|@ts-nocheck" src/` — TS escape hatches
7. Security: grep API_KEY, SECRET in source code

### JS/Node Audit
1. `npm audit fix` — Fix known vulnerabilities (root)
2. Security headers check
3. No secrets in codebase

### Quality Gates
- 0 high/critical vulnerabilities
- 0 secrets in source
- Ruff clean pass
- Tests pass

---

## Phase 4: Verify + Commit

1. `python3 -m pytest tests/ -x --timeout=120` — Run test suite
2. Git add + commit with conventional format
3. Verify production readiness

---

## Risk Assessment
- A2UI repo may need specific Node.js version — mitigate: skip clone, just create renderer
- npm audit may have breaking changes — mitigate: `--force` only if needed
- Test suite 151 files may take time — mitigate: `-x` flag for fast-fail

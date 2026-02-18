# ClaudeKit Engineer v2.9.1 — Deep Command Reference
# Source: https://docs.claudekit.cc/docs/engineer/
# Tiêm vào CTO/Antigravity/CC CLI — KHÔNG BỎ SÓT

## 🔒 COMMAND ROUTING MAP (Tôm Hùm CTO)

### Task → Command Mapping (Auto-CTO/Mission Dispatcher PHẢI dùng)

| Task Complexity | ClaudeKit Command | When to Use |
|:----------------|:------------------|:------------|
| Simple fix | `/cook "task" --auto` | < 30min, < 5 files |
| Quick plan | `/plan:fast "task"` | Simple feature, clear scope |
| Complex feature | `/plan:hard "task"` | Multi-file, needs research |
| 2 approaches | `/plan:two "task"` | When uncertain which path |
| Mega feature | `/plan:parallel "task"` | Needs 3+ researcher agents |
| CI broken | `/plan:ci` | Build/test failures |
| CRO optimization | `/plan:cro` | Conversion rate improvements |
| Archive old plans | `/plan:archive` | Cleanup completed plans |
| Validate plan | `/plan:validate` | Check plan structure |
| Debug issue | `/debug "issue"` | Bugs, errors, failures |
| Run tests | `/test` | After implementation |
| UI tests | `/test:ui` | Visual/E2E testing |
| Ask codebase | `/ask "question"` | Understanding existing code |
| Project status | `/watzup` | What's happening? |
| Kanban board | `/kanban` | View/manage project tasks |
| Write journal | `/journal` | Dev progress logging |
| Init docs | `/docs:init` | First-time doc setup |
| Update docs | `/docs:update` | After code changes |
| Summarize docs | `/docs:summarize` | Generate doc summary |
| Code review | `/review` | Audit entire codebase |
| Parallel review | `/review:codebase` | Multi-agent codebase audit |
| Quality + commit | `/check-and-commit` | Final step before push |
| Git worktree | `/worktree "feature"` | Feature branch isolation |
| Bootstrap project | `/bootstrap "desc"` | Initialize new project |
| Set complexity | `/coding-level "level"` | Adjust code depth |
| Preview work | `/preview` | View current changes |
| MCP tools | `/use-mcp` | Access external tools |
| ClaudeKit help | `/ck-help` | Get help about commands |

---

## 🤖 AGENTS (13 Available — Auto-orchestrated by commands)

### Development & Implementation
| Agent | Role | Activated By |
|:------|:-----|:-------------|
| `planner` | Creates implementation plans | `/plan`, `/plan:hard`, `/plan:parallel` |
| `fullstack-developer` | Implements features end-to-end | `/cook`, `/bootstrap` |
| `debugger` | Investigates and diagnoses issues | `/debug` |
| `tester` | Validates code with automated tests | `/test`, `/test:ui` |

### Quality & Review
| Agent | Role | Activated By |
|:------|:-----|:-------------|
| `code-reviewer` | Audits code for security and quality | `/review`, `/review:codebase` |

### Documentation & Management
| Agent | Role | Activated By |
|:------|:-----|:-------------|
| `docs-manager` | Manages project documentation | `/docs:*` |
| `project-manager` | Oversees project tasks | `/kanban`, `/watzup` |
| `journal-writer` | Logs development progress | `/journal` |
| `git-manager` | Handles git operations/commits | `/check-and-commit`, `/worktree` |

### Creative & Research
| Agent | Role | Activated By |
|:------|:-----|:-------------|
| `ui-ux-designer` | Designs interfaces | Design-related tasks |
| `brainstormer` | Generates ideas | Brainstorming prompts |
| `researcher` | Investigates topics | `/plan:parallel`, `/plan:hard` |

### Integration
| Agent | Role | Activated By |
|:------|:-----|:-------------|
| `mcp-manager` | Manages MCP server tools | `/use-mcp` |

### Orchestration Patterns
```
Sequential (default): planner → fullstack-developer → tester → code-reviewer → git-manager
Parallel:             researcher(1) + researcher(2) + researcher(3) → planner
Hybrid:               Mix of sequential + parallel for complex tasks
Explicit:             "Use debugger agent to investigate, then planner to create fix"
```

---

## 🧩 SKILLS (50+ Available — Activate via keywords)

### Frontend & Design (11)
frontend-design, ui-ux-pro-max, ui-styling, frontend-development,
web-frameworks, threejs, react-best-practices, web-design-guidelines,
web-testing, shader, remotion

### Backend & Infrastructure (3)
backend-development, databases, devops

### AI & Multimodal (3)
ai-multimodal, google-adk-python, ai-artist

### Tools & Utilities (12)
mcp-builder, mcp-management, skill-creator, repomix,
document-skills, docs-seeker, chrome-devtools, media-processing,
agent-browser, markdown-novel-viewer, context-engineering, gkg

### Process & Methodology (12)
planning, research, sequential-thinking, problem-solving,
debug, code-review, brainstorm, scout, cook, fix, git, plans-kanban

### Integrations & Specialized (7)
better-auth, shopify, payment-integration, mobile-development,
copywriting, mermaidjs-v11, find-skills

### Skill Activation
- Mention skill name explicitly: "Use react-best-practices"
- Describe matching task: "Optimize the React components"
- Use domain keywords: "Shopify", "three.js", "payment"

### Creating Custom Skills
```
"Use skill-creator to create a skill for [your-domain]"
```

---

## 📋 WORKFLOW PATTERNS (CTO/Antigravity PHẢI follow)

### 1. New Feature (Standard)
```
/plan:hard "feature description"    ← Plan with research
# Review plan in plans/ directory
/cook "Implement as planned"        ← Execute plan
/test                               ← Validate
/check-and-commit                   ← Quality + commit
```

### 2. Complex Multi-Phase
```
/plan:parallel "mega feature" [3]   ← 3 parallel researchers
# Review aggregated plan
/cook "Phase 1: foundation"         ← Incremental implementation
/test
/cook "Phase 2: integration"
/test
/check-and-commit
```

### 3. Bug Fix
```
/debug "issue description"          ← Diagnose
/plan:fast "fix based on debug"     ← Quick fix plan
/cook "Apply fix"                   ← Implement
/test                               ← Verify
/check-and-commit
```

### 4. CI Recovery
```
/plan:ci                            ← Analyze CI failures
/cook "Fix CI issues"               ← Apply fixes
/test                               ← Verify green
/check-and-commit
```

### 5. Codebase Health
```
/review:codebase                    ← Parallel multi-agent review
/plan:hard "Fix critical findings"  ← Plan fixes
/cook "Apply security fixes"        ← Implement
/test
/docs:update                        ← Update docs
/check-and-commit
```

### 6. Documentation Overhaul
```
/docs:init                          ← First-time setup
/docs:summarize                     ← Generate summary
/docs:update                        ← After changes
```

---

## 🔥 KHÔNG DÙNG RAW TEXT — Mission Dispatcher Enforcement

### ĐÚNG (ClaudeKit enforced):
```
/cook "Fix build errors in anima119" --auto
/plan:hard "Add authentication to 84tea"
/debug "Production 500 error on /api/chat"
/review:codebase
```

### SAI (Raw text — CẤM):
```
Fix the build errors in anima119
Add authentication to the project
Look at the error logs and find the issue
Review all the code for security issues
```

---

## 📊 COMMAND COMPLEXITY ROUTING

```
TRIVIAL   → /cook "task" --auto           (< 5 files, < 15min)
SIMPLE    → /plan:fast → /cook            (< 10 files, < 30min)
MODERATE  → /plan:hard → /cook → /test    (< 20 files, < 1h)
COMPLEX   → /plan:parallel → /cook phases (> 20 files, > 1h)
STRATEGIC → /plan:parallel [5] → phases   (Architecture-level)
```

---

## 🧬 BINH PHÁP × CLAUDEKIT DNA FUSION (v5.0 — 2026-02-18)

> Ref: `BINH_PHAP_MASTER.md` DNA Fusion #5. Mỗi command = một kế Binh Pháp.

### Command → Binh Pháp Chapter Quick Map

| Category | Commands | Binh Pháp Chapter | Nguyên Tắc |
|:---------|:---------|:-------------------|:-----------|
| Planning | `/plan`, `/plan:validate`, `/bootstrap` | 始計 Ch.1 Kế Sách | 多算勝 — Tính nhiều thắng |
| Speed | `/plan:fast`, `/cook`, `/cook --fast` | 作戰 Ch.2 Tác Chiến | 兵貴勝不貴久 — Nhanh |
| Strategy | `/plan:hard`, `/review:codebase`, `/docs:update` | 謀攻 Ch.3 Mưu Công | 知己知彼 — Biết mình biết người |
| Defense | `/debug`, `/test`, `/test:ui` | 軍形 Ch.4 Quân Hình | 先為不可勝 — Bất khả bại trước |
| Parallel | `/plan:two`, `/plan:parallel`, `/cook --parallel` | 兵勢 Ch.5 Binh Thế | 奇正相生 — Chính Kỳ sinh nhau |
| Target | `/plan:cro`, `/worktree` | 虛實 Ch.6 Hư Thực | 避實擊虛 — Tránh mạnh đánh yếu |
| Execute | `/cook --auto`, `/kanban` | 軍爭 Ch.7 Quân Tranh | 以迂為直 — Vòng thành thẳng |
| Adapt | `/plan:archive`, `/cook --no-test` | 九變 Ch.8 Cửu Biến | 變化無窮 — Biến hóa không cùng |
| Recon | `/plan:ci`, `/scout` | 行軍 Ch.9 Hành Quân | 偵察先行 — Trinh sát trước |
| Survey | `/watzup` | 地形 Ch.10 Địa Hình | 知天知地 — Biết thiên địa |
| Deploy | `/check-and-commit` | 火攻 Ch.12 Hỏa Công | 發火有時 — Đốt đúng lúc |
| Intel | `/ask`, `/journal`, `/scout` | 用間 Ch.13 Dụng Gián | 先知者 — Người biết trước |

### Agent → Binh Pháp Role Quick Map

| Agent | Vai Trò | Đức |
|:------|:--------|:----|
| planner | 軍師 Quân Sư | TRÍ 智 |
| fullstack-dev | 先鋒 Tiên Phong | DŨNG 勇 |
| debugger | 斥候 Trinh Sát | TRÍ 智 |
| tester | 監軍 Giám Quân | NGHIÊM 嚴 |
| code-reviewer | 御史 Ngự Sử | NGHIÊM 嚴 |
| researcher | 間諜 Gián Điệp | TRÍ 智 |
| git-manager | 輜重 Hậu Cần | NGHIÊM 嚴 |


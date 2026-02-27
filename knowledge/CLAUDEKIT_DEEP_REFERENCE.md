# 🧬 CLAUDEKIT DEEP REFERENCE — DNA Fusion #5

> Nguồn: `apps/openclaw-worker/BINH_PHAP_MASTER.md` §DNA #5
> 13 agents × 28 commands × 43 skills = 195 concepts
> Ánh xạ: TOÀN BỘ 13 Chương × ClaudeKit v2.9.1

---

## 🎖️ 13 AGENTS × NGŨ ĐỨC TƯỚNG

| Agent | Vai Trò Binh Pháp | Đức | Chương | Khi Nào |
|:------|:-------------------|:----|:-------|:--------|
| `planner` | 軍師 Quân Sư | TRÍ 智 | 始計 Ch.1 | MỌI task phức tạp PHẢI qua |
| `fullstack-developer` | 先鋒 Tiên Phong | DŨNG 勇 | 作戰 Ch.2 | Implement sau plan approved |
| `debugger` | 斥候 Trinh Sát | TRÍ 智 | 行軍 Ch.9 | Bug → investigate TRƯỚC fix |
| `tester` | 監軍 Giám Quân | NGHIÊM 嚴 | 軍形 Ch.4 | SAU implement → verify |
| `code-reviewer` | 御史 Ngự Sử | NGHIÊM 嚴 | 軍形 Ch.4 | Audit quality + security |
| `docs-manager` | 書記 Thư Ký | TÍN 信 | 用間 Ch.13 | Knowledge = intelligence |
| `project-manager` | 督軍 Đốc Quân | TÍN 信 | 地形 Ch.10 | Manage tasks, track |
| `journal-writer` | 太史 Thái Sử | TÍN 信 | 用間 Ch.13 | Record history |
| `git-manager` | 輜重 Hậu Cần | NGHIÊM 嚴 | 火攻 Ch.12 | Git = deploy (發火) |
| `ui-ux-designer` | 工匠 Công Tượng | NHÂN 仁 | 兵勢 Ch.5 | Design = build thế |
| `brainstormer` | 策士 Sách Sĩ | TRÍ 智 | 謀攻 Ch.3 | Brainstorm = 上兵伐謀 |
| `researcher` | 間諜 Gián Điệp | TRÍ 智 | 用間 Ch.13 | Research = Ngũ Gián |
| `mcp-manager` | 器械 Khí Giới | NHÂN 仁 | 九變 Ch.8 | MCP tools = weapons |

---

## 📋 28 COMMANDS × THẤT KẾ ROUTING

### /plan Routing (始計 Decision Tree)

| Command | Binh Pháp | Khi Nào |
|:--------|:----------|:--------|
| `/plan` | 多算勝 Tính nhiều thắng | Default planning |
| `/plan:fast` | 兵貴勝 Nhanh thắng | Simple, clear path |
| `/plan:hard` | 知己知彼 Biết mình người | 2 researchers parallel, ≤150 lines |
| `/plan:two` | 奇正相生 Chính Kỳ | 2 approaches so sánh |
| `/plan:parallel` | 以迂為直 Vòng→thẳng | Dependency graph + File Ownership Matrix |
| `/plan:ci` | 近而靜者恃險 Gần im→hiểm | Log → Error → Codebase → Research → Plan |
| `/plan:cro` | 避實擊虛 Tránh mạnh đánh yếu | Conversion optimization |
| `/plan:archive` | 有所不爭 Không tranh hư | Clean old plans |
| `/plan:validate` | 法令孰行 Kỷ luật nghiêm | Validate structure |

### /cook Workflow (7 Steps)

```
Intent Detection → Research? → Review → Plan → Implement → Test? → Finalize
```

### /cook Flags × 風林火山

| Flag | Binh Pháp | Mode | Timeout | Tokens |
|:-----|:----------|:-----|:--------|:-------|
| `--fast` | 疾如風 GIÓ | Skip research | 15min | 30% |
| `--auto` | 徐如林 RỪNG | Skip human review | 30min | 60% |
| `--parallel` | 侵掠如火 LỬA | Agent Teams parallel | 45min | 100% |
| `--interactive` | Default | Stops at Review gates | 30min | 60% |
| `--no-test` | 必死可殺 ⚠️ | Skip tests (NGUY) | 15min | 30% |

### Quality Gates (luôn enforce trừ --no-test)
- Testing: 100% pass required
- Code Review: Auto-approve ≥9.5, 0 critical
- Finalize: project-manager + docs-manager MUST complete

### Execution Commands

| Command | Mục Đích |
|:--------|:---------|
| `/cook <task>` | Full implementation pipeline |
| `/debug <issue>` | 4-phase root cause investigation |
| `/test` | Run test suite (100% pass) |
| `/test:ui` | UI/E2E visual verification |
| `/review` | Code quality audit |
| `/review:codebase` | PARALLEL multi-agent review |
| `/check-and-commit` | Quality → commit → push |
| `/fix <issue>` | Quick bug fix |
| `/ask <question>` | Codebase intelligence |
| `/scout <what>` | Scan codebase structure |
| `/watzup` | Project status |
| `/kanban` | Task board |
| `/journal` | Development log |
| `/docs:update` | Documentation update |
| `/bootstrap <desc>` | New project init |
| `/worktree <name>` | Git worktree |

---

## 🔍 /debug Protocol — 4 PHASES (IRON LAW)

```
Phase 1 — ROOT CAUSE (行軍偵察 Trinh Sát)
  Read errors → Reproduce → Check changes → Gather evidence
  近而靜者恃其險 (gần mà im = ẩn hiểm)

Phase 2 — PATTERN (虛實分析 Hư Thực)
  Find working examples → Compare → Identify differences
  避實擊虛 (tránh mạnh đánh yếu)

Phase 3 — HYPOTHESIS (謀攻試驗 Mưu Công)
  Form theory → Test minimally → Verify
  上兵伐謀 (thượng sách phạt mưu)

Phase 4 — FIX (軍形落子 Quân Hình)
  Create test → Fix once → Verify fresh
  善守者藏九地之下 (phòng thủ sâu 9 tầng)

🔒 IRON LAW: NO FIX WITHOUT PHASE 1. NO DONE WITHOUT FRESH VERIFICATION.
```

---

## ⚔️ AGENT ORCHESTRATION × 兵勢 CHÍNH/KỲ

```
CHÍNH (正 Sequential) — Default:
  planner → fullstack-developer → tester → code-reviewer → git-manager

KỲ (奇 Parallel) — Wave execution:
  researcher(1) ┐
  researcher(2) ├──→ Aggregate → planner
  researcher(3) ┘

CHÍNH+KỲ (Hybrid) — Wave + Sequential mix:
  Wave 1 (Parallel): Phase 1 + Phase 2 + Phase 3
  Wave 2 (Sequential): Phase 4 (Integration)

FILE OWNERSHIP MATRIX:
  Phase 1: src/auth/**      — Tướng A
  Phase 2: src/analytics/**  — Tướng B
  Phase 3: src/settings/**   — Tướng C
  Phase 4: Integration sau khi 3 tướng xong
```

---

## 🧠 43 SKILLS × CỬU ĐỊA MATRIX

| Địa | Tình Huống | Skills |
|:----|:-----------|:-------|
| **散地** Dev local | `planning`, `brainstorm`, `sequential-thinking`, `research` |
| **輕地** Feature branch | `cook`, `fix`, `scout`, `git`, `code-review` |
| **爭地** Staging | `web-testing`, `devops`, `frontend-development`, `backend-development` |
| **交地** API contracts | `databases`, `mcp-builder`, `mcp-management`, `better-auth` |
| **衢地** Multi-platform | `shopify`, `payment-integration`, `mobile-development`, `google-adk-python` |
| **重地** Production | `debug`, `problem-solving`, `context-engineering`, `chrome-devtools` |
| **圮地** Legacy code | `repomix`, `docs-seeker`, `document-skills`, `find-skills` |
| **圍地** Deadline | `cook --fast`, `fix`, `plans-kanban`, `copywriting` |
| **死地** Prod down | `debug`, `devops`, `agent-browser`, `gkg` |

---

## COMPLEXITY ROUTING (Auto-select)

```
TRIVIAL   → /cook "task" --auto           (< 5 files, < 15min)
SIMPLE    → /plan:fast → /cook            (< 10 files, < 30min)
MODERATE  → /plan:hard → /cook → /test    (< 20 files, < 1h)
COMPLEX   → /plan:parallel → /cook phases (> 20 files, > 1h)
STRATEGIC → /plan:parallel [5] → phases   (Architecture-level)
```

---

_DNA Fusion #5 v5.0.0 | ClaudeKit v2.9.1 × Binh Pháp 13 Chương | 195 concepts | 🦞_

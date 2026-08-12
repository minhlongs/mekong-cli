# Workflows Overview / Tổng quan Workflows

> Mekong CLI uses **skills** as composable workflow blocks. There are **300+ skills** that cover everything from code review to business launch. This doc makes them discoverable and teachable.

> Mekong CLI sử dụng **kỹ năng (skills)** như các khối xây dựng workflow. Có **300+ kỹ năng** — từ review code đến ra mắt sản phẩm. Tài liệu này giúp phát hiện và sử dụng chúng.

---

## TOC / Mục lục

1. [What is a workflow? / Workflow là gì?](#what-is-a-workflow)
2. [The PEV Pipeline / Đường ống PEV](#the-pev-pipeline)
3. [Quick Commands / Lệnh nhanh](#quick-commands)
4. [Categorized Skills / Kỹ năng theo nhóm]
5. [Binh Phap Workflow / Binh Pháp Workflow]
6. [Swarm Mode / Swarm Mode]
7. [Composing Your Own / Tự xây workflow]
8. [FAQs]

---

## 1. What is a workflow? / Workflow là gì?

A **workflow** is just a named sequence of skills. It is not code. It is a recipe that says "do step 1, then step 2, then step 3." You run each step by typing `mekong <command>`.

Một **workflow** (quy trình) là một chuỗi các lệnh kỹ năng có tên. Không phải code, không phải plugin — chỉ là **công thức** gọi kỹ năng theo thứ tự: bước 1 → bước 2 → bước 3.

Each step triggers one skill. Skills are pre-built commands documented in `.claude/commands/`. No new code required for any workflow.

Mỗi bước kích hoạt một skill. Skills là lệnh có sẵn trong `.claude/commands/`. Không cần viết code để dùng workflow nào.

---

## 2. The PEV Pipeline / Đường ống PEV

This is the foundational workflow for every implementation task. Think of it as "Plan, Build, Check."

Đây là workflow nền tảng cho mọi công việc implement. Tương tự "Lập kế hoạch → Thực hiện → Kiểm tra."

```
mekong plan   →  mè kong cook  →  mè kong test  →  mè kong review  →  mè kong ship
    |               |                |                  |                 |
  Elicit          Execute          Validate          Quality           Release
  requirements    per plan         tests pass        gate              + PR
  Lấy yêu cầu   Thực hiện        Test đã pass        cổng             Ra
```

### Step-by-Step / Từng bước

| Step | Command | EN Purpose | Mục đích (VN) | MCU Cost |
|---|---|---|---|---|
| 1 | `plan` | Elicit requirements, produce a task tree | Lấy yêu cầu, tạo cây công việc | 1-2 |
| 2 | `cook` | Execute the plan step by step | Thực hiện từng bước theo plan | 2-4 |
| 3 | `test` | Run tests (unit + integration) | Chạy test (unit + integration) | 0-1 |
| 4 | `review` | Code review before merge | Review code trước khi merge | 1-2 |
| 5 | `ship` | Build + test + PR | Build + test + PR | 2-3 |

### When to use PEV / Khi nào dùng PEV

- **Use**: New feature, bug fix, refactor, anything that changes code.
  - *Dùng*: Feature mới, fix bug, refactor — bất cứ thay đổi code.
- **Skip**: Question, investigation, reading.
  - *Bỏ qua*: Hỏi đáp, điều tra, chỉ đọc.

---

## 3. Quick Commands / Lệnh nhanh

Một skill đơn lẻ có thể tự đáp ứng 80% nhu cầu hàng ngày. Dưới đây là menu nhanh.

### Core Development / Phát triển cốt lõi

| Command | EN Purpose | Mục đích (VN) | Typical Use |
|---|---|---|---|
| `scout` | Discover files/code patterns | Tìm file/pattern code | "Where is X?" |
| `ask` | Q&A with expert analysis | Hỏi đáp chuyên gia | "How does X work?" |
| `brainstorm` | Explore options before deciding | Động não trước khi quyết | "Should we do X or Y?" |
| `cook` | Execute a plan | Thực hiện kế hoạch | "Run this plan" |
| `review` | Code review before merge | Review trước merge | "Check my PR" |
| `debug` | Diagnose failures | Chẩn đoán lỗi | "Why is X broken?" |
| `fix` | Auto-repair code issues | Sửa lỗi tự động | "Fix this bug" |
| `test` | Run test suite | Chạy test suite | "Are tests green?" |
| `journal` | Document decisions | Ghi quyết định | "Log this lesson" |
| `verification-before-completion` | Self-check before finishing | Tự kiểm tra | Final checkpoint |

### Business Operations / Vận hành Doanh nghiệp

| Command | EN Purpose | Mục đích (VN) |
|---|---|---|
| `business-campaign-launch` | Marketing campaign planning | Lập kế hoạch chiến dịch marketing |
| `business-financial-close` | Month-end closure checklist | Checklist đóng sổ cuối tháng |
| `business-client-onboard` | New client onboarding flow | Quy trình onboard khách mới |
| `marketing-strategy` | Marketing strategy & positioning | Chiến lược & định vị marketing |
| `pricing-strategy` | Pricing experiments | Thử nghiệm định giá |
| `sales-pipeline` | Sales automation + forecast | Tự động bán hàng + dự báo |

### Engineering / Kỹ thuật

| Command | EN Purpose | Mục đích (VN) |
|---|---|---|
| `backend-api-build` | Backend API scaffolding | Khung API backend |
| `backend-db-task` | Database migration/task | Việc CSDL / migration |
| `deploy` | Deployment automation | Tự động deploy |
| `testing-patterns` | TDD/BDD pattern library | Thư viện pattern TDD/BDD |
| `devops` | Docker + CI/CD pipelines | Docker + CI/CD |
| `performance-tuning` | Performance optimization | Tối ưu hiệu năng |

### Security / Bảo mật

| Command | EN Purpose | Mục đích (VN) |
|---|---|---|
| `security` | Security posture audit | Kiểm tra bảo mật |
| `security-scan` | Secrets/vulnerability scan | Quét secrets/lỗ hổng |
| `cti-expert` | OSINT/threat-intel | Trinh sát mạng |

---

## 4. Categorized Skills / Kỹ năng theo nhóm

Skills live in `.claude/skills/<skill-name>/SKILL.md`. Run `mekong` and a skill will auto-activate when relevant.

Kỹ năng nằm ở `.claude/skills/<tên>/SKILL.md`. Chạy `mekong` với công việc liên quan → skill tự động kích hoạt.

### Frontend / UI / Trang trước

| Skill | Use when / Dùng khi |
|---|---|
| `ui-ux-pro-max` | Choose colors, fonts, layout |
| `threejs` | 3D / WebGL / Three.js |
| `shader` | GLSL / procedural graphics |
| `tailwind-patterns` | Tailwind + shadcn/ui |
| `frontend-development` | React/TS components |

### Backend / API

| Skill | Use when / Dùng khi |
|---|---|
| `backend-development` | REST/GraphQL (NestJS, FastAPI) |
| `better-auth` | OAuth, JWT, Passkeys |
| `databases` | Schema design, SQL/NoSQL |
| `integration` | Phần mềm tích hợp |

---

## 4.5. FABRIC DAG / FABRIC DAG (Catalog Flow)

The Mekong Command Fabric is a **Directed Acyclic Graph (DAG)** of capabilities.
It reads `.claude/commands/*.md` (117+ command schemas) and `.claude/skills/*/SKILL.md`
(300+ skill definitions), then exports a unified catalog that powers
CLI, IDE completions, SDKs, MCP, shell, and vim/helix/zed/nova/emacs.

### En (English)

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                     MEKONG COMMAND FABRIC                       │
  │                       (Single Source of Truth)                   │
  └────────────────────────────┬─────────────────────────────────────┘
                               │ reads
                    ┌──────────▼──────────┐
                    │ .claude/commands/*  │ 117 command schemas / markdown
                    └──────────┬──────────┘
                               │ joins
              ┌────────────────▼────────────────┐
              │  factory/contracts/commands/*.json│  Layer metadata, MCU costs, contracts
              └────────────────┬────────────────┘
                               │ builds
              ┌────────────────▼────────────────┐
              │  src/command_fabric/catalog.py   │  build_command_catalog()
              │  · CommandRecord dataclass       │  name, source, description,
              │  · export_command_catalog()      │  execution, layer, targets
              └────────────────┬────────────────┘
                               │ feeds
    ┌──────────────────────────┼──────────────────────────────┐
    │                          │                              │
    ▼                          ▼                              ▼
 ┌───────┐              ┌──────────────┐           ┌──────────────────┐
 │  CLI  │              │  CLI + MCP + │           │  IDE / Editor +  │
 │ Typer │              │  SDK Adapter  │           │  Shell Packages  │
 │mekong │              │  Exporters    │           │  (22 targets)     │
 └───┬───┘              └──────┬───────┘           └────────┬─────────┘
     │                         │                             │
     ▼                         ▼                             ▼
 ┌─────────┐           ┌──────────┐              ┌───────────────────┐
 │ claude  │           │ vscode,  │              │ claude-code, vim, │
 │  code   │           │ cursor,  │              │ neovim, helix,    │
 │ slash   │           │  jetbrains│              │ zed, emacs, shell │
 │ cmds    │           │  mcp     │              │ waka, xiaoshuyi   │
 └─────────┘           └──────────┘              └───────────────────┘
     │                      │
     ▼                      ▼
  User types `mekong ...`  →  command routed by `/binh-phap win` / governance gates
```

### Tiếng Việt

`mekong workflow list` và `mekong workflow show` đọc FABRIC catalog:

- `workflow list [--domain <id>]` → nhóm kỹ năng theo 10 lĩnh vực.
- `workflow show <name>` → metadata đầy đủ: source, execution, contract, layer, targets.

### Domain Order / Thứ tự nhóm

```
👑 Founder   💼 Business   🎯 Product   ⚙️ Engineering   🔧 Ops   🏯 Studio
🎪 Strategy  ✍️ Content    🤖 Agent     📚 Docs          ⚖️ Legal
```

### Safety / An toàn

- **`cli/tui/router.py`** is Track 1 — DO NOT modify.
- FABRIC reads markdown at runtime (no code generation).
- DAG: command markdown → record → export → consumer. No cycle; one-directional.

### Skill Catalog Table — Top 30 Skills by Domain / Bảng Kỹ năng — 30 đại diện theo nhóm

| # | Skill | Domain (EN) | Domain (VN) | Typical Invoke |
|---|-------|------------|------------|----------------|
| 1 | `binh-phap` | Strategy / Chiến lược | 5-layer military analysis | `/binh-phap` |
| 2 | `cook` | Engineering / Kỹ thuật | Execute a plan step-by-step | `mekong cook` |
| 3 | `plan` / `ask` | Ops / Vận hành | Decompose goal → task tree | `mekong plan`, `mekong ask` |
| 4 | `review` | Engineering / Kỹ thuật | Code review gate | `mekong review` |
| 5 | `scout` | Ops / Vận hành | Discover files / code | `mekong scout` |
| 6 | `fix` / `debug` | Engineering / Kỹ thuật | Auto-repair / diagnose | `mekong fix`, `mekong debug` |
| 7 | `brainstorm` | Product / Sản phẩm | Ideate before deciding | `mekong brainstorm` |
| 8 | `deploy` | Engineering / Kỹ thuật | CF-only deploy + SHA verify | `mekong deploy` |
| 9 | `test` / `security` | Engineering/Ops | TDD / security audit | `mekong test`, `mekong security` |
| 10 | `frontend-development` | Engineering | React / Next.js RSC | invoked by `cook` |
| 11 | `backend-development` | Engineering | REST/GraphQL scaffold | invoked by `cook` |
| 12 | `databases` | Engineering | D1/Supabase schema design | invoked by `cook` |
| 13 | `better-auth` | Engineering | OAuth/JWT/passkeys | invoked by `cook` |
| 14 | `security-scan` | Ops | Secrets / OWASP sweep | `mekong security-scan` |
| 15 | `cti-expert` | Ops | OSINT / threat intel | `mekong cti-expert` |
| 16 | `sales` | Business | Sales automation + pipeline | `mekong sales` |
| 17 | `marketing` / `marketing-*` | Business | Copy / SEO / CRO / ads | `mekong marketing` |
| 18 | `business-campaign-launch` | Business | Multi-channel campaign | `mekong business-campaign-launch` |
| 19 | `pricing-strategy` | Business | Pricing experiments | `mekong pricing-strategy` |
| 20 | `fundraise` | Founder | Investor outreach deck | `mekong fundraise` |
| 21 | `annual` / `okr` | Founder | Annual plan / OKRs | `mekong annual`, `mekong okr` |
| 22 | `swot` | Founder | Strengths / weaknesses | `mekong swot` |
| 23 | `audit` / `audit-execute` | Ops | `SOX` / `ITGC` / trail | `mekong audit` |
| 24 | `docx` / `pptx` / `xlsx` | Content / Docs | Office artifacts | `mekong docx/pptx/xlsx` |
| 25 | `ai-multimodal` | Content | Image/video generation | `mekong ai-multimodal` |
| 26 | `watzup` / `journal` | Ops | EOD handoff / lesson log | `mekong watzup`, `mekong journal` |
| 27 | `use-mcp` | Engineering | MCP server consumption | `mekong use-mcp` |
| 28 | `docs-seeker` | Docs | Up-to-date lib/framework docs | `mekong docs-seeker` |
| 29 | `context-engineering` | Agent | Memory / RAG / context | invoked on long-horizon tasks |
| 30 | `skill-creator` | Meta | Custom SKILL.md authoring | `mekong skill-creator` |

> **Note / Lưu ý:** 30/300+ đại diện. Chạy `mekong workflow list` — danh sách đầy đủ.  
> Run `mekong workflow list` — full coverage.

### CLI Surface / Giao diện CLI

```bash
mekong workflow list            # All skills / Tất cả kỹ năng
mekong workflow list --domain engineering  # Filter one domain
mekong workflow show cook      # Full metadata for one skill
mekong workflow domains        # List 10 domain ids with bilingual labels
```

### Source of Truth / Nguồn chân lý

- **Markdown:** `.claude/commands/*.md` (117 schemas)
- **Skill impl:** `.claude/skills/*/SKILL.md` (300+ impls)
- **Python catalog:** `src/command_fabric/catalog.py :: build_command_catalog()`
- **Schema:** `mekong.command_fabric.v1` (`schema`, `count`, `commands[]`)

---

## 5. Binh Phap Workflow / Binh Pháp Workflow

Run `/binh-phap` to invoke the 5-layer military strategy workflow.

Run `/binh-phap` to invoke the 5-layer military strategy workflow.

This is a decision-making framework, not a code workflow. Each layer produces structured output.

Dùng `/binh-phap` để kích hoạt chiến lược 5 tầng Binh Pháp.

Đây là khung ra quyết định, không phải workflow code. Mỗi tầng tạo output có cấu trúc.

| Layer | EN Name | Phương thức Binh Pháp | Purpose |
|---|---|---|---|
| 1 | Situation | Trinh sát (Scout) | Understand the terrain |
| 2 | Assessment | Phân tích mạnh yếu (Assess) | Strengths / weaknesses |
| 3 | Strategy | Bày kế (Strategy) | Deception / leverage |
| 4 | Execution | Tấn công (Attack) | Multi-vector push |
| 5 | Review | Kiểm tra (Review) | Outcome / lessons |

### Example usage / Ví dụ

```bash
mekong ask "Should we enter the VietnamB2B market?"   # Quick answer
mekong binh-phap                                      # Full 5-layer analysis
mekong brainstorm "VietnamB2B entry strategies"       # Ideate options
mekong plan "VietnamB2B MVP build"                    # Plan from decision
```

---

## 6. Swarm Mode / Swarm Mode

When a task is too large for one agent, use Swarm Mode to parallelize. Each agent works on a clearly-owned slice of work.

Khi công việc quá lớn cho 1 agent, dùng Swarm Mode để song song hóa. Mỗi agent làm phần việc thuộc sở hữu rõ ràng.

```bash
mekong workflows parallel   # Start a parallel plan with slice assignment
```

**Rule:** Each subagent must have its own file scope. Never two agents writing to the same file in parallel.

**Quy tắc:** Mỗi subagent phải có scope file riêng. Không hai agent cùng ghi 1 file.

Swarm Mode is activated automatically by `plan --parallel`. The planner agent assigns file ownership to each subagent before spawning.

Swarm Mode tự động bật qua `plan --parallel`. Planner agent gán quyền sở hữu file cho mỗi subagent trước khi spawn.

---

## 7. Composing Your Own / Tự xây Workflow

A workflow is just you running skills in order. Example — **Launch a new product feature**:

### EN

1. `mekong ask "what's the simplest MVP for X?"` — ask first
2. `mekong brainstorm "X feature options"` — explore options
3. `mekong plan` — produce a task tree
4. `mekong worktree new-feature` — isolate work
5. `mekong cook` — execute
6. `mekong test` — validate
7. `mekong review` — quality gate
8. `mekong ship` — release

### Tiếng Việt

1. `mekong ask "MVP đơn giản nhất cho X là gì?"` — hỏi trước
2. `mekong brainstorm "các option feature X"` — thảo luận
3. `mekong plan` — tạo cây công việc
4. `mekong worktree new-feature` — cô lập công việc
5. `mekong cook` — thực hiện
6. `mekong test` — kiểm tra
7. `mekong review` — cổng chất lượng
8. `mekong ship` — ra mắt

**Tip:** If in doubt, start with `ask` or `brainstorm`. Planning before you know what you want is the #1 mistake. / *Nếu không chắc, bắt đầu với `ask` hoặc `brainstorm`. Lập kế hoạch trước khi biết mình muốn gì là lỗi phổ biến nhất.*

---

## 8. FAQs / Câu hỏi thường gặp

### "Is a skill different from a command?"
Skills are the **implementation**. Commands are the **handles** you type. Each command in `.claude/commands/` triggers one or more skills in `.claude/skills/`.

*Skill là phần triển khai. Command là phần bạn gõ. Mỗi command kích hoạt một hoặc nhiều skill.*

### "How many skills are there?"
~300 skills as of this version. Run `mekong workflows` for the live list.

*Khoảng ~300 skills. Dùng `mekong workflows` để xem danh sách mới nhất.*

### "Can I add my own skill?"
Yes. Add a new folder under `.claude/skills/<name>/SKILL.md` following the existing format. It will auto-load next time you run `mekong`.

*Có. Thêm thư mục mới dạng `.claude/skills/<tên>/SKILL.md` theo format hiện có.*

### "Where are workflows defined?"
Workflows are defined across two places: `.claude/skills/` (skill implementations) and this doc (workflow descriptions + recipes). There is no separate "workflow code" file — workflows are emergent from skill composition.

*Workflows định nghĩa ở 2 chỗ: `.claude/skills/` (implement skill) và tài liệu này (mô tả workflow + công thức). Không có file "workflow code" riêng — workflows tạo ra từ sự kết hợp skill.*

---

## Version / Phiên bản

| Field | Value |
|---|---|
| Document | `docs/workflows-overview.md` |
| CLI version | `6.0.0` |
| Last updated | 2026-07-12 |
| Maintainer | OpenClaw Engineering |

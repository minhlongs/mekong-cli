---
description: "List and describe available workflows and skills as composable building blocks. Shows PEV Pipeline, Swarm Mode, Binh Phap, and categorized skills."
argument-hint: "[workflow-name]"
allowed-tools: Bash, Read, Agent
---

# /workflows — Workflow Catalog

List available workflows and skills. Each workflow is a documented sequence of skills that solves a specific class of problem.

**Learn more:** `docs/workflows-overview.md`

## Usage

```bash
mekong workflows              # Show all workflows
mekong workflows pev          # Show PEV Pipeline details
mekong workflows cook        # Show Cook workflow details
mekong workflows binh-phap   # Show Binh Phap details
```

## Core Workflows

| Workflow | EN | Tiếng Việt |
|---|---|---|
| **PEV Pipeline** | Plan → Execute → Verify | Lập kế hoạch → Thực hiện → Kiểm tra |
| **Swarm Mode** | Parallel agent coordination | Phối hợp song song đa agent |
| **Binh Phap** | 5-layer military strategy | Chiến lược 5 tầng Binh Pháp |
| **Core Dev Loop** | scout → cook → test → review | trinh sát → nấu ăn → test → review |
| **Bugfix Flow** | scout → debug → fix → test | trinh sát → debug → sửa → test |
| **Investigation** | scout → debug → brainstorm → plan | trinh sát → debug → brainstorm → plan |

## Quick Commands (Skills as Workflow Blocks)

| Command | EN Purpose | Mục đích (VN) |
|---|---|---|
| `ask` | Q&A with expert analysis | Hỏi đáp chuyên gia |
| `brainstorm` | Explore options before deciding | Khám phá phương án |
| `plan` | Design implementation steps | Thiết kế kế hoạch |
| `cook` | Execute a plan end-to-end | Thực hiện kế hoạch |
| `review` | Code review before merge | Review trước khi merge |
| `scout` | Discover relevant code/files | Khám phá code |
| `debug` | Diagnose failures | Chẩn đoán lỗi |
| `fix` | Auto-repair code issues | Sửa lỗi |
| `test` | Run test suite | Chạy test suite |
| `journal` | Document decisions | Ghi lại quyết định |
| `verification-before-completion` | Self-check before finishing | Tự kiểm tra trước khi xong |
| `ship` | Full shipping pipeline (CI + PR) | Đẩy lên production |

## Category: Business / Vận hành Doanh nghiệp

| Command | EN | Mục đích (VN) |
|---|---|---|
| `business-campaign-launch` | Marketing campaign planner | Lập kế hoạch chiến dịch marketing |
| `business-financial-close` | Month-end closure checklist | Checklist đóng sổ cuối tháng |
| `business-client-onboard` | New client onboarding guide | Hướng dẫn onboard khách mới |
| `sales-pipeline` | Sales process automation | Tự động hóa pipeline bán hàng |
| `marketing-strategy` | Marketing strategy framework | Khung chiến lược marketing |

## Category: Engineering / Kỹ thuật

| Command | EN | Mục đích (VN) |
|---|---|---|
| `backend-api-build` | Backend API scaffolding | Khung API backend |
| `backend-db-task` | Database migration/task | Việc CSDL / migration |
| `test` | TDD/BDD test runner | Chạy test TDD/BDD |
| `test-driven-development` | TDD workflow pattern | Pattern TDD |
| `deploy` | Deployment automation | Tự động hóa deploy |
| `code-review` | Pre-merge code review | Review code trước merge |
| `docs` | Documentation update | Cập nhật tài liệu |

## Category: Product / Sản phẩm

| Command | EN | Mục đích (VN) |
|---|---|---|
| `idea` | BizPlan OS (idea → company blueprint) | OS BizPlan (ý tưởng → bản thiết kế công ty) |
| `plan` | Implementation planner | Lập kế hoạch implement |
| `brainstorm` | Ideation / solution evaluation | Động não / đánh giá giải pháp |
| `roadmap` | Product roadmap | Lộ trình sản phẩm |
| `scope` | Feature scope definition | Định nghĩa scope |

## Category: Ops / Vận hành Hệ thống

| Command | EN | Mục đích (VN) |
|---|---|---|
| `health` | System health check | Kiểm tra sức khoẻ hệ thống |
| `audit` | Security/compliance audit | Audit bảo mật/tuân thủ |
| `status` | Current status dashboard | Dashboard trạng thái hiện tại |
| `clean` | Project cleanup | Dọn dẹp dự án |
| `security` | Security posture audit | Kiểm tra bảo mật |

## Binh Phap Chain (Spec) / Chuỗi Binh Pháp (Yêu cầu)

Use `/binh-phap` for full 5-layer strategic analysis.

| Layer | EN | Phương thức Binh Pháp |
|---|---|---|
| 1 | Scout situation | Trinh sát |
| 2 | Analyze strengths/weaknesses | Phân tích mạnh yếu |
| 3 | Plan deception / leverage | Bày kế lường lợi |
| 4 | Execute multi-vector attack | Đa trọng tấn công |
| 5 | Verify outcome / learn | Kiểm tra / rút kinh nghiệm |

## Examples

```bash
mekong workflows              # Show full catalog
mekong workflows pev          # Deep-dive on PEV workflow
mekong workflows cook        # Show Cook usage
mekong workflows binh-phap   # Show Binh Phap strategy
mekong ask "How does OAuth work?"  # Use ask skill directly
mekong brainstorm "How to scale uploads?"  # Brainstorm first, then plan
```

---

## How to Build a Custom Workflow / Tự xây Workflow Riêng

A custom workflow = a sequence of skills triggered by you via `mekong <command>`. No code required.

**Example: Launch Solar / Bắt đầu thử nghiệm Solar**

```bash
mekong ask "What should we build first for the Solar AI product?"   # 1. Explore
mekong brainstorm "Solar AI MVP feature options"                     # 2. Ideate
mekong plan "Build Solar AI MVP"                                     # 3. Plan
mekong worktree solar-ai                                            # 4. Isolate
mekong cook solar-ai/plans/phase-01.md                              # 5. Execute
mekong test                                                          # 6. Validate
mekong review                                                        # 7. Review
mekong ship                                                          # 8. Ship
```

Skills are composable — any sequence works. Start with the one closest to your need.

**Tip:** Run `mekong workflows` before starting to see the full menu.

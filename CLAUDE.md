# MEKONG CLI v6.0 — OPENCLAW CONSTITUTION
*"I am OpenClaw. I run this company."*

**Mekong CLI** — AI-operated business platform. Open source. Universal LLM.
**Version:** 6.0.0 | **License:** MIT | **Language:** English

---

## NAMESPACE

| Location | Content |
|----------|---------|
| `.claude/skills/` | 542 skill definitions (SKILL.md) |
| `.claude/commands/` | 342+ command definitions (.md) — dispatch to `mekong` engine |
| `mekong/agents/` | Agent definitions |
| `mekong/adapters/` | LLM provider configs |
| `mekong/infra/` | 3-layer deploy templates (CF-only) |
| `mekong/daemon/` | Tôm Hùm autonomous dispatch |
| `factory/contracts/` | 567 JSON machine contracts |
| `clipmart/` | Paperclip Agent Companies templates (PUBLIC marketplace) |
| `mekong/` | Adapters, infra, daemon (NOT skills/commands) |

CC CLI reads `.claude/skills/` and `.claude/commands/` directly. NO symlinks.

---

## UNIFIED WRAPPER — `mekong` is the ONLY entry point

```
mekong-cli (outer shell)  →  CC CLI (inner engine)  →  .claude/commands/ (300+ commands)
scripts/mekong-wrapper.sh    claude|gemini|qwen|bb     135 root + package commands
scripts/shell-init.sh        --dangerously-skip-perms  257 skills auto-loaded
```

### Quick Start

```bash
source ~/mekong-cli/scripts/shell-init.sh   # Add to .zshrc/.bashrc

mekong              # Interactive CC CLI with all mekong commands
mekong-opus         # Force Anthropic Claude Opus 4.6
mekong-sonnet       # Force Anthropic Claude Sonnet 4.6
mekong-qwen         # Force DashScope Qwen 3.5 Plus
mekong-cto          # CTO daemon mode (P->D->V->S loop)
mekong-continue     # Resume last session
mekong-print "task" # Non-interactive (pipe output)
mekong-status       # Show current API config
```

### Provider Routing

| Alias | Provider | Binary | Model |
|-------|----------|--------|-------|
| `mekong` | claude (default) | `claude` | CC CLI default |
| `mekong-opus` | claude | `claude` | claude-opus-4-6 |
| `mekong-qwen` | dashscope | `claude` | qwen3.5-plus |
| `mekong --provider gemini` | google | `gemini` | gemini default |

All providers launch from `~/mekong-cli` root, ensuring `.claude/commands/` discovery.

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│  CLI: mekong cook/fix/plan/deploy/...              │
│  IDE: ide.mekongmind.com → /v1/missions            │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  API Gateway       │  FastAPI + auth + MCU check
         │  src/api/          │  HTTP 402 on zero balance
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  PEV Engine        │  src/core/
         │  planner.py        │  LLM task decomposition
         │  executor.py       │  shell/LLM/API execution
         │  verifier.py       │  quality gates + rollback
         │  orchestrator.py   │  Plan→Execute→Verify loop
         └─────────┬──────────┘
                   │
    ┌──────────────▼──────────────────┐
    │  Agent Layer   src/agents/      │
    │  GitAgent  FileAgent  ShellAgent│
    │  LeadHunter  ContentWriter      │
    └──────────────┬──────────────────┘
                   │
         ┌─────────▼──────────┐
         │  LLM Router        │  src/core/llm_client.py
         │  3 vars, any provider │
         └────────────────────┘
```

### 6 Layers

```
🏯 Studio     /studio:launch /dealflow /venture /expert  — VC studio ops (23 cmds)
👑 Founder    /annual /okr /fundraise /swot               — Strategy (52 cmds)
💼 Business   /sales /marketing /finance /hr               — Revenue (71 cmds)
🎯 Product    /plan /sprint /roadmap /brainstorm           — Product (31 cmds)
⚙️ Engineering /cook /code /test /deploy /review           — Build (66 cmds)
🔧 Ops        /audit /health /security /status             — Monitor (41 cmds)
```

---

## LLM CONFIG — Universal Endpoint (3 vars, any provider)

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4
```

**Presets:** `mekong/adapters/llm-providers.yaml`
**Fallback chain:** `OPENROUTER_API_KEY` → `DASHSCOPE_API_KEY` → `DEEPSEEK_API_KEY` → `ANTHROPIC_API_KEY` → `OPENAI_API_KEY` → `GOOGLE_API_KEY` → `OLLAMA_BASE_URL` → OfflineProvider

---

## COMMANDS (Top per layer)

| Layer | Commands | MCU |
|-------|----------|-----|
| 👑 Founder | `annual`, `okr`, `swot`, `fundraise`, `pitch`, `vc/cap-table`, `ipo/*` | 1-5 |
| 💼 Business | `sales`, `marketing`, `finance`, `hr`, `pricing`, `brand` | 1-5 |
| 🎯 Product | `plan`, `sprint`, `roadmap`, `brainstorm`, `scope` | 1-3 |
| ⚙️ Engineering | `cook`, `fix`, `code`, `test`, `deploy`, `review` | 1-5 |
| 🔧 Ops | `audit`, `health`, `security`, `status`, `clean` | 0-3 |

Total: 342+ commands (284 base + 23 studio + 89 super + DAG recipes). Run `mekong help` for full list.

---

## CLAUDEKIT BRIDGE — Mekong-First Policy

**User assertion #1:** All slash commands MUST dispatch to mekong CLI engine.

When running via `mekong` (cwd=`~/mekong-cli`), CC CLI discovers `.claude/commands/` here (396+ cmds).
When running bare `claude` from `~`, it only sees `~/.claude/commands/` (18 claudekit-only cmds).

**Policy:** For best results, always use `mekong` not bare `claude`.

### Claudekit → Mekong Command Map

| Claudekit (`~/.claude`) | Mekong (`mekong-cli/.claude`) | Status |
|------------------------|-------------------------------|--------|
| `/binh-phap` | `/ck-binh-phap` | Identical — use mekong version |
| `/remember` | `/ck-remember` | Identical — use mekong version |
| `/save` | `/ck-save` | Identical — use mekong version |
| `/techdebt` | `/ck-techdebt` | Identical — use mekong version |
| `/marketing` | `/ck-marketing` | Identical — use mekong version |
| `/marketing-ads` | `/ck-marketing-ads` | Identical — use mekong version |
| `/marketing-copy` | `/ck-marketing-copy` | Identical — use mekong version |
| `/marketing-cro` | `/ck-marketing-cro` | Identical — use mekong version |
| `/marketing-growth` | `/ck-marketing-growth` | Identical — use mekong version |
| `/marketing-local` | `/ck-marketing-local` | Identical — use mekong version |
| `/marketing-seo` | `/ck-marketing-seo` | Identical — use mekong version |
| `/idea` (simple 4-step) | `/idea` (25-step BizPlan OS) | Mekong wins — more complete |
| `/raas-flow` | `/ck-raas-flow` | Ported (2026-04-16) |
| `/vercel-debug` | `/vercel-debug` | Ported (2026-04-16) |
| `/claude-mem` | `/ck-claude-mem` | Ported (2026-04-16) |
| `/cc-cli-input-rules` | `.claude/rules/cc-cli-input-rules.md` | Rule (not command) |
| `trading/*` | `trading/*` | Ported (2026-04-16) — 42 files |

### New Commands Added (2026-04-16)

- `/ck-raas-flow` — RAAS pipeline status dashboard across all plans/
- `/vercel-debug` — Vercel CI/CD debug + verification loop
- `/ck-claude-mem` — Memory management via claude-mem MCP
- `trading/` — 42 trading-context C-suite + analyst persona commands

---

## QUALITY RULES

| Rule | Standard |
|------|----------|
| File size | < 200 lines (split into modules) |
| Type hints | Required for all functions |
| Docstrings | Every class and public method |
| Tests | `python3 -m pytest tests/` must pass |
| Naming | snake_case (Python), kebab-case (files) |
| Secrets | Never in code — use `.env` |
| Commits | Conventional: `feat/fix/refactor/docs/test/chore` |
| No automation refs | Clean commit messages |

### Binh Phap Quality Fronts

| Front | Target |
|-------|--------|
| Tech Debt | 0 TODO/FIXME, 0 console.log |
| Type Safety | 0 `any` types, strict mode |
| Performance | Build < 10s, LCP < 2.5s |
| Security | Input validation, no secrets |
| UX | Loading states, error boundaries |
| Documentation | Self-documenting code |

## 🚨 PUBLIC REPO BOUNDARY — KHÔNG ĐƯỢC VI PHẠM

**mekong-cli là PUBLIC repo.** Bất kỳ ai trên internet đều thấy.

### ❌ CẤM TUYỆT ĐỐI commit/push:
| Path | Lý do |
|------|-------|
| `apps/` | Dự án khách hàng PRIVATE (algo-trader, sophia, well...) |
| `mekong/daemon/` | Internal CTO brain, API keys, secrets |
| `mekong/hooks/` | Internal automation hooks |
| `.env`, `.env.*` | Secrets, API keys |
| `*.pem`, `*.key` | Certificates |

### ✅ CHỈ commit/push:
| Path | Nội dung |
|------|----------|
| `packages/` | openclaw-engine, mekong-cli-core (PUBLIC SDK) |
| `recipes/` | Command recipes (PUBLIC) |
| `.claude/skills/` | Skill definitions (PUBLIC) |
| `.claude/commands/` | Command definitions (PUBLIC) |
| `factory/contracts/` | Machine contracts (PUBLIC) |
| `clipmart/` | Clipmart marketplace templates (PUBLIC) |
| Root files | package.json, tsconfig, README, CLAUDE.md |

### Khi `git add -A` hoặc `git commit`:
1. **LUÔN kiểm tra** `git diff --cached --name-only` trước khi commit
2. Nếu thấy `apps/` hoặc `mekong/daemon/` → **DỪNG LẠI**, chạy `git reset HEAD -- apps/ mekong/daemon/`
3. Pre-commit hook sẽ block, nhưng **đừng dùng --no-verify**

---

## GIT PROTOCOL

```bash
# Pre-commit: blocks apps/ + secrets + runs tsc
# Pre-push: pytest must pass
# Commit format:
feat: add new command
fix: resolve billing edge case
refactor: simplify PEV orchestrator
```

Never commit: `.env`, API keys, `node_modules`, `__pycache__`, `.pyc`, `apps/`, `mekong/daemon/`

---

## DEPLOY — 3-Layer Infrastructure (Cloudflare-only)

| Layer | Platform | Cost |
|-------|----------|------|
| Frontend | Cloudflare Pages | $0 |
| Edge API | Cloudflare Workers | $0 |
| Backend | Cloudflare Workers + D1 + KV + R2 | $0 |

```bash
bash mekong/infra/scaffold.sh myproject startup  # frontend + API
bash mekong/infra/scaffold.sh myproject scale     # all 3 layers
```

Deploy: CF Pages (frontend via `git push`) + CF Workers (backend via `wrangler deploy`). No other platforms.

---

## MCU BILLING

1 MCU = 1 credit. Deduct after successful delivery only.

| Tier | Credits/mo | Price |
|------|-----------|-------|
| Starter | 200 | $49 |
| Growth | 1,000 | $149 |
| Pro | 5,000 | $499 |

- Zero balance → HTTP 402
- Polar.sh webhooks → license provisioning + credit allocation
- Audit trail for every transaction

---

## STAKEHOLDERS

| Role | Share | Responsibility |
|------|-------|---------------|
| OpenClaw CTO | 80% | Plan, execute, verify, deploy |
| CC CLI Worker | — | Subagent execution |
| Human | 10% | Approve, review, strategic decisions |
| Customer | 10% | Submit goals, pay credits |

---

## SUBAGENT DELEGATION (Claude Code standard)

Standard pattern — every long task delegates specialised work via `Task`:

| Phase | Subagent | Source | When |
|-------|----------|--------|------|
| Scout | `Explore` | global | Discover relevant files / multi-step search |
| Research | `researcher` | global | External tech / docs research |
| Plan | `planner` | global | Multi-phase implementation plan |
| Implement | `fullstack-developer` | global | Code changes per phase |
| Test | `tester`, `debugger` | global | **MUST** spawn before ship |
| Review | `code-reviewer` | global | **MUST** spawn before merge |
| Finalize | `project-manager`, `docs-manager`, `git-manager` | global | **MUST** spawn all 3 |

All 14 stock subagents resolve from `~/.claude/agents/` per the Option B
layering (architecture-mapping.md). Mekong-domain agents live in
`.claude/agents/` (only override-with-purpose, see `why-override:` headers).

**Why this matters (Boris Cherny tip #8):** keep the main session context
clean by handing off context-heavy work (full test runs, deep research,
big diff reviews) to subagents that have their own 200K token budget.
The lead session orchestrates, the subagents execute.

Reference: <https://docs.claude.com/en/docs/claude-code/sub-agents>

---

## CLAUDE CODE STANDARD COMPLIANCE

`.claude/` follows the official project layout (verified 2026-05-03):

- `.claude/agents/`        — 6 mekong-domain agents (14 stock pulled from `~/.claude/`)
- `.claude/commands/`      — ~399 domain commands (3 with `why-override:`)
- `.claude/skills/`        — 195 skills, 100% compliant frontmatter (post-backfill)
- `.claude/hooks/`         — pre-tool-use guard, stop-checkpoint, etc.
- `.claude/output-styles/` — 6 coding-level personas (eli5 → god)
- `.claude/settings.json`  — `permissions.deny/ask` + `enableAllProjectMcpServers`
- `.claude/statusline.sh`  — custom statusline (Boris Cherny tip #7)
- `.ci/check-no-duplicate-claudekit.sh` — pre-commit guard against re-introduced dups

Mapping report:
`~/projects/sophia-ai-factory/plans/260503-0443-claudekit-mekong-architecture-mapping/`

References:
- <https://docs.claude.com/en/docs/claude-code/skills>
- <https://docs.claude.com/en/docs/claude-code/settings>
- <https://docs.claude.com/en/docs/claude-code/memory>

---

## SESSION BOOTSTRAP

Every session:
1. Read `.mekong/company.json` (if exists)
2. Load active tasks from `.mekong/tasks/`
3. Print: `"OpenClaw online. [N] pending tasks. Ready."`
4. If no `company.json` → suggest: `mekong company/init`

**Language:** English for all documentation and code. Vietnamese for user-facing content when configured.

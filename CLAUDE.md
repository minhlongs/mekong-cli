# 📜 MEKONG-CLI BINH PHÁP RULES

> **RaaS Agency Operating System** - Powered by ClaudeKit DNA + Binh Pháp Framework

---

## 第一篇 始計 (Shi Ji) - PROJECT FOUNDATION

> "Binh giả, quốc chi đại sự" - Architecture is a matter of vital importance

### Language & Framework

| Component      | Technology             |
| -------------- | ---------------------- |
| **Language**   | Python 3.11+           |
| **CLI**        | Typer (Commands)       |
| **UI**         | Rich (Terminal UI)     |
| **Validation** | Pydantic (Type Safety) |

### Architecture Pattern

```
src/core/
├── planner.py      # 謀 Planning - Task decomposition
├── executor.py     # 執 Execution - Multi-mode runner (shell/LLM)
├── verifier.py     # 證 Verification - Result validation
└── orchestrator.py # 統 Orchestration - Plan→Execute→Verify flow

packages/
├── core/           # Foundation SDKs (vibe, agents, shared)
├── integrations/   # External connectors (bridge, CRM)
├── tooling/        # Developer utilities (dev, analytics)
├── business/       # Revenue logic (money, ops, marketing)
└── ui/             # Interface components (vibe-ui, i18n)
```

- **Modular Agents:** Mỗi agent là 1 folder riêng trong `/agents`
- **DNA:** Luôn tuân thủ logic **Plan-Execute-Verify** của ClaudeKit
- **Hub Architecture:** Monorepo với logical grouping theo layer

---

## 第三篇 謀攻 (Mou Gong) - CODE STANDARDS

> "Thượng binh phạt mưu" - Excellence through planning first

### Quality Requirements

- ✅ Type hinting required cho tất cả functions
- ✅ Docstring cho mọi class và public method
- ✅ Test cho mọi module trong `/tests`

### Execution Flow (Plan-Execute-Verify)

```
1. PLAN    → RecipePlanner decomposes goals via LLM
            → Generates Recipe with tasks + dependencies + verification criteria
2. EXECUTE → RecipeExecutor runs tasks (shell/LLM/API modes)
            → Retry logic with exponential backoff
            → Rollback on failure
3. VERIFY  → RecipeVerifier validates results
            → Exit codes, file checks, LLM quality assessment
            → Generate verification reports
```

**Core Components:**
- `planner.py` - LLM-powered task decomposition
- `executor.py` - Multi-mode execution engine
- `verifier.py` - Result validation layer
- `orchestrator.py` - Workflow coordination

---

## 第六篇 虛實 (Xu Shi) - OPEN CORE STRATEGY

> "Tỵ thực nhi kích hư" - Public strengths, hide weaknesses

### What's Open vs Private

```
PUBLIC (Open Source):
├── src/core/               # Plan-Execute-Verify engine
├── _bmad/                  # 169 workflows
├── CLAUDE.md               # Agent rules
└── packages/               # Hub SDK structure
    ├── core/               # Foundation (vibe, agents, shared)
    ├── integrations/       # Connectors (bridge, CRM)
    ├── tooling/            # Dev tools (analytics, dev)
    ├── business/           # Revenue logic (money, ops, marketing)
    └── ui/                 # Components (vibe-ui, i18n)

PRIVATE (.gitignore):
├── plans/internal/
├── dna/pricing/
└── apps/dashboard-internal/
```

**SDK Dependency Flow:**
```
ui/ ──┐
      ├──> integrations/ ──> core/ (foundation)
business/ ┘                    └── vibe, vibe-agents, shared
```

---

## 第七篇 軍爭 (Jun Zheng) - MANEUVERING

> "Binh quý thắng, bất quý cửu" - Speed is the essence

### Two-Call Mandate (CC CLI)

```
Bước 1: Gửi command (KHÔNG có \n ở cuối)
Bước 2: Gửi Enter riêng (\n)
```

### Workflow Chuẩn

```
1. /plan:hard "task"  ← Strategy
2. /cook <plan>       ← Execute
3. npm run build      ← Verify
4. Browser check      ← Visual confirm
```

---

## 第五篇 兵勢 (Bing Shi) - AGENT TEAMS

> "Thế như hoãn huyệt" - Parallel power execution

### Configuration

```bash
# Setting: ~/.claude/settings.json
"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
```

### Team Workflow

```
1. Create plan: /plan:hard "task"
2. Execute: "Gọi team thực hiện plan này"
3. CC CLI auto-spawns: FE + BE + Debug + Review
4. Agents sync via Shared Task List
```

### Mekong CLI Integration

**Orchestrator delegates to Agent Teams:**

```bash
# Mekong triggers plan
mekong run "build authentication system"

# Internally delegates to CC CLI with Agent Teams:
├── Planner Agent    → Plan generation
├── Developer Agent  → Implementation (parallel FE/BE)
├── Tester Agent     → Verification (unit/integration)
└── Reviewer Agent   → Code quality + security

# RecipeOrchestrator coordinates workflow
# Agents share task list via ~/.claude/tasks/
```

**Usage Pattern:**
```bash
# High-level goal → automatic planning
mekong run "implement user authentication"

# Manual recipe execution
mekong cook recipes/deploy-api.md

# Both use Plan→Execute→Verify engine
```

---

## 第九篇 九變 (Jiu Bian) - BMAD INTEGRATION

> "Tướng thông cửu biến" - Adapt with 169 workflows

### BMAD Location: `_bmad/`

| Component | Count                                       |
| --------- | ------------------------------------------- |
| Workflows | 169                                         |
| Agents    | 9 (PM, Architect, Dev, QA, Analyst, SM, UX) |
| Teams     | 2                                           |

### Key Workflows

| Command                | Purpose           |
| ---------------------- | ----------------- |
| `/product-brief`       | Define scope      |
| `/create-prd`          | Full requirements |
| `/create-architecture` | System design     |
| `/dev-story`           | Implement with QA |

**Combo:** BMAD planning → Agent Teams parallel execution

---

## 第十篇 地形 (Di Xing) - BINH PHAP QUALITY GATES

> "知彼知己, 勝乃不殆" - Quality enforced at every step

### Verification Criteria (Every Recipe Execution)

| Gate | Criterion | Verification Method |
|------|-----------|---------------------|
| 始計 (Tech Debt) | 0 TODOs/FIXMEs | `grep -r "TODO\|FIXME" src` |
| 作戰 (Type Safety) | 0 `any` types | `grep -r ": any" src` |
| 謀攻 (Performance) | Build < 10s | `time npm run build` |
| 軍形 (Security) | 0 high/critical vulns | `npm audit --audit-level=high` |
| 兵勢 (UX) | Loading states on async | Manual review |
| 虛實 (Documentation) | Updated on completion | Git diff check |

**Enforced by RecipeVerifier:**
```python
# verifier.py automatically checks gates
verification = verifier.verify(result, criteria)
if not verification.passed:
    orchestrator.rollback(step)
```

**Override (Development Only):**
```bash
mekong run --skip-gates "deploy-api"  # Emergency bypass
```

---

## 第十一篇 九地 (Jiu Di) - CC CLI OPERATIONS

> "Tứ địa tắc hợp" - On intersecting ground, join with allies

### CC CLI Proxy Rule

- CC CLI dùng Antigravity Proxy, KHÔNG phải API hãng
- Khi context compact 0% → gửi Enter ngay để kick tiếp
- `RESOURCE_EXHAUSTED` (429/400) → `/proxy:reset`
- CLI bị treo → `./scripts/proxy-recovery.sh`

### Verification Rule

**KHÔNG TIN BÁO CÁO - PHẢI XÁC THỰC!**

- Khi agent báo cáo "hoàn thành" → verify bằng browser/tools
- Kiểm tra production site trực tiếp
- Xác thực visual/functional trước khi ship

---

## 第十二篇 火攻 (Huo Gong) - COMMIT CONVENTION

> "Phát hỏa hữu thời" - Execute at the right time

### Git Standards

```
feat: [module] - Add new feature
fix: [module] - Fix bug
refactor: [module] - Code improvement
docs: Update documentation
```

---

## 第十三篇 用間 (Yong Jian) - INTELLIGENCE SYNC

> "Minh quân hiền tướng" - Knowledge prevails

### Knowledge Sources

| Source    | Path                               |
| --------- | ---------------------------------- |
| Brain     | `~/.gemini/antigravity/brain/`     |
| Knowledge | `~/.gemini/antigravity/knowledge/` |
| BMAD      | `_bmad/bmm/workflows/`             |
| Skills    | `.claude/skills/`                  |

---

_Genesis: 2026-02-06 | ClaudeKit DNA v2.9.1+ | Agent Teams + BMAD + Binh Pháp_

# ZenOS Architecture — Mekong CLI

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  L6: CIVILIZATION                                               │
│  Commons, protocols, ecosystem. ZenOS Manifesto.                │
│  mekong/constitution/ZENOS.md                                    │
├─────────────────────────────────────────────────────────────────┤
│  L5: FOUNDER (HUMAN)                                            │
│  AI/founder.md — The First Guardian                             │
│  - Owns the mission (ZenOS Art 8)                               │
│  - Final decision on critical path                              │
│  - VC/Investor: studio + portfolio management                   │
│  - AI CEO reports to Founder, not replaces                      │
│  - mekong studio init (VC level, portfolio view)                 │
├─────────────────────────────────────────────────────────────────┤
│  L4: STUDIO                                                     │
│  Venture builder, deal flow, multi-particle management.         │
│  mekong studio init / .claude/commands/studio-*.md              │
├─────────────────────────────────────────────────────────────────┤
│  L3: ECONOMIC PARTICLE (project)                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ZENOS.md           — Constitution, mission                │  │
│  │  .claude/           — CK init harness (hooks, settings)    │  │
│  │  .github/workflows/ — 2-guard deploy pipeline              │  │
│  │  AI/                — C-Level agents (CEO, CTO, CMO, ...)  │  │
│  │  mekong audit       — compliance check                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│  mekong init <project> creates this layer                       │
├─────────────────────────────────────────────────────────────────┤
│  L2: KERNEL (CK Init Harness)                                   │
│  mekong/hooks/         — Canonical hooks                        │
│  mekong/bootstrap/     — Init, health, self-heal                │
│  mekong/init/          — Project generator                      │
│  mekong/audit/         — Compliance auditor                     │
│  mekong/constitution/  — ZenOS rules                            │
├─────────────────────────────────────────────────────────────────┤
│  L1: INFRASTRUCTURE                                             │
│  Claude Code CLI      — 3 profiles (cc/deepseek/claude)        │
│  ~/.zshrc             — Shell aliases                           │
│  Cloudflare Workers   — Deploy target                           │
│  GitHub               — Repo + CI/CD                            │
└─────────────────────────────────────────────────────────────────┘
```

## C-Level Agents

| Agent | Global (`~/.claude/agents/`) | Particle (`project/AI/`) |
|-------|------------------------------|--------------------------|
| CEO | — | Strategy, mission, OKRs, investor |
| CTO | `ck:cto` / `code-reviewer` | Tech stack, architecture, code quality |
| CMO | `ck:cmo` / `copywriter` | Marketing, brand, content, SEO |
| CFO | — | Finance, pricing, burn rate, billing |
| CSO | `ck:cso` | Sales, outreach, partnerships |
| CHRO | — | Hiring, culture, people ops |
| COO | `ck:coo` | Operations, automation, workflows |

**Rule:** Global agents = engineering/tooling. Particle agents = mission-specific.
Particle agents override global when both exist.

## Org Structure (39 Agents)

```
FOUNDER (HUMAN) — The First Guardian
│
├── CEO ─── 6 Dept Heads
├── CTO ─── 6 Dept Heads
│   ├── engineering-fullstack
│   ├── engineering-frontend
│   ├── engineering-backend
│   ├── engineering-qa
│   ├── engineering-devops
│   └── engineering-security
├── CMO ─── 5 Dept Heads
│   ├── marketing-content, marketing-design, marketing-seo
│   ├── marketing-social, marketing-pr
├── CFO ─── 5 Dept Heads
│   ├── finance-accounting, finance-billing, finance-treasury
│   ├── finance-compliance, finance-audit
├── CSO ─── 5 Dept Heads
│   ├── sales-outreach, sales-partnerships, sales-customer-success
│   ├── sales-proposals, sales-contracts
├── COO ─── 5 Dept Heads
│   ├── ops-workflow, ops-automation, ops-legal
│   ├── ops-admin, ops-infrastructure
└── CHRO ─── 5 Dept Heads
    ├── people-culture, people-recruiting, people-learning
    ├── people-wellness, people-engagement
```

Total: 7 C-Level + 31 Department Heads = 38 AI agents, AI-operated.

## CK Init = DNA (Skill & Tool Standard)

CK init is the canonical source for ALL skills, commands, hooks, and settings.
Mekong extends, never duplicates.

| Layer | Source | Count | Rule |
|-------|--------|-------|------|
| Skills | CK init global (`~/.claude/skills/`) | 140 | Mekong doesn't create skills |
| Commands | CK init global (`~/.claude/commands/`) | 120 | Mekong adds `mekong-` prefix |
| Agents | Global + Particle | 39 | Particle > Global when both exist |
| MCP | Global config | 2+ | Shared, no conflict |
| Hooks | Mekong canonical (`mekong/hooks/`) | 17 | Global symlinks to mekong |

**Conflict Resolution (mekong audit):**
- Detects skills/commands existing in both CK init and mekong
- Prefers CK init (DNA) when names match
- Flags mekong-specific items for `mekong-` rename
- Auto-fix when CK init updates

**Update Flow:**
```
npx ck init -g  → CK init updates skills/commands
                → mekong audit --fix detects conflicts
                → resolves automatically
                → shell-init.sh --quiet runs on terminal start
```

## Cross-Department Workflows

Agents don't call each other directly. **COO routes via workflows.**

```
CEO → COO → tìm workflow → dispatch subagent → step 1 → step 2 → done
```

| Workflow | Departments | Trigger |
|----------|-------------|---------|
| `feature-launch` | CEO → CTO → CMO → CSO → COO | New feature |
| `campaign-publish` | CEO → CMO → CTO → CSO → COO | Marketing campaign |
| `feature-request` | CSO → CTO → CMO → COO | Customer request |
| `bug-critical` | CSO → CTO → COO | Critical bug report |
| `monthly-report` | COO → ALL | End of month |

All workflows at `workflows/*.md` — spawned by COO, executed by subagents.

## Init Flow

```
mekong init my-startup
  → Layer 3: Particle skeleton (ZENOS.md + AI/7 C-Level + AI/org/31 Dept Heads + .github/)
  → Layer 2: CK init harness (.claude/ + hooks + settings)
  → Layer 1: git init
  → Ready for: mekong audit . --fix
```

## Audit Flow

```
mekong audit .
  → Check L2: CK init hooks present
  → Check L3: Constitution, 2-guard, AI agents
  → Check L1: Git remote, branch protection
  → mekong audit . --fix auto-repairs
```

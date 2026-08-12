# Greenfield Quickstart

Build your first autonomous company from scratch with Mekong.

**Time estimate:** 20-30 minutes to first running mission

---

## What is a Greenfield Project?

A **greenfield project** is a brand new business or product built from scratch using Mekong's autonomous agents. Unlike brownfield (integrating Mekong into existing code), greenfield means:

- No existing codebase to migrate
- No legacy systems to maintain
- Full autonomy to design your business architecture
- Start with a clean slate and let AI agents build everything

This guide walks you through creating a **complete autonomous company** — from idea to deployed application — using Mekong's 10 business layers.

---

## Prerequisites

### System Requirements

| Tool | Version | Why |
|------|---------|-----|
| macOS 14+ (Sonoma) | or Ubuntu 22.04+ | Local development |
| Git | 2.40+ | Version control |
| Node.js | 20+ (LTS) | Frontend build |
| Python | 3.11+ | Backend runtime |
| Docker | optional | Containerized builds |
| Ollama | optional | Free local LLM |

### LLM Provider (Pick One)

| Provider | Cost | Setup |
|----------|------|-------|
| **OpenRouter** (recommended) | $5 free credit, then pay-per-use | Fastest setup, 200+ models |
| **Anthropic** | Claude API key | Best reasoning |
| **OpenAI** | GPT-4o | Familiar interface |
| **Ollama** (free) | Local only | No API costs, requires RAM |

---

## Phase 1: Install Mekong CLI

### 1.1 Clone and Setup

```bash
# Clone the repository
git clone --depth 1 https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli

# Initialize shell integration (add to ~/.zshrc for persistence)
source scripts/shell-init.sh

# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Node packages (for SDK)
pnpm install
```

### 1.2 Configure Your LLM

Choose your provider and set three environment variables:

```bash
# Option A: OpenRouter (easiest - supports 200+ models)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-your-key-here
export LLM_MODEL=anthropic/claude-sonnet-4

# Option B: Anthropic Direct
export LLM_BASE_URL=https://api.anthropic.com/v1
export LLM_API_KEY=sk-ant-your-key-here
export LLM_MODEL=claude-sonnet-4-20250514

# Option C: OpenAI
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-your-key-here
export LLM_MODEL=gpt-4o

# Option D: Ollama (free, local)
ollama pull qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=qwen2.5-coder
```

**Pro tip:** Add these to `~/.zshrc` or `~/.bashrc` for persistence.

### 1.3 Verify Installation

```bash
# Check Mekong is available
mekong status

# Expected output:
# Mekong CLI v6.0
# Provider: OpenRouter (Claude Sonnet 4)
# Commands loaded: 443
# Credits remaining: N/A (not configured)
```

---

## Phase 2: Initialize Your Company

Every autonomous company needs a **company manifest** that defines your identity, constitution, and operating parameters.

### 2.1 Run the Company Wizard

```bash
mekong company/init
```

This interactive wizard creates `~/.mekong/company.json`:

```json
{
  "company_name": "YourCo AI",
  "mission": "Build tools for solo founders",
  "founder": {
    "name": "Your Name",
    "email": "you@example.com",
    "timezone": "Asia/Ho_Chi_Minh"
  },
  "constitution": {
    "principles": [
      "Human dignity first",
      "Transparency in all decisions",
      "Freedom to exit"
    ],
    "budget_limits": {
      "monthly_spend_cap": 1000,
      "daily_credit_alert": 50
    }
  },
  "economic_particle": {
    "type": "micro_enterprise",
    "allocation_rules": {
      "reserve": 0.30,
      "tax": 0.25,
      "reinvest": 0.30,
      "draw": 0.15
    }
  }
}
```

### 2.2 Configure Billing (Optional)

If you have a Polar.sh subscription:

```bash
export MEKONG_POLAR_WEBHOOK_SECRET=your-webhook-secret
mekong billing/activate --plan growth
```

Without billing, commands run in **exploration mode** with no credit limits.

---

## Phase 3: Your First Mission

### 3.1 Understanding the 10 Business Layers

Mekong organizes all capabilities into 10 layers:

| Layer | Prefix | Commands | Use Case |
|-------|--------|----------|----------|
| **Founder** | `/founder:*` | 52 | Strategy, vision, governance |
| **Business** | `/business:*` | 71 | Sales, marketing, finance |
| **Product** | `/product:*` | 31 | Planning, roadmaps, sprints |
| **Engineering** | `/eng:*` or `/cook`, `/code` | 66 | Build and ship |
| **Ops** | `/ops:*` | 41 | Monitor, audit, secure |
| **Studio** | `/studio:*` | 23 | VC portfolio operations |
| **CTO** | `/cto:*` | Architecture reviews | Tech leadership |
| **PM** | `/pm:*` | Tactical planning | Product management |
| **Dev** | `/dev:*` | Developer workflows | Feature work |
| **Worker** | `/worker:*` | Atomic tasks | Background jobs |

**Most used layers for greenfield:**
- **Founder** — Define strategy and goals
- **Product** — Plan features and timelines
- **Engineering** — Build the product
- **Ops** — Keep it running

### 3.2 The PEV Loop

Every Mekong command follows **Plan-Execute-Verify**:

```
┌─────────────┐
│   Your Goal │  "Build a SaaS landing page"
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│      PLANNER        │  Breaks goal into 5 steps:
│   (LLM reasoning)   │  1. Design wireframes
│                     │  2. Create HTML/CSS
│                     │  3. Add contact form
│                     │  4. Deploy to Cloudflare
│                     │  5. Test responsiveness
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│     EXECUTOR        │  Runs each step:
│   (Agent actions)   │  - DesignAgent → Figma spec
│                     │  - CodeAgent → HTML files
│                     │  - ShellAgent → wrangler deploy
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│     VERIFIER        │  Quality gates:
│   (Check results)   │  - Build succeeds ✓
│                     │  - Tests pass ✓
│                     │  - Lighthouse score >90 ✓
│                     │  - Deployment health check ✓
└─────────────────────┘
```

### 3.3 Run Your First Cook Command

The `cook` command is your primary entry point for building:

```bash
# Simple version - just describe what you want
mekong cook "Build a landing page for my SaaS product"

# With more detail
mekong cook "Create a Python FastAPI backend with:
- PostgreSQL database
- JWT authentication
- User registration/login endpoints
- API rate limiting
- Deploy to Cloudflare Workers"
```

**What happens:**
1. Mekong planner decomposes your goal
2. Engineers (subagents) execute in parallel where possible
3. Verifier checks everything works
4. Results committed to git

### 3.4 Monitor Progress

```bash
# See running missions
mekong status

# Follow logs in real-time
mekong logs --follow

# Check agent output
mekong agent:tail --agent code-writer
```

---

## Phase 4: Common Greenfield Workflows

### 4.1 MVP in One Day

```bash
# Morning: Strategy
mekong founder/validate "AI-powered note-taking app for students"
mekong product/roadmap --timeline 3mo --milestones 5

# Afternoon: Build Core
mekong cook "Create MVP with:
- Next.js frontend (Tailwind CSS)
- Stripe payments
- Supabase auth + database
- Deploy to Vercel"

# Evening: Polish
mekong review/ux "Improve mobile checkout flow"
mekong test/e2e --coverage 80
```

### 4.2 Full Stack Application

```bash
# 1. Architecture decision record
mekong cto/architect "Design system for real-time collaboration app"

# 2. Database schema
mekong cook "Design and implement PostgreSQL schema for:
- users, teams, documents
- real-time editing (CRDTs)
- version history"

# 3. Backend API
mekong code/api "Build REST API with:
- FastAPI
- SQLAlchemy ORM
- WebSocket for real-time
- OpenAPI docs"

# 4. Frontend
mekong code/frontend "React app with:
- TypeScript
- TanStack Query
- Zustand state
- Socket.io client"

# 5. Testing
mekong test/unit --coverage 85
mekong test/e2e --cypress

# 6. Deploy
mekong deploy --platform vercel --env production
```

### 4.3 Business Operations Setup

```bash
# Finance
mekong finance/setup --currency usd --tax us
mekong finance/forecast --months 12

# Sales
mekong marketing/landing --product "Your Product"
mekong sales/crm-setup --pipeline stages

# Legal
mekong legal/terms --jurisdiction us --company llc
mekong legal/privacy --gdpr --ccpa
```

---

## Phase 5: Understanding Project Structure

Mekong creates this structure for greenfield projects:

```
your-project/
├── .mekong/                 # Mekong state (local only)
│   ├── company.json        # Your company manifest
│   ├── tasks/              # Active and queued tasks
│   ├── usage_events.jsonl  # Audit log
│   └── constitution.json   # Constitutional AI rules
│
├── .claude/                # Command definitions (committed)
│   ├── commands/          # 443+ command specs
│   ├── skills/            # 197 agent skills
│   └── agents/            # Agent configurations
│
├── src/                    # Generated source code
│   ├── api/               # Backend API
│   ├── web/               # Frontend
│   ├── db/                # Database migrations
│   └── tests/             # Test suite
│
├── factory/                # Machine contracts
│   └── contracts/
│       └── commands/      # JSON schemas for all commands
│
├── packages/               # SDK packages
│   ├── mekong-cli-core/   # CLI core (TS)
│   └── openclaw-engine/   # Orchestration SDK
│
├── docker-compose.yml      # Local dev environment
├── docker-compose.prod.yml # Production
├── .env.example            # Environment template
├── Makefile               # Common tasks
├── README.md              # Project docs
└── AGENTS.md              # Agent definitions
```

**Key directories to know:**
- `.claude/commands/` — Command definitions (markdown specs)
- `.claude/skills/` — Agent capabilities (SKILL.md files)
- `factory/contracts/` — JSON machine-readable contracts
- `src/` — Your actual codebase
- `.mekong/` — Local state (gitignored, per-machine)

---

## Phase 6: Multi-Agent Orchestration

### 6.1 Parallel Execution

Mekong automatically parallelizes independent work:

```bash
# This spawns 8 agents working concurrently
mekong cook "Launch a startup website with:
- Landing page
- Blog with 5 articles
- Contact form with email notifications
- Analytics dashboard
- SEO optimization"
```

Agents assigned:
- DesignAgent → Landing page designs
- ContentWriter → Blog articles  
- FrontendDev → React components
- BackendDev → API + email service
- DevOps → Vercel deployment
- SEOExpert → Meta tags, sitemap
- QAEngineer → Testing
- DocumentationWriter → User guide

### 6.2 Explicit Delegation

For complex projects, use `--parallel` with specific agent counts:

```bash
mekong cook "Build e-commerce platform" \
  --agents.frontend 2 \
  --agents.backend 2 \
  --agents.devops 1
```

### 6.3 Approval Gates

High-risk actions require explicit approval:

```bash
# Database migrations require confirmation
mekong db:migrate --env production
# Output: Apply migration? (Y/n)

# Deployments to production
mekong deploy --platform cloudflare --env production
# Output: Deploy to production? This will make changes visible to users.
```

Configure approval requirements in `.claude/settings.json`:

```json
{
  "permissions": {
    "deny": ["git push --force", "db:drop", "billing:charge"],
    "ask": ["deploy:prod", "db:migrate", "ssl:renew"]
  }
}
```

---

## Phase 7: The Command Catalog

### 7.1 Explore Available Commands

```bash
# All commands (443+)
mekong help

# Filter by layer
mekong help --layer engineering
mekong help --layer founder

# Search by keyword
mekong search "deploy"
mekong search "auth"
mekong search "stripe"

# Command details
mekong help cook
mekong help deploy
```

### 7.2 Command Structure

Every command follows this pattern:

```bash
mekong <namespace>:<action> [arguments] [options]
```

Examples:
- `mekong cook "description"` — Build something
- `mekong code:refactor --file auth.py --suggestions 3` — Refactor code
- `mekong deploy --platform vercel --branch main` — Deploy
- `mekong test:unit --coverage 85` — Run unit tests

### 7.3 Most Common Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `cook` | Build from description | `mekong cook "API with auth"` |
| `code` | Code generation | `mekong code component --name Button` |
| `fix` | Debug and repair | `mekong fix "TypeError in login"` |
| `test` | Run tests | `mekong test --watch` |
| `deploy` | Deploy application | `mekong deploy --vercel` |
| `review` | Code review | `mekong review --security` |
| `plan` | Create implementation plan | `mekong plan "feature"` |
| `brainstorm` | Ideation | `mekong brainstorm "product ideas"` |
| `audit` | System audit | `mekong audit --security` |
| `status` | System status | `mekong status` |

---

## Phase 8: SDK Integration (For Developers)

If you're building tools that integrate with Mekong:

### 8.1 Install the SDK

```bash
npm install @mekongcli/openclaw-engine
# or
pip install mekong-openclaw
```

### 8.2 TypeScript Example

```typescript
import { OpenClawEngine } from '@mekongcli/openclaw-engine';

const engine = new OpenClawEngine({
  provider: 'openrouter',
  apiKey: process.env.LLM_API_KEY,
  model: 'anthropic/claude-sonnet-4'
});

// Classify task
const complexity = await engine.classifyComplexity(
  "Build a payment processing microservice"
);
// => "complex"

// Submit mission
const result = await engine.submitMission({
  goal: "Create user authentication with OAuth",
  layer: "engineering",
  commands: ["code", "test", "deploy"],
  constraints: {
    budget: 500,
    deadline: "2026-06-30"
  }
});

console.log(result);
// => { status: "completed", artifacts: [...], cost: 47 }
```

### 8.3 Python Example

```python
from openclaw_engine import OpenClawEngine

engine = OpenClawEngine(
    provider="anthropic",
    api_key=os.environ["ANTHROPIC_API_KEY"]
)

# Plan first
plan = engine.plan("Build blog with CMS")
# => { steps: [...], estimate: "2 hours", agents: 4 }

# Execute
result = engine.execute(plan)
# => { success: true, output: {...} }

# Verify
passed = engine.verify(result)
# => true
```

---

## Phase 9: Workflow Patterns

### 9.1 Iterative Development

```bash
# Week 1: MVP
mekong cook "Build core feature set"

# Week 2: Refine based on feedback
mekong review/feedback --source users
mekong cook "Address top 5 user feedback items"

# Week 3: Scale
mekong ops/scale --autoscaling true
mekong cook "Optimize database queries"
```

### 9.2 A/B Testing Setup

```bash
mekong cook "Implement A/B testing framework:
- Feature flags
- Conversion tracking
- Statistical significance calculator
- Dashboard for results"
```

### 9.3 Compliance & Security

```bash
# Security audit
mekong audit/security --scan all --report pdf

# GDPR compliance
mekong legal/gdpr --audit --remediate

# SOC 2 prep
mekong audit/soc2 --type ii --controls all
```

---

## Phase 10: Next Steps

### Continue Learning

```bash
# Read the full documentation
open docs/command-fabric.md
open docs/constitutional-ai.md
open docs/economic-particles.md

# Run example missions
mekong brainstorm --examples
mekong demo --all
```

### Join the Community

- **GitHub:** github.com/longtho638-jpg/mekong-cli
- **Discord:** discord.gg/mekong (community support)
- **Docs:** mekongmind.com/guides

### Production Readiness

Before going live:

- [ ] Complete security audit (`mekong audit/security --full`)
- [ ] Set up monitoring (`mekong observability/setup`)
- [ ] Configure backups (`mekong backup/configure --daily`)
- [ ] Load test (`mekong test/load --users 1000`)
- [ ] Legal review (`mekong legal/compliance-check`)
- [ ] Billing activation (`mekong billing/activate`)

---

## Troubleshooting

### "Command not found"

```bash
# Reinitialize shell
source scripts/shell-init.sh

# Or restart terminal
```

### "No LLM API key"

```bash
# Check environment variables
echo $LLM_API_KEY
echo $LLM_BASE_URL

# Re-export if needed
export LLM_API_KEY=your-key
```

### "Agent timeout"

```bash
# Increase timeout
mekong cook "goal" --timeout 600

# Or break into smaller tasks
mekong cook "step 1 of 5"
```

### "Permission denied"

```bash
# Check .claude/settings.json
cat .claude/settings.json | jq .permissions

# Add permission or run with --override
mekong cook "goal" --override
```

---

## Quick Reference Card

```bash
# Startup
source scripts/shell-init.sh
mekong status

# Company setup
mekong company/init
mekong founder/validate "your idea"

# Build
mekong cook "your goal"
mekong code component --name Button
mekong fix "error message"

# Test
mekong test --unit
mekong test --e2e
mekong review --security

# Deploy
mekong deploy --platform vercel
mekong ops/monitor --healthchecks

# Monitor
mekong logs --follow
mekong status --detailed
mekong audit/security

# SDK
npm install @mekongcli/openclaw-engine
```

---

## What's Next?

1. **Try the tutorials** — `docs/tutorials/` (coming soon)
2. **Join the community** — Share your greenfield journey
3. **Read the architecture** — `docs/system-architecture.md`
4. **Explore the command fabric** — `docs/command-fabric.md`
5. **Configure constitutional AI** — `docs/constitutional-ai.md`

**Remember:** Mekong is your autonomous workforce. Start small, verify each step, and scale what works.

---

**Need help?** Run `mekong help` or visit [mekongmind.com/guides](https://mekongmind.com/guides)

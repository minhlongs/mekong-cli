# Mekong CLI — Command Catalog

**319 commands • 542 skills • 5 business layers**

> Quick reference organized by layer. Use `mekong help [layer]` for full details.

---

## Table of Contents

- [Founder Layer (46 commands)](#founder-layer)
- [Business Layer (32 commands)](#business-layer)
- [Product Layer (17 commands)](#product-layer)
- [Engineering Layer (47 commands)](#engineering-layer)
- [Ops Layer (27 commands)](#ops-layer)
- [Cross-layer Commands (150+ commands)](#cross-layer)
- [Usage Examples](#usage-examples)

---

## Founder Layer

**46 commands** — Strategy, fundraising, market analysis, financial planning.

| Command | MCU | Purpose |
|---------|-----|---------|
| `/annual` | 2 | Generate annual business plan |
| `/okr` | 2 | Define quarterly OKRs |
| `/swot` | 1 | SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) |
| `/fundraise` | 5 | Prepare Series A/B fundraising kit |
| `/pitch` | 3 | Create investor pitch deck |
| `/vc-map` | 2 | Identify target VCs by thesis |
| `/cap-table` | 1 | Model cap table and dilution |
| `/financial-forecast` | 3 | 24-month financial projections |
| `/unit-economics` | 2 | Calculate CAC, LTV, payback period |
| `/tam` | 1 | Total addressable market analysis |
| `/moat-audit` | 2 | Evaluate competitive moat |
| `/ipo-readiness` | 4 | S-1 filing preparation checklist |
| `/board-deck` | 3 | Quarterly board presentation |
| `/data-room` | 2 | Investor data room structure |
| `/vc-update` | 1 | Monthly investor update email |
| ... | ... | 31 more founder commands |

**Example:**
```bash
mekong founder:raise "Series A for AI platform"
# → Reports: /reports/raise-ready-kit/
# Executes in parallel: /unit-economics + /tam + /moat-audit
```

---

## Business Layer

**32 commands** — Revenue, operations, marketing, HR, finance.

| Command | MCU | Purpose |
|---------|-----|---------|
| `/sales` | 3 | Lead generation + pipeline analysis |
| `/quote` | 1 | Generate pricing quotes (13-chapter framework) |
| `/proposal` | 2 | Create client proposals |
| `/win-rate` | 1 | Analyze deal win/loss reasons |
| `/churn-analysis` | 2 | Customer churn root cause |
| `/marketing` | 3 | Marketing campaign planning |
| `/content` | 2 | Blog post + social media writing |
| `/seo` | 2 | SEO audit + optimization strategy |
| `/brand` | 2 | Brand positioning + messaging |
| `/pricing` | 2 | Dynamic pricing optimization |
| `/market-research` | 3 | Competitive intelligence |
| `/finance` | 2 | Monthly P&L analysis |
| `/cash-forecast` | 2 | 12-month cash flow projection |
| `/budget` | 1 | Annual budget planning |
| `/hr-hiring` | 2 | Job description + interview guide |
| `/hr-review` | 1 | Performance review template |
| `/kpi-dashboard` | 1 | Business KPI tracking |
| ... | ... | 15 more business commands |

**Example:**
```bash
mekong business:sales "Identify high-value tech companies in APAC"
# → Reports: /reports/leads-20260321.csv
# Outreach templates ready for personalization
```

---

## Product Layer

**17 commands** — Product planning, roadmap, feature prioritization, sprint management.

| Command | MCU | Purpose |
|---------|-----|---------|
| `/plan` | 2 | Product roadmap (12-month) |
| `/sprint` | 1 | Sprint planning + backlog refinement |
| `/roadmap` | 2 | Feature prioritization matrix (RICE) |
| `/brainstorm` | 1 | Ideas generation + voting |
| `/scope` | 2 | Feature scope + complexity estimation |
| `/requirements` | 2 | PRD (Product Requirements Document) |
| `/user-research` | 3 | User interview synthesis + insights |
| `/analytics-review` | 1 | Weekly analytics deep-dive |
| `/competitor-analysis` | 2 | Competitive feature matrix |
| `/launch-plan` | 2 | Go-to-market strategy |
| `/beta-feedback` | 1 | Beta user feedback summary |
| `/retention-analysis` | 2 | User retention cohort analysis |
| `/ab-test-plan` | 1 | A/B test design + hypothesis |
| `/accessibility-audit` | 1 | WCAG 2.1 accessibility review |
| `/mobile-strategy` | 2 | Mobile-first product strategy |
| `/api-design` | 1 | REST API design review |
| `/release-notes` | 1 | Generate release notes + changelog |

**Example:**
```bash
mekong product:plan "AI code assistant with multi-language support"
# → Reports: /reports/roadmap-ai-assistant.md
# Estimates: 3-month implementation, priority features identified
```

---

## Engineering Layer

**47 commands** — Build, test, deploy, code review, debugging.

| Command | MCU | Purpose |
|---------|-----|---------|
| `/cook` | 1 | Build feature with AI (full-stack) |
| `/fix` | 1 | Debug and fix production issues |
| `/code` | 1 | Generate code snippet |
| `/test` | 1 | Write unit + integration tests |
| `/deploy` | 2 | Deploy to production (CD pipeline) |
| `/review` | 1 | Automated code review |
| `/refactor` | 2 | Code refactoring + optimization |
| `/security-audit` | 2 | Security vulnerability scan |
| `/perf-profile` | 1 | Performance profiling + optimization |
| `/load-test` | 2 | Load testing + stress testing |
| `/e2e-test` | 2 | End-to-end test suite |
| `/debug-trace` | 1 | Debug distributed traces (APM) |
| `/db-migrate` | 2 | Database schema migration |
| `/api-test` | 1 | REST API testing + documentation |
| `/docker-build` | 1 | Build Docker image |
| `/k8s-deploy` | 2 | Kubernetes deployment manifest |
| `/ci-setup` | 2 | GitHub Actions CI/CD pipeline |
| `/lighthouse` | 1 | Web performance audit |
| `/accessibility-test` | 1 | Automated accessibility testing |
| `/sql-optimize` | 1 | SQL query optimization |
| `/cache-strategy` | 1 | Caching optimization |
| `/observability` | 2 | Logging + monitoring setup |
| `/incident-response` | 2 | Post-mortem + RCA (root cause analysis) |
| ... | ... | 24 more engineering commands |

**Example:**
```bash
mekong engineering:cook "Build authentication module with OAuth2"
# → Step 1: Plan (architecture decision)
# → Step 2: Code (implementation)
# → Step 3: Test (unit + integration)
# → Step 4: Review (security check)
# Output: /src/auth/ fully implemented
```

---

## Ops Layer

**27 commands** — Monitoring, security, health checks, infrastructure audit.

| Command | MCU | Purpose |
|---------|-----|---------|
| `/audit` | 1 | Infrastructure security audit |
| `/health` | 0 | System health check |
| `/status` | 0 | Service status dashboard |
| `/security` | 2 | Security posture assessment (OWASP Top 10) |
| `/compliance` | 2 | SOC 2, GDPR, HIPAA compliance check |
| `/soc2-audit` | 3 | SOC 2 Type II audit preparation |
| `/incident-log` | 0 | View incidents (last 30 days) |
| `/on-call` | 1 | On-call schedule + rotation |
| `/alert-rules` | 1 | Alert threshold optimization |
| `/log-analysis` | 1 | Log anomaly detection |
| `/cost-optimization` | 2 | Cloud cost reduction opportunities |
| `/backup-test` | 1 | Disaster recovery drill |
| `/dependency-audit` | 1 | Dependency vulnerability scan (npm audit) |
| `/ssl-cert-check` | 0 | SSL/TLS certificate validation |
| `/dns-audit` | 0 | DNS records health check |
| `/rate-limit-audit` | 1 | Rate limit effectiveness review |
| `/ddos-protection` | 2 | DDoS protection strategy |
| `/data-retention` | 1 | Data retention policy audit |
| `/secret-rotation` | 1 | API key/secret rotation automation |
| `/uptime-report` | 1 | Monthly uptime SLA report |
| `/capacity-planning` | 2 | 6-month capacity forecast |
| `/upgrade-plan` | 2 | Software upgrade sequencing |
| `/maintenance-window` | 1 | Schedule maintenance window |
| `/runbook` | 1 | Generate runbook (incident response) |
| `/chaos-engineering` | 3 | Chaos experiment design + execution |
| `/disaster-recovery` | 3 | DR plan + recovery testing |
| ... | ... | 1 more ops command |

**Example:**
```bash
mekong ops:audit
# → Reports: /reports/audit-20260321.json
# Scores: Database (9/10), Server (8/10), Security (8/10)
# Action items: 5 high-priority fixes identified
```

---

## Cross-Layer Commands

**150+ commands** — Available across all layers via `/` notation.

### Super Commands (Meta-orchestration)

| Command | MCU | Purpose |
|---------|-----|---------|
| `/plan` | 2 | Master project planning |
| `/help` | 0 | View all commands + usage |
| `/version` | 0 | CLI version + status |
| `/status` | 0 | LLM + infrastructure status |
| `/configure` | 1 | Configure CLI settings |
| `/init` | 0 | Initialize new project |
| `/setup` | 1 | Setup local environment |

### Utility Commands

| Command | MCU | Purpose |
|---------|-----|---------|
| `/shell` | 0 | Interactive shell |
| `/batch` | 2 | Batch command execution |
| `/parallel` | 3 | Run commands in parallel (DAG) |
| `/queue` | 1 | View task queue |
| `/cancel` | 0 | Cancel running task |
| `/resume` | 1 | Resume failed task |
| `/export` | 1 | Export results (CSV, JSON) |
| `/import` | 1 | Import data (CSV, JSON) |

---

## Usage Examples

### Quick Start

```bash
# Interactive mode
mekong

# Single command
mekong cook "Build a REST API with authentication"

# Force model
mekong-opus cook "Complex feature"
mekong-sonnet plan "Quick feature plan"
mekong-qwen fix "Debug this issue"

# Check status
mekong health
mekong status
```

### Founder Workflow

```bash
# Create annual plan
mekong annual "2026 roadmap for AI startup"

# Define OKRs
mekong okr "Q2 2026 objectives"

# Prepare fundraising
mekong fundraise "Series A for $5M"
mekong pitch "Investor deck for Y Combinator"
```

### Engineering Workflow

```bash
# Build feature end-to-end
mekong cook "Implement user authentication with OAuth2"

# Fix production bug
mekong fix "High memory usage in API"

# Deploy to production
mekong deploy

# Code review before push
mekong review
```

### Business Workflow

```bash
# Generate pricing proposal
mekong quote "Acme Corp project" --budget 50000

# Create marketing plan
mekong marketing "Q2 content calendar"

# Analyze sales metrics
mekong kpi "Weekly sales analysis"
```

### Ops Workflow

```bash
# Security audit
mekong audit

# Health check
mekong health

# Generate incident response plan
mekong incident-response "Database outage scenario"
```

---

## Command Execution Flow

Every command follows Plan→Execute→Verify:

```
User Input
    ↓
1. PLAN: AI decomposes goal into tasks
    ↓
2. EXECUTE: AI runs tasks (code, shell, API)
    ↓
3. VERIFY: Quality gates + automated testing
    ↓
Success ✅ or Failure → Retry/Escalate
    ↓
Output: Code + reports + metrics
```

---

## MCU Consumption

**Average MCU per command:**

```
Simple commands: 1 MCU
  /help, /status, /health

Standard commands: 1-2 MCU
  /quote, /code, /test, /fix

Complex commands: 2-5 MCU
  /cook, /plan, /deploy, /audit, /fundraise

Parallel commands: 3-8 MCU
  /pitch, /deploy, /fundraise (runs 5+ agents)
```

---

## Next Steps

- **Full CLI Reference:** `/docs/CLI_REFERENCE.md`
- **API Reference:** `/docs/api-reference.md`
- **Getting Started:** `/docs/getting-started.md`
- **Deployment Guide:** `/docs/DEPLOYMENT_GUIDE.md`
